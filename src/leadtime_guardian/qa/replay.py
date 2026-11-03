"""Offline C001 replay: archived prediction -> unchanged adapter -> original engine -> QA.

Not a fresh Upstage request, not a human PDF ground-truth check.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from leadtime_guardian.studio_adapter import apply_studio_extractions
from leadtime_guardian.studio_integration import (
    analyze_studio_documents,
    documents_from_export,
    validate_documents,
)

from .archive import verify_c001_archive
from .audit import audit_case, load_json_strict
from .portfolio import audit_portfolio


def verify_c001_replay(repo_root: str | Path) -> dict:
    root = Path(repo_root)
    prefix = root / "data/results/studio_runs/C001_20261030_v4"
    issues = []

    def fail(code: str, field: str) -> None:
        issues.append({"issue_code": code, "field": field, "severity": "ERROR"})

    def read(path: Path):
        try:
            return load_json_strict(path.read_bytes())
        except (OSError, UnicodeDecodeError, ValueError, TypeError):
            fail("UNREADABLE_REPLAY_INPUT", str(path.relative_to(root)))
            return None

    base = read(root / "data/cases/SYN-C001/trusted_base_case.json")
    raw = read(prefix / "analysis/studio_original.json")
    normalized = read(prefix / "analysis/normalized_documents.json")
    saved = read(prefix / "analysis/analysis.json")
    metadata = read(prefix / "analysis/run_metadata.json")
    execution = read(prefix / "execution_record.json")
    schema = read(root / "configs/schemas/document_extraction.schema.json")
    if any(value is None for value in (base, raw, normalized, saved, metadata, execution, schema)):
        return {"qa_status": "FAIL", "issues": issues, "mode": "ARCHIVED_REPLAY"}

    try:
        studio_path = prefix / "analysis/studio_original.json"
        if hashlib.sha256(studio_path.read_bytes()).hexdigest() != metadata.get("export_sha256"):
            fail("EXPORT_HASH_MISMATCH", "analysis/studio_original.json")
        native_meta = raw.get("metadata", {})
        if not isinstance(native_meta, dict) or native_meta.get("job_execution_id") != execution.get(
            "job_id"
        ) or native_meta.get("step_run_id") != execution.get("native_step_run_id"):
            fail("NATIVE_EXECUTION_ID_MISMATCH", "studio_original.metadata")
        if metadata.get("run_id") != execution.get("job_id") or metadata.get(
            "config_version"
        ) != execution.get("config_id"):
            fail("ARCHIVE_RUN_ID_MISMATCH", "analysis/run_metadata.json")
        decoded = documents_from_export(raw)
        if decoded != normalized:
            fail("NORMALIZED_DOCUMENT_MISMATCH", "analysis/normalized_documents.json")
        quotes = validate_documents(base, decoded, schema)
        integrated_case = apply_studio_extractions(base, decoded)
        integrated_case["quotes"] = quotes
        replay = analyze_studio_documents(base, decoded, schema)
        if replay != saved:
            fail("REPLAY_RESULT_MISMATCH", "analysis/analysis.json")
        for evaluator in (audit_case(integrated_case, replay), audit_portfolio(integrated_case, replay)):
            if evaluator["qa_status"] != "PASS":
                for item in evaluator["issues"]:
                    issues.append({"issue_code": "REPLAY_" + item["issue_code"],
                                   "field": item.get("field", "$"), "severity": "ERROR"})
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        fail("REPLAY_CONTRACT_ERROR", type(exc).__name__)

    archived = verify_c001_archive(root)
    if archived["qa_status"] != "PASS":
        issues.extend(archived["issues"])
    return {"qa_status": "FAIL" if issues else "PASS", "issues": issues,
            "mode": "ARCHIVED_REPLAY", "live_studio_runs_started": 0,
            "human_verified_extraction_accuracy": None}
