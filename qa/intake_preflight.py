"""Offline evidence intake. PASS requires a separately reviewed trust manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from leadtime_guardian.qa.studio_contract import audit_native_envelope
from qa.gold_metrics import bound_native, is_approved
from qa.inventory import strict_json
from qa.review_bridge import inspect_xlsx_review

REQUIRED = ("reviewed_xlsx", "baseline_csv", "human_review_record",
            "team_approval_record", "frozen_gold", "studio_native",
            "native_binding", "execution_record", "v6_sidecar")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def _read(root: Path, entry: object) -> tuple[bytes, str]:
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise TypeError("invalid path entry")
    relative = Path(entry["path"])
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("path outside intake directory")
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("path outside intake directory")
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("evidence exceeds size limit")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if not isinstance(entry.get("sha256"), str) or not SHA.fullmatch(entry["sha256"]):
        raise ValueError("declared sha256 required")
    if entry["sha256"] != digest:
        raise ValueError("sha256 mismatch")
    return raw, digest


def inspect(manifest_path: Path, trusted_manifest_path: Path | None = None) -> dict:
    """Separate missing evidence from contradictory evidence; never alter bytes."""
    result = {"status": "BLOCKED", "scope": "OFFLINE_EVIDENCE_INTAKE",
              "source_authentication_status": "NOT_VERIFIED",
              "official_metrics_eligible": False, "release_authorized": False,
              "sha256": {}, "blocking_reasons": [], "failures": []}
    try:
        root = manifest_path.resolve(strict=True).parent
        manifest = strict_json(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("artifacts"), dict):
            raise TypeError("manifest must contain artifacts object")
        case_id, job_id = manifest.get("case_id"), manifest.get("job_id")
        for name, value in (("case_id", case_id), ("job_id", job_id)):
            if value is None:
                result["blocking_reasons"].append(name + ":NOT_PROVIDED")
            elif not isinstance(value, str) or not value.strip():
                raise ValueError("invalid case or job identity")
        artifacts = manifest["artifacts"]
        raw = {}
        for name in REQUIRED:
            if name not in artifacts:
                result["blocking_reasons"].append(name + ":NOT_PROVIDED")
                continue
            try:
                raw[name], result["sha256"][name] = _read(root, artifacts[name])
            except FileNotFoundError:
                result["blocking_reasons"].append(name + ":NOT_PROVIDED")
            except (OSError, ValueError) as exc:
                result["failures"].append(name + ":" + type(exc).__name__)
        if "reviewed_xlsx" in raw and "baseline_csv" in raw:
            try:
                report = inspect_xlsx_review(raw["reviewed_xlsx"], raw["baseline_csv"],
                                             manifest.get("sheet"))
                result["xlsx_review_status"] = report["status"]
                if report["status"] != "PASS":
                    result["failures"].append("XLSX_REVIEW_CONTRACT_FAILED")
            except (OSError, ValueError, TypeError, IndexError, KeyError,
                    zipfile.BadZipFile):
                result["xlsx_review_status"] = "FAIL"
                result["failures"].append("XLSX_REVIEW_CONTRACT_FAILED")
        if all(name in raw for name in ("frozen_gold", "native_binding", "studio_native",
                                       "execution_record",
                                       "human_review_record", "team_approval_record",
                                       "v6_sidecar")):
            gold = strict_json(raw["frozen_gold"])
            binding = strict_json(raw["native_binding"])
            sidecar = strict_json(raw["v6_sidecar"])
            review = strict_json(raw["human_review_record"])
            approval = strict_json(raw["team_approval_record"])
            native = strict_json(raw["studio_native"])
            execution = strict_json(raw["execution_record"])
            if not all(isinstance(x, dict) for x in (gold, binding, sidecar, review,
                                                     approval, native, execution)):
                raise ValueError("JSON evidence must be objects")
            if not is_approved(gold):
                result["failures"].append("FROZEN_GOLD_NOT_APPROVED")
            if not bound_native(gold, binding):
                result["failures"].append("NATIVE_BINDING_MISMATCH")
            if (not isinstance(gold.get("case_id"), str)
                    or gold["case_id"].removeprefix("SYN-") != case_id
                    or binding.get("job_id") != job_id):
                result["failures"].append("CASE_OR_JOB_MISMATCH")
            if sidecar.get("export_sha256") != result["sha256"]["studio_native"]:
                result["failures"].append("SIDECAR_NATIVE_SHA_MISMATCH")
            review_ref = gold.get("approval_provenance")
            if (not isinstance(review_ref, dict) or
                    review_ref.get("approval_record_sha256") != result["sha256"]["human_review_record"]):
                result["failures"].append("HUMAN_REVIEW_SHA_MISMATCH")
            if (approval.get("case_id") != case_id
                    or approval.get("gold_sha256") != result["sha256"]["frozen_gold"]
                    or approval.get("decision") != "APPROVE"):
                result["failures"].append("TEAM_APPROVAL_MISMATCH")
            step = execution.get("native_step_run_id")
            native_check = audit_native_envelope(native, expected_job_id=job_id,
                                                 expected_step_run_id=step)
            result["native_contract_status"] = native_check["qa_status"]
            if native_check["qa_status"] != "PASS":
                result["failures"].append("NATIVE_CONTRACT_FAILED")
            if (execution.get("job_id") != job_id
                    or execution.get("config_id") != binding.get("config_id")
                    or not isinstance(execution.get("agent_id"), str)
                    or not execution["agent_id"].strip()
                    or type(execution.get("config_version")) is not int
                    or not isinstance(step, str) or not step.strip()
                    or execution.get("studio_execution_completed") is not True):
                result["failures"].append("EXECUTION_IDENTITY_MISMATCH")
            metadata = native.get("metadata")
            native_sources = metadata.get("source_files") if isinstance(metadata, dict) else None
            bound_sources = binding.get("file_bindings")
            if (not isinstance(native_sources, list) or not isinstance(bound_sources, list)
                    or not native_sources or len(native_sources) != len(bound_sources)
                    or {(x.get("file_id"), x.get("file_name")) for x in native_sources
                        if isinstance(x, dict)} !=
                       {(x.get("file_id"), x.get("filename")) for x in bound_sources
                        if isinstance(x, dict)}):
                result["failures"].append("NATIVE_FILE_BINDING_MISMATCH")
            pdfs = execution.get("source_pdfs")
            if (not isinstance(pdfs, list) or not isinstance(bound_sources, list)
                    or len(pdfs) != len(bound_sources)
                    or {(Path(x.get("path", "")).name, x.get("sha256")) for x in pdfs
                        if isinstance(x, dict) and isinstance(x.get("path"), str)} !=
                       {(x.get("filename"), x.get("sha256")) for x in bound_sources
                        if isinstance(x, dict)}):
                result["failures"].append("SOURCE_PDF_SHA_BINDING_MISMATCH")
        if trusted_manifest_path is None:
            result["blocking_reasons"].append("INDEPENDENT_TRUST_MANIFEST_NOT_PROVIDED")
        else:
            if trusted_manifest_path.resolve(strict=True).is_relative_to(root):
                raise ValueError("trust manifest must be outside intake directory")
            trust = strict_json(trusted_manifest_path.read_text(encoding="utf-8"))
            if (not isinstance(trust, dict) or trust.get("case_id") != case_id
                    or trust.get("job_id") != job_id or trust.get("sha256") != result["sha256"]
                    or not isinstance(trust.get("verified_by"), str)
                    or not trust["verified_by"].strip()):
                result["failures"].append("INDEPENDENT_TRUST_MANIFEST_MISMATCH")
            else:
                result["source_authentication_status"] = "EXTERNAL_ATTESTATION_RECORDED"
    except (OSError, ValueError, TypeError, KeyError, IndexError, UnicodeError,
            RecursionError, zipfile.BadZipFile) as exc:
        result["failures"].append("INVALID_INPUT:" + type(exc).__name__)
    result["status"] = ("FAIL" if result["failures"] else
                        "BLOCKED" if result["blocking_reasons"] else "PASS")
    # A local intake result does not settle the official output contract or provider identity.
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--trusted-manifest", type=Path)
    args = parser.parse_args()
    result = inspect(args.manifest, args.trusted_manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
