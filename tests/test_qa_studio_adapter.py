"""Studio raw QA adapter tests are synthetic, never new Upstage execution."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.qa.cross_agent import (
    HANDOFF_VERSION,
    SANDBOX_COPY_AGENT_ID,
    SANDBOX_COPY_CONFIG_ID,
    audit_cross_agent_handoff,
)
from leadtime_guardian.qa.studio_qa_adapter import (
    STUDIO_REPORT_FORMAT,
    normalize_studio_qa_report,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/results/studio_runs/C001_20261030_v4/analysis/studio_original.json"
DOC_IDS = ["PO-DOC", "NOTICE-DOC", "QUOTE-DOC"]


def report():
    return {
        "case_id": "C001",
        "qa_status": "NOT_VERIFIED",
        "checked_document_ids": DOC_IDS.copy(),
        "issues": [],
        "evidence_status": "PARTIAL",
        "recommended_action": "Review source and Python result",
        "workflow_version": "v1",
        "execution_provenance": {
            "workflow_id": None, "config_id": None, "job_id": None, "source_files": None
        },
        "field_checks": [
            {"field": "po_id", "status": "VERIFIED"},
            {"field": "qty", "status": "SOURCE_NOT_VERIFIED"},
        ],
    }


def codes(result):
    return {x["issue_code"] for x in result["issues"]}


def make_handoff(source_report=None):
    raw = report() if source_report is None else source_report
    original_report_bytes = json.dumps(raw, ensure_ascii=False).encode()
    native = ARCHIVE.read_bytes()  # V4 archived operational bytes, NOT QA live!
    meta = json.loads(native)["metadata"]
    mapped = normalize_studio_qa_report(
        raw, expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    manifest = {
        "protocol_version": HANDOFF_VERSION,
        "producer": "UPSTAGE_QA_SANDBOX",
        "studio": {
            "agent_id": SANDBOX_COPY_AGENT_ID,
            "config_id": SANDBOX_COPY_CONFIG_ID,
            "config_version": 1,
            "case_id": "C001",
            "checked_document_ids": DOC_IDS.copy(),
            "job_id": meta["job_execution_id"],
            "step_run_id": meta["step_run_id"],
            "execution_kind": "ARCHIVED_REPLAY",
            "qa_report_format": STUDIO_REPORT_FORMAT,
            "input_file_ids": [x["file_id"] for x in meta["source_files"]],
            "native_sha256": hashlib.sha256(native).hexdigest(),
            "qa_report_sha256": hashlib.sha256(original_report_bytes).hexdigest(),
        },
        "verdict": {
            "document_qa_status": mapped["document_qa_status"],
            "python_qa_status": mapped["python_qa_status"],
            "issues": mapped["issues"],
        },
        "github": {
            "repository": "dohun3540-crypto/leadtime-guardian-agent.copy",
            "head_sha": "a" * 40,
            "contract_version": HANDOFF_VERSION,
        },
    }
    return manifest, native, original_report_bytes


def test_actual_report_shape_does_not_promote_unverified_to_pass():
    result = normalize_studio_qa_report(
        report(), expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    assert result["adapter_status"] == "PASS"
    assert result["document_qa_status"] == "NOT_VERIFIED"
    assert result["python_qa_status"] == "NOT_VERIFIED"
    assert result["execution_provenance"]["job_id"] is None
    assert result["requires_human_review"] is True
    assert result["pdf_grounding_verified"] is False


def test_raw_report_bytes_are_unchanged_and_archived_replay_is_blocked():
    manifest, native, raw = make_handoff()
    before = bytes(raw)
    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=raw,
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert result["qa_status"] == "BLOCKED"
    assert result["document_qa_status"] == "NOT_VERIFIED"
    assert result["python_qa_status"] == "NOT_VERIFIED"
    assert result["requires_human_review"] is True
    assert result["release_or_merge_authorized"] is False
    assert raw == before


def test_unverified_studio_cannot_claim_python_pass():
    manifest, native, raw = make_handoff()
    manifest["verdict"]["python_qa_status"] = "PASS"
    response = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=raw,
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert "RAW_STUDIO_CANNOT_ASSERT_PYTHON_PASS" in codes(response)
    assert response["qa_status"] == "FAIL"


@pytest.mark.parametrize(("key", "value", "issue"), [
    ("case_id", "C013", "STUDIO_STUDIO_CASE_ID_MISMATCH"),
    ("checked_document_ids", ["WRONG"], "STUDIO_STUDIO_DOCUMENT_ID_MISMATCH"),
])
def test_case_and_doc_binding_cannot_be_changed(key, value, issue):
    raw = report()
    raw[key] = value
    manifest, native, original = make_handoff(raw)
    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=original,
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert issue in codes(result)
    assert result["qa_status"] == "FAIL"


def test_qa_report_sha_is_exact_original_bytes():
    manifest, native, original = make_handoff()
    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=original + b" ",
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert "QA_REPORT_HASH_MISMATCH" in codes(result)


def test_report_issue_mapping_cannot_be_faked_in_manifest():
    manifest, native, original = make_handoff()
    manifest["verdict"]["issues"] = []
    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=original,
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert "STUDIO_MAPPED_ISSUES_MISMATCH" in codes(result)


@pytest.mark.parametrize("field", [
    "case_id", "qa_status", "checked_document_ids", "field_checks", "issues",
    "workflow_version", "execution_provenance", "evidence_status",
])
def test_missing_raw_field_fails_closed(field):
    raw = report()
    del raw[field]
    outcome = normalize_studio_qa_report(
        raw, expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    assert outcome["adapter_status"] == "FAIL"


def test_source_not_verified_blocks_even_optimistic_raw_pass():
    raw = report()
    raw["qa_status"] = "PASS"
    outcome = normalize_studio_qa_report(
        raw, expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    assert outcome["document_qa_status"] == "NOT_VERIFIED"
    assert outcome["requires_human_review"] is True


def test_normalized_output_claim_does_not_prove_actual_node_failure():
    raw = report()
    raw["issues"].append({
        "issue_code": "NORMALIZED_OUTPUT_NOT_PROVIDED",
        "scope": "integration",
        "severity": "WARNING",
    })
    outcome = normalize_studio_qa_report(
        raw, expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    assert outcome["adapter_status"] == "PASS"
    assert outcome["requires_human_review"] is True
    assert outcome["document_qa_status"] == "NOT_VERIFIED"


def test_same_run_provenance_conflict_is_review_warning_not_error():
    raw = report()
    raw["execution_provenance"] = {
        "workflow_id": SANDBOX_COPY_AGENT_ID,
        "config_id": SANDBOX_COPY_CONFIG_ID,
        "job_id": "job_something_else",
        "source_files": [],
    }
    manifest, native, original = make_handoff(raw)
    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=original,
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert result["qa_status"] == "BLOCKED"
    assert "EXECUTION_PROVENANCE_MISMATCH" in codes(result)
    assert result["requires_human_review"] is True
    assert all(x["severity"] == "WARNING"
               for x in result["issues"]
               if x["issue_code"] == "EXECUTION_PROVENANCE_MISMATCH")


def test_separate_historical_prediction_id_is_not_same_run_conflict():
    raw = report()
    raw["historical_prediction_job_id"] = "job_older_operational_prediction"
    manifest, native, original = make_handoff(raw)
    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=original,
        expected_agent_id=SANDBOX_COPY_AGENT_ID,
    )
    assert "EXECUTION_PROVENANCE_MISMATCH" not in codes(result)


def test_raw_report_scope_must_be_explicit_or_reviewed():
    raw = report()
    raw["issues"] = [{"issue_code": "SOURCE_NOT_VERIFIED", "severity": "WARNING"}]
    outcome = normalize_studio_qa_report(
        raw, expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    assert outcome["requires_human_review"] is True
    assert outcome["issues"][0]["scope"] == "integration"


def test_raw_report_input_not_mutated():
    raw = report()
    copy = deepcopy(raw)
    normalize_studio_qa_report(
        raw, expected_case_id="C001", expected_document_ids=DOC_IDS,
    )
    assert raw == copy
