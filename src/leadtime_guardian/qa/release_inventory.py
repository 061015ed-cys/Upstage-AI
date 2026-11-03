"""Read-only C001 evidence inventory: local SHA and missing files, never release approval."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from leadtime_guardian.qa.audit import load_json_strict

VERSION = "leadtime-release-evidence/v1"
REQUIRED = (
    "stage_manifest", "operational_native", "qa_native", "qa_report",
    "team2_provenance", "operational_pdf_receipt", "qa_pdf_receipt",
    "human_gold",
)
PDF_KINDS = ("purchase_order", "delivery_notice", "quotation")
OPTIONAL = ("b0_manifest", "e1_manifest", "b0_normalize", "e1_normalize")
HEX = set("0123456789abcdef")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_release_folder(manifest_path: Path) -> dict[str, Any]:
    """Manifest paths relative to one local evidence directory; no cloud claims."""
    report: dict[str, Any] = {
        "schema_version": VERSION, "status": "BLOCKED",
        "checked_inputs": {}, "missing_inputs": [], "invalid_inputs": [],
        "evidence_sha256": {}, "blocking_issues": [],
        "next_required_action": None,
        "source_authentication_status": "NOT_AUTHENTICATED",
        "python_safety_status": "NOT_RUN",
        "cross_agent_status": "NOT_VERIFIED",
        "human_gold_status": "NOT_VERIFIED",
        "b0_e1_comparison_status": "NOT_MEASURED",
        "local_stage_status": "NOT_PROVIDED",
        "release_authorized": False,
    }

    def issue(code: str, key: str, *, invalid: bool = False) -> None:
        report["blocking_issues"].append({"issue_code": code, "source": key})
        bucket = "invalid_inputs" if invalid else "missing_inputs"
        if key not in report[bucket]:
            report[bucket].append(key)

    try:
        root = manifest_path.resolve(strict=True)
        if root.stat().st_size > 1024 * 1024:
            raise ValueError("release manifest too large")
        manifest = load_json_strict(root.read_bytes())
        if (not isinstance(manifest, dict)
                or manifest.get("schema_version") != VERSION
                or manifest.get("case_id") != "C001"
                or not isinstance(manifest.get("operational_job_id"), str)
                or not manifest["operational_job_id"].startswith("job_")
                or not isinstance(manifest.get("config_id"), str)
                or not manifest["config_id"].startswith("cfg_")
                or type(manifest.get("config_version")) is not int
                or manifest["config_version"] < 1
                or not isinstance(manifest.get("sources"), dict)):
            raise ValueError("invalid release manifest identity")
        directory = root.parent
        sources = manifest["sources"]
        for key in sorted(set(sources) - set(REQUIRED) - set(OPTIONAL)
                          - {"source_pdfs"}):
            issue("UNKNOWN_SOURCE_KEY", key, invalid=True)
        pdf_sources = sources.get("source_pdfs")
        if pdf_sources is None:
            pdf_sources = {}
        if not isinstance(pdf_sources, dict):
            issue("PDF_SOURCE_LIST_INVALID", "source_pdfs", invalid=True)
            pdf_sources = {}
        for kind in sorted(set(pdf_sources) - set(PDF_KINDS)):
            issue("UNKNOWN_PDF_KIND", "source_pdfs." + kind, invalid=True)

        def inspect(key: str, item: Any) -> None:
            if item is None:
                issue("SOURCE_NOT_PROVIDED", key)
                return
            if isinstance(item, str):
                item = {"path": item}
            if (not isinstance(item, dict)
                    or not isinstance(item.get("path"), str)
                    or not item["path"]
                    or Path(item["path"]).is_absolute()):
                issue("SOURCE_PATH_INVALID", key, invalid=True)
                return
            try:
                path = (directory / item["path"]).resolve(strict=True)
                if not path.is_relative_to(directory) or not path.is_file():
                    raise ValueError("path escape or not a file")
                sha = _sha256_file(path)
                claimed = item.get("sha256")
                if claimed is not None and (
                    not isinstance(claimed, str) or len(claimed) != 64
                    or any(c not in HEX for c in claimed.lower())
                ):
                    issue("SOURCE_DECLARED_SHA_INVALID", key, invalid=True)
                    return
                if claimed is not None and sha != claimed.lower():
                    issue("SOURCE_SHA_MISMATCH", key, invalid=True)
                    return
                report["checked_inputs"][key] = {
                    "relative_path": item["path"], "sha256": sha,
                    "size_bytes": path.stat().st_size,
                    "declared_sha256_match": claimed is not None,
                    "evidence_status": "LOCAL_BYTES_ONLY",
                }
                report["evidence_sha256"][key] = sha
            except (OSError, ValueError):
                issue("SOURCE_FILE_NOT_READABLE", key, invalid=True)

        for key in REQUIRED:
            inspect(key, sources.get(key))
        for key in OPTIONAL:
            if key in sources:
                inspect(key, sources[key])
        for kind in PDF_KINDS:
            inspect("source_pdfs." + kind, pdf_sources.get(kind))

        stage = report["checked_inputs"].get("stage_manifest")
        if stage is None:
            for kind in PDF_KINDS:
                issue("EXTRACT_BRANCH_NOT_PROVIDED", "stage.Extract." + kind)
            for name in (
                "MergeDocuments", "NormalizeDocuments",
                "IndependentQA_Input", "IndependentQA_Report",
            ):
                issue("STAGE_RAW_NOT_PROVIDED", "stage." + name)
        if stage is not None:
            from scripts.qa_stage_intake_check import inspect_manifest_path

            stage_report = inspect_manifest_path(directory / stage["relative_path"])
            report["local_stage_status"] = stage_report["status"]
            if stage_report["status"] == "FAIL":
                issue("STAGE_INTAKE_FAILED", "stage_manifest", invalid=True)
            if any(stage_report.get(key) != manifest[key] for key in (
                "case_id", "operational_job_id", "config_id", "config_version"
            )):
                issue("STAGE_IDENTITY_CONFLICT", "stage_manifest", invalid=True)
            for name, value in stage_report.get("stages", {}).items():
                if value.get("status") == "NOT_PROVIDED":
                    issue("STAGE_RAW_NOT_PROVIDED", "stage." + name)
                if name == "Extract":
                    branches = value.get("branches")
                    if not isinstance(branches, dict):
                        for kind in PDF_KINDS:
                            issue("EXTRACT_BRANCH_NOT_PROVIDED",
                                  "stage.Extract." + kind)
                    else:
                        for kind in PDF_KINDS:
                            if kind not in branches:
                                issue("EXTRACT_BRANCH_NOT_PROVIDED",
                                      "stage.Extract." + kind)
        report["status"] = "FAIL" if report["invalid_inputs"] else "BLOCKED"
        report["missing_inputs"].sort()
        report["invalid_inputs"].sort()
        report["blocking_issues"].sort(
            key=lambda x: (x["source"], x["issue_code"])
        )
        if report["invalid_inputs"]:
            report["next_required_action"] = (
                "Resolve invalid source paths, hashes and Job/Config/Case conflicts."
            )
        elif report["missing_inputs"]:
            report["next_required_action"] = (
                "Request the listed original Studio/PDF/QA/Gold evidence; "
                "do not run or fabricate a new Job."
            )
        else:
            report["next_required_action"] = (
                "Run combined Python V6/QA, Cross-Agent and PDF provenance gates. "
                "Local source completeness does not authenticate Studio execution."
            )
    except (OSError, TypeError, ValueError, UnicodeDecodeError, RecursionError):
        issue("RELEASE_MANIFEST_MISSING_OR_INVALID", "release_manifest",
              invalid=True)
        report["status"] = "FAIL"
        report["next_required_action"] = (
            "Supply a valid leadtime-release-evidence/v1 metadata manifest."
        )
    return report


def render_markdown(report: dict[str, Any]) -> str:
    """Plain Markdown without any original source content or user PDF data."""
    lines = [
        "# LeadTime Guardian — Release evidence preflight",
        "",
        f"Inventory status: {report['status']}",
        f"Stage local contract: {report['local_stage_status']}",
        "Studio execution authenticated: NO",
        "Python V6 executed by preflight: NO",
        "Release authorized: NO",
        "",
        "## Checked local files (SHA does not authenticate provider)",
    ]
    for key, item in sorted(report["checked_inputs"].items()):
        lines.append(f"- {key}: SHA256 {item['sha256']} ({item['size_bytes']} bytes)")
    lines.extend(["", "## Missing inputs"])
    lines.extend("- " + x for x in report["missing_inputs"])
    lines.extend(["", "## Invalid inputs"])
    lines.extend("- " + x for x in report["invalid_inputs"])
    lines.extend(["", "## Next action", report["next_required_action"] or "NONE"])
    return "\n".join(lines) + "\n"
