"""Actual Studio Step Input must be observed; local content is never live proof."""
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.input_delivery import audit_normalize_qa_input

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_input_delivery_check.py"
DOCS = [
    {"document_id": "PO-DOC", "document_type": "purchase_order"},
    {"document_id": "NOTICE-DOC", "document_type": "delivery_notice"},
    {"document_id": "QUOTE-DOC", "document_type": "quotation"},
]


def test_explicit_single_case_local_match_remains_blocked():
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "case_id": "C001",
         "content": json.dumps({"documents": DOCS})},
        {"case_id": "C001", "input": {"normalized_documents": DOCS}},
        expected_case_id="C001",
    )
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MATCH"
    assert result["qa_status"] == "BLOCKED"
    assert result["case_binding_conflict"] is False
    assert result["normalize_document_count"] == 3
    assert result["actual_cloud_input_authenticated"] is False


def test_explicit_wrong_qa_case_blocks_even_with_matching_documents():
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "case_id": "C001", "output": {"documents": DOCS}},
        {"case_id": "C013", "normalized_documents": DOCS},
        expected_case_id="C001",
    )
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MISMATCH"
    assert result["qa_status"] == "FAIL"
    assert result["case_binding_conflict"] is True
    assert {x["issue_code"] for x in result["issues"]} >= {
        "QA_INPUT_CASE_ID_MISMATCH",
    }


def test_equal_malformed_lists_cannot_claim_local_content_match():
    bad = [{"document_type": "purchase_order"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": bad}},
        {"normalized_documents": bad},
        expected_case_id="C001",
    )
    assert result["input_delivery_status"] == "QA_INPUT_MALFORMED"
    assert result["qa_status"] == "FAIL"


def test_qa_report_explicit_wrong_case_is_error():
    report = {"case_id": "C013", "issues": [], "execution_provenance": None}
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": DOCS}},
        {"normalized_documents": DOCS}, report,
        expected_case_id="C001",
    )
    assert result["qa_status"] == "FAIL"
    assert result["case_binding_conflict"] is True


def test_cli_blocks_missing_real_qa_input(tmp_path):
    step = tmp_path / "normalize.json"
    step.write_text(json.dumps({"status": "COMPLETED",
                                "output": {"documents": DOCS}}), encoding="utf-8")
    process = subprocess.run([
        sys.executable, str(CLI), "--normalize", str(step),
        "--case-id", "C001",
    ], cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    answer = json.loads(process.stdout)
    assert process.returncode == 2
    assert answer["input_delivery_status"] == "UNKNOWN"
    assert answer["actual_cloud_input_authenticated"] is False



def test_normalize_and_qa_boolean_false_not_equal_to_numeric_zero():
    normalize = [
        {"document_id": "PO-DOC", "document_type": "purchase_order",
         "items": [{"quantity": 0}]},
    ]
    qa = [
        {"document_id": "PO-DOC", "document_type": "purchase_order",
         "items": [{"quantity": False}]},
    ]
    report = audit_normalize_qa_input(
        {"status": "COMPLETED", "case_id": "C001",
         "output": {"documents": normalize}},
        {"case_id": "C001", "normalized_documents": qa},
        expected_case_id="C001",
    )
    assert report["qa_status"] == "FAIL"
    assert report["input_delivery_status"] == "LOCAL_CONTENT_MISMATCH"
    assert report["actual_cloud_input_authenticated"] is False


def test_boolean_true_not_equal_to_numeric_one_in_existing_qa_checker():
    normalize = [
        {"document_id": "PO-DOC", "document_type": "purchase_order",
         "items": [{"quantity": 1}]},
    ]
    qa = [
        {"document_id": "PO-DOC", "document_type": "purchase_order",
         "items": [{"quantity": True}]},
    ]
    report = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": normalize}},
        {"normalized_documents": qa},
    )
    assert report["qa_status"] == "FAIL"
    assert report["input_delivery_status"] == "LOCAL_CONTENT_MISMATCH"
