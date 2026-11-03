"""Offline combined Team2 V6 / QA E2E ingestion without Studio or release claims.

Read exact source bytes. Never infer that two Studio jobs used identical PDFs
from their file names, case IDs, or unrelated provider file IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.cross_agent import (
    APPROVED_SANDBOX_AGENTS,
    audit_cross_agent_handoff,
)
from leadtime_guardian.qa.handoff_builder import build_studio_raw_handoff
from leadtime_guardian.qa.portfolio import audit_portfolio
from leadtime_guardian.qa.provenance_link import audit_team2_provenance_link
from leadtime_guardian.qa.studio_batch import audit_studio_case_batch
from leadtime_guardian.qa.studio_contract import audit_native_envelope
from leadtime_guardian.studio_adapter import apply_studio_extractions
from leadtime_guardian.studio_integration import (
    analyze_studio_documents,
    documents_from_export,
    validate_documents,
)


def audit_combined_bytes(
    operational_native_bytes: bytes, base_case_bytes: bytes, schema_bytes: bytes,
    *, operational_job_id: str, case_id: str, github_sha: str,
    qa_native_bytes: bytes | None = None, qa_report_bytes: bytes | None = None,
    qa_agent_id: str | None = None, qa_config_id: str | None = None,
    qa_config_version: int | None = None,
    execution_kind: str = "ARCHIVED_STUDIO",
    studio_batch_report_bytes: bytes | None = None,
    team2_provenance_bytes: bytes | None = None,
    qa_pdf_receipt_bytes: bytes | None = None,
    operational_pdf_receipt_bytes: bytes | None = None,
    pdf_root: Path | None = None,
) -> dict:
    """Independently check the joined code path; no authentication of cloud runs."""
    result = {
        "status": "BLOCKED",
        "single_case_grouping_status": "NOT_VERIFIED",
        "provenance_link_status": "NOT_VERIFIED",
        "experiment_comparison_allowed": False,
        "python_business_status": "NOT_VERIFIED",
        "python_safety_status": "NOT_VERIFIED",
        "studio_document_status": "NOT_VERIFIED",
        "cross_agent_status": "BLOCKED",
        "same_original_pdf_bytes_verified": False,
        "actual_studio_e2e_status": "NOT_VERIFIED",
        "release_or_merge_authorized": False,
        "external_action_taken": False,
        "issues": [],
        "sha256": {},
    }

    def record(code: str, stage: str) -> None:
        result["issues"].append({"issue_code": code, "stage": stage})

    try:
        if studio_batch_report_bytes is not None:
            if type(studio_batch_report_bytes) is not bytes:
                raise TypeError("Studio batch observation must be original bytes")
            result["sha256"]["studio_batch_observation"] = hashlib.sha256(
                studio_batch_report_bytes
            ).hexdigest()
            batch = audit_studio_case_batch(
                load_json_strict(studio_batch_report_bytes),
                expected_case_id=case_id, expected_job_id=operational_job_id,
            )
            result["single_case_grouping_status"] = batch["single_case_grouping_status"]
            result["studio_batch_issues"] = batch["issues"]
            if batch["qa_status"] == "FAIL":
                result["status"] = "FAIL"
                record("INVALID_STUDIO_BATCH_GROUPING_EVIDENCE", "studio_batch")
                return result
            if batch["single_case_grouping_status"] == "INVALID_SPLIT_JOBS":
                record("MULTI_JOB_B0_NOT_INTEGRATED_C001", "studio_batch")
                return result
        if type(operational_native_bytes) is not bytes:
            raise TypeError("operational Native must be bytes")
        if type(base_case_bytes) is not bytes or type(schema_bytes) is not bytes:
            raise TypeError("trusted case and schema must be original bytes")
        result["sha256"]["operational_native"] = hashlib.sha256(
            operational_native_bytes
        ).hexdigest()
        operational = load_json_strict(operational_native_bytes)
        base = load_json_strict(base_case_bytes)
        schema = load_json_strict(schema_bytes)
        if not isinstance(operational, dict) or not isinstance(base, dict):
            raise TypeError("Native and base must be JSON objects")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("explicit nonempty case ID required")
        if base.get("case_id") not in (case_id, "SYN-" + case_id):
            raise ValueError("operational trusted base case ID differs from expected case")
        if not isinstance(operational.get("metadata"), dict):
            raise TypeError("operational Native metadata not observed")
        metadata = operational["metadata"]
        if metadata.get("job_execution_id") != operational_job_id:
            raise ValueError("operational job ID does not match expected")
        native = audit_native_envelope(
            operational, expected_job_id=operational_job_id,
            expected_step_run_id=metadata.get("step_run_id"),
        )
        if native["qa_status"] != "PASS":
            raise ValueError("operational Native contract did not pass")
        docs = documents_from_export(
            operational, expected_job_id=operational_job_id
        )
        if case_id == "C001":
            # C001 is a three-document case, not three independent Job outputs
            # or a one-document extract paired to a trusted base case.
            expected = {"purchase_order", "delivery_notice", "quotation"}
            source_rows = metadata.get("source_files")
            if (len(docs) != 3
                    or {d.get("document_type") for d in docs} != expected
                    or not isinstance(source_rows, list)
                    or len(source_rows) != 3
                    or any(not isinstance(x, dict) for x in source_rows)
                    or len({x.get("file_id") for x in source_rows}) != 3):
                record("C001_NOT_SINGLE_THREE_DOCUMENT_JOB", "operational_native")
                return result
            result["single_case_grouping_status"] = "NATIVE_THREE_DOCUMENT_CONTRACT_PASS"
        python_result = analyze_studio_documents(base, docs, schema)
        result["python_business_status"] = python_result["execution_status"]
        result["python_summary"] = {
            "case_id": python_result.get("case_id"),
            "execution_status": python_result.get("execution_status"),
            "review_flags": python_result.get("review_flags"),
            "baseline_shortage_quantity": python_result.get("baseline_shortage_quantity"),
            "changed_shortage_quantity": python_result.get("changed_shortage_quantity"),
            "estimated_quote_cost_krw": python_result.get("estimated_quote_cost_krw"),
            "evidence_verified_against_pdf": False,
        }
        if python_result["execution_status"] == "COMPLETED":
            from_case = apply_studio_extractions(base, docs)
            from_case["quotes"] = validate_documents(base, docs, schema)
            safety = audit_portfolio(from_case, python_result)
        else:
            safety = audit_portfolio(base, python_result)
        if safety["qa_status"] != "PASS":
            result["python_safety_status"] = "FAIL"
            record("INDEPENDENT_PYTHON_QA_FAILED", "python_safety")
        else:
            result["python_safety_status"] = (
                "PASS_LOCAL" if python_result["execution_status"] == "COMPLETED"
                else "SAFELY_BLOCKED_LOCAL"
            )
        if qa_native_bytes is None and qa_report_bytes is None:
            record("QA_STUDIO_RAW_ARTIFACTS_NOT_PROVIDED", "studio_qa")
        elif qa_native_bytes is None or qa_report_bytes is None:
            record("QA_STUDIO_RAW_ARTIFACT_PAIR_INCOMPLETE", "studio_qa")
        else:
            if (qa_agent_id is None or qa_config_id is None
                    or qa_config_version is None):
                raise ValueError("explicit QA agent/config/version required")
            if qa_agent_id not in APPROVED_SANDBOX_AGENTS:
                raise ValueError("QA agent not in frozen allow-list")
            result["sha256"]["qa_native"] = hashlib.sha256(
                qa_native_bytes
            ).hexdigest()
            result["sha256"]["qa_report"] = hashlib.sha256(
                qa_report_bytes
            ).hexdigest()
            manifest = build_studio_raw_handoff(
                qa_native_bytes, qa_report_bytes, case_id=case_id,
                agent_id=qa_agent_id, config_id=qa_config_id,
                config_version=qa_config_version,
                github_sha=github_sha, execution_kind=execution_kind,
            )
            if case_id == "C001":
                qa_raw = load_json_strict(qa_native_bytes)
                qa_docs = load_json_strict(qa_raw["content"])["documents"]
                expected = {"purchase_order", "delivery_notice", "quotation"}
                if (len(qa_docs) != 3
                        or {d.get("document_type") for d in qa_docs} != expected
                        or len(qa_raw["metadata"]["source_files"]) != 3):
                    record("QA_C001_NATIVE_CASE_INCOMPLETE", "qa_native")
                    return result
            verdict = audit_cross_agent_handoff(
                manifest, native_bytes=qa_native_bytes,
                report_bytes=qa_report_bytes,
                expected_agent_id=qa_agent_id,
                expected_config_id=qa_config_id,
                expected_github_sha=github_sha,
            )
            result["studio_document_status"] = verdict["document_qa_status"]
            result["cross_agent_status"] = verdict["qa_status"]
            result["requires_human_review"] = verdict["requires_human_review"]
            result["cross_agent_issues"] = verdict["issues"]
            if verdict["qa_status"] == "FAIL":
                record("CROSS_AGENT_CONTRACT_FAILED", "cross_agent")
        supplied = (team2_provenance_bytes, qa_pdf_receipt_bytes,
                    operational_pdf_receipt_bytes)
        if any(x is not None for x in supplied) or pdf_root is not None:
            if not all(type(x) is bytes for x in supplied) or pdf_root is None:
                record("PDF_PROVENANCE_EVIDENCE_SET_INCOMPLETE", "pdf_provenance")
            elif qa_native_bytes is None or qa_report_bytes is None:
                record("PDF_PROVENANCE_NEEDS_QA_RAW_PAIR", "pdf_provenance")
            else:
                sidecar = load_json_strict(team2_provenance_bytes)
                qa_receipt = load_json_strict(qa_pdf_receipt_bytes)
                op_receipt = load_json_strict(operational_pdf_receipt_bytes)
                if not isinstance(sidecar, dict) or not isinstance(op_receipt, dict):
                    raise TypeError("operational sidecar and PDF receipt must be objects")
                for key, raw in (
                    ("team2_provenance", team2_provenance_bytes),
                    ("qa_pdf_receipt", qa_pdf_receipt_bytes),
                    ("operational_pdf_receipt", operational_pdf_receipt_bytes),
                ):
                    result["sha256"][key] = hashlib.sha256(raw).hexdigest()
                if sidecar.get("export_sha256") != result["sha256"]["operational_native"]:
                    result["provenance_link_status"] = "FAIL"
                    record("OPERATION_NATIVE_SIDECAR_SHA_MISMATCH", "team2_provenance")
                supplied_meta = sidecar.get("studio_metadata_supplied")
                if (not isinstance(supplied_meta, dict)
                        or supplied_meta.get("job_execution_id") != operational_job_id):
                    result["provenance_link_status"] = "FAIL"
                    record("OPERATION_SIDECAR_JOB_MISMATCH", "team2_provenance")
                # Match operational receipt File IDs to original Native metadata.
                native_sources = metadata.get("source_files")
                expected_sources = (
                    {(x.get("file_id"), x.get("file_name")) for x in native_sources}
                    if isinstance(native_sources, list)
                    and all(isinstance(x, dict)
                            and isinstance(x.get("file_id"), str)
                            and isinstance(x.get("file_name"), str)
                            for x in native_sources) else set()
                )
                actual_rows = op_receipt.get("files")
                receipt_sources = (
                    {(x.get("file_id"), x.get("filename")) for x in actual_rows}
                    if isinstance(actual_rows, list)
                    and all(isinstance(x, dict)
                            and isinstance(x.get("file_id"), str)
                            and isinstance(x.get("filename"), str)
                            for x in actual_rows) else set()
                )
                if (not expected_sources or not receipt_sources
                        or len(expected_sources) != len(native_sources)
                        or len(receipt_sources) != len(actual_rows)
                        or expected_sources != receipt_sources):
                    result["provenance_link_status"] = "FAIL"
                    record("OPERATION_NATIVE_UPLOAD_RECEIPT_MISMATCH", "pdf_provenance")
                link = audit_team2_provenance_link(
                    manifest, sidecar, qa_receipt, op_receipt, pdf_root=pdf_root,
                )
                result["provenance_issues"] = link["issues"]
                result["same_original_pdf_bytes_verified"] = (
                    link["same_local_pdf_bytes_verified"]
                )
                if link["qa_status"] == "FAIL":
                    result["provenance_link_status"] = "FAIL"
                    record("PDF_PROVENANCE_LINK_FAILED", "pdf_provenance")
                elif result["provenance_link_status"] != "FAIL":
                    result["provenance_link_status"] = "BLOCKED"
                if result["provenance_link_status"] == "FAIL":
                    result["same_original_pdf_bytes_verified"] = False
        if (result["python_safety_status"] == "FAIL"
                or result["cross_agent_status"] == "FAIL"
                or result["provenance_link_status"] == "FAIL"):
            result["status"] = "FAIL"
    except (ValueError, TypeError, KeyError, IndexError, UnicodeDecodeError) as exc:
        result["status"] = "FAIL"
        record("COMBINED_E2E_INPUT_OR_BOUNDARY_FAILED", type(exc).__name__)
    return result


def preflight_stage_before_python(
    manifest_path: Path, operational_raw_bytes: bytes,
    *, case_id: str, operational_job_id: str,
) -> dict:
    """Reject corrupt or mismatched evidence BEFORE running V6 calculations."""
    from qa_stage_intake_check import inspect_manifest_path

    from leadtime_guardian.qa.stage_trace import canonical_documents_sha256

    stage = inspect_manifest_path(manifest_path)
    result = {
        "status": "BLOCKED", "stage_intake": stage,
        "stage_intake_status": stage["status"],
        "release_or_merge_authorized": False,
        "actual_studio_e2e_status": "NOT_VERIFIED",
        "python_safety_status": "NOT_RUN",
        "issues": [],
    }

    def fail(code: str) -> None:
        result["status"] = "FAIL"
        result["issues"].append({"issue_code": code, "stage": "stage_intake"})

    if stage["status"] == "FAIL":
        fail("RAW_STAGE_INTAKE_FAILED")
    elif (stage.get("case_id") != case_id
          or stage.get("operational_job_id") != operational_job_id):
        fail("STAGE_AND_OPERATIONAL_JOB_IDENTITY_CONFLICT")
    else:
        normalized = stage["stages"]["NormalizeDocuments"]
        if normalized.get("document_content_sha256") is None:
            result["issues"].append({
                "issue_code": "NORMALIZE_STAGE_RAW_NOT_VERIFIED",
                "stage": "stage_intake",
            })
        else:
            op = load_json_strict(operational_raw_bytes)
            docs = documents_from_export(op, expected_job_id=operational_job_id)
            if (canonical_documents_sha256(docs)
                    != normalized["document_content_sha256"]):
                fail("NATIVE_AND_NORMALIZE_CONTENT_MISMATCH")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operational-native", required=True, type=Path)
    parser.add_argument("--studio-batch-report", type=Path)
    parser.add_argument("--stage-intake-manifest", type=Path)
    parser.add_argument("--team2-provenance", type=Path)
    parser.add_argument("--qa-pdf-receipt", type=Path)
    parser.add_argument("--operational-pdf-receipt", type=Path)
    parser.add_argument("--pdf-root", type=Path)
    parser.add_argument("--trusted-base", required=True, type=Path)
    parser.add_argument("--schema", type=Path, default=ROOT /
                        "configs/schemas/document_extraction.schema.json")
    parser.add_argument("--operational-job-id", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--qa-native", type=Path)
    parser.add_argument("--qa-report", type=Path)
    parser.add_argument("--qa-agent-id", choices=sorted(APPROVED_SANDBOX_AGENTS))
    parser.add_argument("--qa-config-id")
    parser.add_argument("--qa-config-version", type=int)
    parser.add_argument("--github-sha", required=True)
    parser.add_argument("--execution-kind", choices=(
        "ARCHIVED_STUDIO", "ARCHIVED_REPLAY", "NEW_LIVE_STUDIO",
    ), default="ARCHIVED_STUDIO")
    args = parser.parse_args()
    try:
        if args.execution_kind == "NEW_LIVE_STUDIO":
            missing = []
            for label, value in (
                ("STAGE_INTAKE_MANIFEST", args.stage_intake_manifest),
                ("QA_NATIVE", args.qa_native),
                ("QA_REPORT", args.qa_report),
                ("TEAM2_PROVENANCE", args.team2_provenance),
                ("QA_PDF_RECEIPT", args.qa_pdf_receipt),
                ("OPERATIONAL_PDF_RECEIPT", args.operational_pdf_receipt),
                ("PDF_ROOT", args.pdf_root),
                ("QA_AGENT_ID", args.qa_agent_id),
                ("QA_CONFIG_ID", args.qa_config_id),
                ("QA_CONFIG_VERSION", args.qa_config_version),
            ):
                if value is None:
                    missing.append(label)
            if missing:
                result = {
                    "status": "BLOCKED",
                    "python_safety_status": "NOT_RUN",
                    "actual_studio_e2e_status": "NOT_VERIFIED",
                    "release_or_merge_authorized": False,
                    "missing_inputs": missing,
                    "issues": [
                        {"issue_code": "NEW_LIVE_EVIDENCE_NOT_PROVIDED",
                         "stage": "preflight"}
                    ],
                }
                print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
                return 2
        original_bytes = args.operational_native.read_bytes()
        preflight = (
            preflight_stage_before_python(
                args.stage_intake_manifest, original_bytes,
                case_id=args.case_id,
                operational_job_id=args.operational_job_id,
            )
            if args.stage_intake_manifest is not None else None
        )
        if preflight is not None and preflight["status"] == "FAIL":
            result = preflight
        elif (args.execution_kind == "NEW_LIVE_STUDIO"
              and (preflight is None
                   or not preflight["stage_intake"].get(
                       "all_expected_raw_stages_present", False
                   ))):
            # Archived offline replay remains possible with partial inputs.
            # An expressly NEW_LIVE claim never reaches V6 without the full
            # original Stage and actual IndependentQA Input/Report evidence.
            result = preflight if preflight is not None else {
                "status": "BLOCKED", "issues": [],
            }
            result["python_safety_status"] = "NOT_RUN"
            result["issues"].append({
                "issue_code": "NEW_LIVE_RAW_STAGES_INCOMPLETE",
                "stage": "preflight",
            })
        else:
            result = audit_combined_bytes(
                original_bytes, args.trusted_base.read_bytes(),
                args.schema.read_bytes(),
                operational_job_id=args.operational_job_id,
                case_id=args.case_id, github_sha=args.github_sha,
                qa_native_bytes=args.qa_native.read_bytes() if args.qa_native else None,
                qa_report_bytes=args.qa_report.read_bytes() if args.qa_report else None,
                qa_agent_id=args.qa_agent_id, qa_config_id=args.qa_config_id,
                qa_config_version=args.qa_config_version,
                execution_kind=args.execution_kind,
                studio_batch_report_bytes=(args.studio_batch_report.read_bytes()
                                           if args.studio_batch_report else None),
                team2_provenance_bytes=(args.team2_provenance.read_bytes()
                                        if args.team2_provenance else None),
                qa_pdf_receipt_bytes=(args.qa_pdf_receipt.read_bytes()
                                      if args.qa_pdf_receipt else None),
                operational_pdf_receipt_bytes=(
                    args.operational_pdf_receipt.read_bytes()
                    if args.operational_pdf_receipt else None
                ),
                pdf_root=args.pdf_root,
            )
            if preflight is not None:
                result["stage_intake"] = preflight["stage_intake"]
                result["stage_intake_status"] = preflight["stage_intake_status"]
                result["issues"].extend(preflight["issues"])
    except (OSError, TypeError, ValueError, KeyError, UnicodeDecodeError):
        result = {
            "status": "FAIL", "release_or_merge_authorized": False,
            "issues": [{"issue_code": "INPUT_FILE_NOT_READABLE", "stage": "cli"}],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if result["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
