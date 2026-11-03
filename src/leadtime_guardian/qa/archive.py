"""Verify archived Studio evidence integrity without executing Studio or trusting labels."""
from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .audit import load_json_strict


def verify_c001_archive(repo_root: str | Path) -> dict:
    """Read-only audit of the previously archived C001 evidence.

    A PASS is archive consistency only, never independent Studio re-execution,
    source PDF text verification, or human-reviewed extraction accuracy.
    """
    root = Path(repo_root)
    base = root / "data/results/studio_runs/C001_20261030_v4"
    issues = []

    def fail(code: str, path: str) -> None:
        issues.append({"issue_code": code, "field": path, "severity": "ERROR"})

    def read_json(path: Path) -> dict:
        try:
            content = load_json_strict(path.read_bytes())
        except (OSError, ValueError, TypeError):
            fail("UNREADABLE_OR_INVALID_JSON", str(path.relative_to(root)))
            return {}
        if not isinstance(content, dict):
            fail("INVALID_JSON_OBJECT", str(path.relative_to(root)))
            return {}
        return content

    execution = read_json(base / "execution_record.json")
    metadata = read_json(base / "analysis/run_metadata.json")
    analysis = read_json(base / "analysis/analysis.json")
    if not execution or not metadata or not analysis:
        return {"qa_status": "FAIL", "issues": issues,
                "evidence_type": "ARCHIVED_RECORD_ONLY", "source_pdf_hashes_checked": 0}

    if execution.get("execution_mode") != "live_studio_web" or execution.get(
        "studio_execution_completed"
    ) is not True:
        fail("ARCHIVED_RUN_NOT_MARKED_COMPLETED", "execution_record.json")
    if execution.get("job_id") != metadata.get("run_id"):
        fail("JOB_ID_MISMATCH", "analysis/run_metadata.json")
    if execution.get("config_id") != metadata.get("config_version"):
        fail("CONFIG_ID_MISMATCH", "analysis/run_metadata.json")
    if analysis.get("case_id") != "SYN-C001":
        fail("CASE_ID_MISMATCH", "analysis/analysis.json")
    if analysis.get("status") != "OK" or analysis.get("execution_status") != "COMPLETED":
        fail("NOT_COMPLETED", "analysis/analysis.json")

    for key in ("baseline_shortage_quantity", "changed_shortage_quantity",
                "additional_shortage_quantity"):
        if (type(execution.get(key)) is not int or type(analysis.get(key)) is not int
                or execution[key] != analysis[key]):
            fail("QUANTITY_RECORD_MISMATCH", key)
    try:
        expected = Decimal(str(execution.get("estimated_quote_cost_krw")))
        actual = Decimal(str(analysis.get("estimated_quote_cost_krw")))
        if not expected.is_finite() or not actual.is_finite() or expected != actual:
            fail("COST_RECORD_MISMATCH", "estimated_quote_cost_krw")
    except InvalidOperation:
        fail("COST_RECORD_INVALID", "estimated_quote_cost_krw")
    if analysis.get("external_action_taken") is not False or execution.get(
        "external_procurement_action_taken"
    ) is not False:
        fail("EXTERNAL_ACTION_NOT_DISPROVEN", "external_action_taken")
    for record in (execution, metadata, analysis):
        if record.get("evidence_verified_against_pdf") is True:
            fail("UNSUPPORTED_PDF_GROUNDING", "evidence_verified_against_pdf")
    if execution.get("accuracy_measured") is True or execution.get("human_gold_reviewed") is True:
        fail("UNSUPPORTED_ACCURACY_OR_HUMAN_REVIEW", "execution_record.json")

    checked = 0
    entries = execution.get("source_pdfs")
    if not isinstance(entries, list) or len(entries) != 3:
        fail("SOURCE_PDF_LIST_INVALID", "source_pdfs")
    else:
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                fail("INVALID_PDF_RECORD", f"source_pdfs[{i}]")
                continue
            name, recorded = entry.get("path"), entry.get("sha256")
            if not isinstance(name, str) or not name.startswith("data/cases/SYN-C001/"):
                fail("INVALID_PDF_PATH", f"source_pdfs[{i}]")
                continue
            path = (root / name).resolve()
            if root.resolve() not in path.parents or not path.is_file() or not path.is_relative_to(
                root.resolve()
            ):
                fail("PDF_NOT_FOUND", name)
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != recorded:
                fail("PDF_HASH_MISMATCH", name)
                continue
            checked += 1
    return {"qa_status": "FAIL" if issues else "PASS", "issues": issues,
            "evidence_type": "ARCHIVED_RECORD_ONLY",
            "source_pdf_hashes_checked": checked,
            "live_studio_runs_started_by_this_audit": 0,
            "human_gold_accuracy": None}
