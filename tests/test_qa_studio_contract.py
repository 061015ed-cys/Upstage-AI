"""Archive-based Studio envelope contract checks, no cloud execution."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.qa.studio_contract import audit_native_envelope

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/results/studio_runs/C001_20261030_v4"


def original():
    return json.loads((ARCHIVE / "analysis/studio_original.json").read_text(encoding="utf-8"))


def ids():
    record = json.loads((ARCHIVE / "execution_record.json").read_text(encoding="utf-8"))
    return record["job_id"], record["native_step_run_id"]


def checked(raw):
    job, step = ids()
    return audit_native_envelope(raw, expected_job_id=job, expected_step_run_id=step)


def codes(report):
    return {item["issue_code"] for item in report["issues"]}


def test_native_archive_contract_is_valid_but_not_ground_truth():
    result = checked(original())
    assert result["qa_status"] == "PASS"
    assert result["evidence_type"] == "NATIVE_ENVELOPE_CONTRACT_ONLY"
    assert result["pdf_grounding_verified"] is False
    assert result["new_studio_run_started"] is False


def test_native_without_expected_run_is_not_verified():
    result = audit_native_envelope(original())
    assert result["qa_status"] == "NOT_VERIFIED"


@pytest.mark.parametrize(("part", "field", "value", "expected"), [
    ("metadata", "job_execution_id", "job_old_other", "CROSS_JOB_MISMATCH"),
    ("metadata", "step_run_id", "step-old", "CROSS_STEP_MISMATCH"),
    ("metadata", "occurrence_id", "other-occurrence", "STEP_OCCURRENCE_MISMATCH"),
    ("metadata", "source_files", [], "INVALID_SOURCE_MANIFEST"),
    ("metadata", "merge", {"items": []}, "MERGE_DOCUMENT_COUNT_MISMATCH"),
    ("root", "content", "{oops", "INVALID_OR_DUPLICATE_NATIVE_JSON"),
    ("root", "content", '{"documents":[]}', "MISSING_NATIVE_DOCUMENTS"),
    ("root", "content", '{"documents":[],"documents":[]}', "INVALID_OR_DUPLICATE_NATIVE_JSON"),
    ("root", "content", '{"documents":"not-a-list"}', "MISSING_NATIVE_DOCUMENTS"),
    ("root", "needs_review", True, "INCOMPLETE_OR_REVIEW_RUN"),
])
def test_native_bad_metadata_and_content_are_blocked(part, field, value, expected):
    raw = original()
    target = raw["metadata"] if part == "metadata" else raw
    target[field] = value
    assert expected in codes(checked(raw))


@pytest.mark.parametrize(("field", "value"), [
    ("documents", []), ("output_text", '{"documents":[]}'),
    ("gold", {"approved": True}), ("human_reviewed", True),
    ("provenance", "DRAFT_GOLD"),
])
def test_native_rejects_ambiguous_and_gold_wrappers(field, value):
    raw = original()
    raw[field] = value
    assert "AMBIGUOUS_OR_GOLD_NATIVE_ENVELOPE" in codes(checked(raw))


def test_native_rejects_mixed_source_file_ids():
    raw = original()
    raw["metadata"]["merge"]["items"][0]["source_files"][0]["file_id"] = "file_unknown"
    assert "MERGE_SOURCE_MISMATCH" in codes(checked(raw))


def test_unknown_source_id_without_filename_must_not_pass():
    raw = original()
    raw["metadata"]["merge"]["items"][0]["source_files"][0] = {
        "file_id": "file_unknown"
    }
    assert "MERGE_SOURCE_MISMATCH" in codes(checked(raw))


def test_native_rejects_mixed_source_filenames():
    raw = original()
    raw["metadata"]["merge"]["items"][1]["source_files"][0]["file_name"] = "other.pdf"
    assert "MERGE_SOURCE_MISMATCH" in codes(checked(raw))


def test_native_rejects_mixed_merge_document_types():
    raw = original()
    raw["metadata"]["merge"]["items"][1]["document_type"] = "quotation"
    assert "MERGE_TYPE_COUNTS_MISMATCH" in codes(checked(raw))


@pytest.mark.parametrize("doc_id", [None, "", ["unhashable"]])
def test_native_rejects_bad_document_id(doc_id):
    raw = original()
    payload = json.loads(raw["content"])
    payload["documents"][0]["document_id"] = doc_id
    raw["content"] = json.dumps(payload)
    assert "MISSING_OR_DUPLICATE_DOCUMENT_ID" in codes(checked(raw))


def test_native_rejects_duplicate_document_id():
    raw = original()
    payload = json.loads(raw["content"])
    payload["documents"][1]["document_id"] = payload["documents"][0]["document_id"]
    raw["content"] = json.dumps(payload)
    assert "MISSING_OR_DUPLICATE_DOCUMENT_ID" in codes(checked(raw))


def test_native_rejects_bad_document_type():
    raw = original()
    payload = json.loads(raw["content"])
    payload["documents"][0]["document_type"] = {"bad": True}
    raw["content"] = json.dumps(payload)
    assert "INVALID_NATIVE_DOCUMENT_TYPE" in codes(checked(raw))


def test_original_read_is_not_mutated():
    raw = original()
    preserved = deepcopy(raw)
    checked(raw)
    assert raw == preserved
