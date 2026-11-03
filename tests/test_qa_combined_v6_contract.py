"""Actual combined tree: Team2 safety V6 + independent QA reference cross-check.

DRAFT synthetic cases are NEVER Studio output or human-reviewed Gold.
Operational C001 V4 is archived (not a current QA Sandbox run).
"""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.portfolio import audit_portfolio
from leadtime_guardian.studio_adapter import apply_studio_extractions
from leadtime_guardian.studio_integration import (
    analyze_studio_documents,
    documents_from_export,
    validate_documents,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = load_json_strict(
    (ROOT / "configs/schemas/document_extraction.schema.json").read_bytes()
)


def synthetic(number):
    location = ROOT / f"data/cases/SYN-C{number:03}"
    base = load_json_strict((location / "trusted_base_case.json").read_bytes())
    draft = load_json_strict((location / "extraction_gold.DRAFT.json").read_bytes())
    assert draft["human_reviewed"] is False
    with pytest.raises(ValueError, match="gold/fixture"):
        documents_from_export(draft)
    return base, draft["documents"]


def independent_check(base, docs, output):
    """QA independently checks Team2 calculation against a source-case copy."""
    if output["execution_status"] != "COMPLETED":
        return audit_portfolio(base, output)
    case = apply_studio_extractions(base, docs)
    case["quotes"] = validate_documents(base, docs, SCHEMA)
    return audit_portfolio(case, output)


def test_combined_c001_archived_native_engine_plus_qa_reference():
    archive = ROOT / "data/results/studio_runs/C001_20261030_v4/instruct_original.json"
    native = load_json_strict(archive.read_bytes())
    docs = documents_from_export(
        native, expected_job_id=native["metadata"]["job_execution_id"]
    )
    base = load_json_strict(
        (ROOT / "data/cases/SYN-C001/trusted_base_case.json").read_bytes()
    )
    unchanged = deepcopy((base, docs))
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["execution_status"] == "COMPLETED"
    assert (result["baseline_shortage_quantity"],
            result["changed_shortage_quantity"],
            result["additional_shortage_quantity"]) == (0, 60, 60)
    assert Decimal(result["estimated_quote_cost_krw"]) == Decimal(60500)
    assert independent_check(base, docs, result)["qa_status"] == "PASS"
    assert result["evidence_verified_against_pdf"] is False
    assert result["external_action_taken"] is False
    assert (base, docs) == unchanged


def test_combined_c013_cross_po_is_blocked_and_qa_confirms_safety():
    base, docs = synthetic(13)
    original = deepcopy((base, docs))
    assert docs[0]["po_id"] == "PO1"
    assert docs[1]["po_id"] == "PO999"
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["execution_status"] == "BLOCKED"
    assert result["baseline_shortage_quantity"] is None
    assert result["estimated_quote_cost_krw"] is None
    assert independent_check(base, docs, result)["qa_status"] == "PASS"
    assert (base, docs) == original


def test_combined_c008_receipt_isolation_and_independent_reference():
    base, docs = synthetic(8)
    receipts = [x["receipt_id"] for x in base["inbound"]]
    assert receipts == ["R1", "R2"]
    assert [x["quantity"] for x in base["inbound"]] == [40, 60]
    assert docs[1]["items"][0]["receipt_id"] == "R2"
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["execution_status"] == "COMPLETED"
    assert result["changed_shortage_quantity"] == 40
    assert Decimal(result["estimated_quote_cost_krw"]) == Decimal(40500)
    assert independent_check(base, docs, result)["qa_status"] == "PASS"
    assert [x["eta"] for x in apply_studio_extractions(base, docs)["inbound"]] == [
        "2026-11-03", "2026-11-08",
    ]


def test_combined_c017_draft_iso_date_is_not_korean_ocr_evidence():
    base, docs = synthetic(17)
    assert docs[1]["revised_delivery"] == "2026-11-08"
    original = deepcopy((base, docs))
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["execution_status"] == "COMPLETED"
    assert independent_check(base, docs, result)["qa_status"] == "PASS"
    assert result["evidence_verified_against_pdf"] is False
    docs[1]["revised_delivery"] = "2026년 11월 8일"
    wrong = analyze_studio_documents(base, docs, SCHEMA)
    assert wrong["execution_status"] == "BLOCKED"
    assert wrong["changed_shortage_quantity"] is None
    assert independent_check(base, docs, wrong)["qa_status"] == "PASS"
    assert docs[1]["revised_delivery"] != original[1][1]["revised_delivery"]


def test_combined_null_empty_quoted_null_and_zero_fail_closed():
    base, docs = synthetic(8)
    for bad in (None, "", "null", [], "49", 0, -1):
        changed = deepcopy(docs)
        changed[1]["items"][0]["quantity"] = bad
        result = analyze_studio_documents(base, changed, SCHEMA)
        assert result["execution_status"] == "BLOCKED", bad
        assert result["supplier_options"] == []
        assert result["estimated_quote_cost_krw"] is None
        assert independent_check(base, changed, result)["qa_status"] == "PASS"
