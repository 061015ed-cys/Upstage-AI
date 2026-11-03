"""Fail-closed source preflight and evidence binding for successful calculations.

Uses the real deterministic engine only to obtain valid starting outputs;
original engine, Studio Adapter, PDFs and Gold are not modified.
"""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.engine import analyze_portfolio
from leadtime_guardian.qa.portfolio import audit_portfolio

ROOT = Path(__file__).resolve().parents[1]


def base():
    return json.loads((ROOT / "data/sample/portfolio_case.json").read_text(encoding="utf-8"))


def baseline():
    case = base()
    output = analyze_portfolio(deepcopy(case))
    assert output["status"] == "OK"
    return case, output


def errors(case, output):
    return {problem["issue_code"] for problem in audit_portfolio(case, output)["issues"]}


@pytest.mark.parametrize(("section", "field", "bad"), [
    ("inventory", "available_stock", []),
    ("inventory", "available_stock", -1),
    ("orders", "quantity", {"x": 1}),
    ("orders", "quantity", True),
    ("inbound", "quantity", "100"),
    ("inbound", "quantity", None),
    ("quotes", "capacity", []),
    ("quotes", "capacity", -1),
])
def test_invalid_source_quantities_never_crash_or_pass(section, field, bad):
    case, result = baseline()
    case[section][0][field] = bad
    assert "INVALID_SOURCE_QUANTITY" in errors(case, result)


@pytest.mark.parametrize(("section", "field", "bad"), [
    ("inbound", "original_eta", "2026-02-30"),
    ("inbound", "eta", None),
    ("orders", "due_date", "2026년 11월 05일"),
    ("quotes", "arrival_date", 123),
])
def test_invalid_source_dates_fail_without_exception(section, field, bad):
    case, result = baseline()
    case[section][0][field] = bad
    assert "INVALID_SOURCE_DATE" in errors(case, result)


@pytest.mark.parametrize(("field", "bad"), [
    ("unit_price", []),
    ("unit_price", "Infinity"),
    ("shipping_cost", {"x": 0}),
    ("shipping_cost", False),
    ("shipping_cost", "-2.00"),
])
def test_unused_broken_quote_money_is_still_rejected(field, bad):
    case, result = baseline()
    case["quotes"].append({
        "quote_id": "Q_UNUSED", "supplier_id": "S2", "product_id": "A",
        "arrival_date": "2026-11-20", "capacity": 10,
        "unit_price": "1.00", "shipping_cost": "0",
        "supplier_risk": "UNKNOWN",
    })
    case["quotes"][1][field] = bad
    assert "INVALID_SOURCE_MONEY" in errors(case, result)


@pytest.mark.parametrize("tampered", [
    ["OTHER-DOC", "NOTICE-DOC"],
    ["PO-DOC", "PO-DOC"],
    [],
    "PO-DOC",
    None,
])
def test_success_evidence_must_match_source_document_ids(tampered):
    case, result = baseline()
    result["evidence_document_ids"] = tampered
    assert "EVIDENCE_DOCUMENT_IDS_MISMATCH" in errors(case, result)


def test_success_cannot_retain_review_flags():
    case, result = baseline()
    result["review_flags"] = ["NO_DOCUMENT_EVIDENCE"]
    assert "SUCCESS_WITH_REVIEW_FLAGS" in errors(case, result)


def test_success_must_have_source_documents_when_present():
    case, result = baseline()
    case["documents"] = []
    assert "SUCCESS_WITHOUT_DOCUMENTS" in errors(case, result)


def test_duplicate_source_document_id_is_rejected():
    case, result = baseline()
    case["documents"][1]["document_id"] = case["documents"][0]["document_id"]
    assert "INVALID_DOCUMENT_IDS" in errors(case, result)


def test_real_engine_success_passes_source_preflight():
    case, result = baseline()
    assert audit_portfolio(case, result)["qa_status"] == "PASS"


def test_quote_arriving_on_customer_due_date_is_valid():
    case = base()
    case["quotes"][0]["arrival_date"] = case["orders"][0]["due_date"]
    result = analyze_portfolio(deepcopy(case))
    assert result["status"] == "OK"
    assert audit_portfolio(case, result)["qa_status"] == "PASS"


def test_zero_inventory_is_valid_if_engine_consistent():
    case = base()
    case["inventory"][0]["available_stock"] = 0
    result = analyze_portfolio(deepcopy(case))
    assert result["status"] == "OK"
    assert audit_portfolio(case, result)["qa_status"] == "PASS"
