"""Adversarial QA boundary tests against real engine-shaped local output.

These do not change the engine and do not execute Studio.
"""
import json
from pathlib import Path

import pytest

from leadtime_guardian.engine import analyze_portfolio
from leadtime_guardian.qa import audit_case
from leadtime_guardian.qa.portfolio import audit_portfolio

ROOT = Path(__file__).resolve().parents[1]


def sample():
    return json.loads((ROOT / "data/sample/portfolio_case.json").read_text(encoding="utf-8"))


def prepared():
    case = sample()
    result = analyze_portfolio(case)
    assert result["status"] == "OK"
    return case, result


def codes(report):
    return {item["issue_code"] for item in report["issues"]}


def test_real_engine_quote_with_integer_prices_is_accepted():
    case = sample()
    case["quotes"][0]["unit_price"] = 1000
    case["quotes"][0]["shipping_cost"] = 500
    assert analyze_portfolio(case)["status"] == "OK"
    assert audit_case(case)["qa_status"] == "PASS"
    assert audit_portfolio(case, analyze_portfolio(case))["qa_status"] == "PASS"


@pytest.mark.parametrize(("section", "field", "expected"), [
    ("impacted_orders", "order_id", "INVALID_ORDER_REFERENCE"),
    ("delays", "receipt_id", "INVALID_DELAY_REFERENCE"),
    ("supplier_options", "quote_id", "INVALID_OPTION_REFERENCE"),
    ("supplier_options", "order_id", "INVALID_OPTION_REFERENCE"),
])
@pytest.mark.parametrize("value", [[], {"bad": "value"}])
def test_unhashable_output_ids_fail_closed(section, field, expected, value):
    case, result = prepared()
    result[section][0][field] = value
    assert expected in codes(audit_portfolio(case, result))


@pytest.mark.parametrize("section", ["inventory", "orders", "inbound", "quotes"])
def test_unhashable_source_sku_fails_closed(section):
    case, result = prepared()
    case[section][0]["product_id"] = ["bad"]
    assert "INVALID_SOURCE_PRODUCT" in codes(audit_portfolio(case, result))


def test_changed_delay_product_is_detected():
    case, result = prepared()
    result["delays"][0]["product_id"] = "DIFFERENT_SKU"
    assert "DELAY_MISMATCH" in codes(audit_portfolio(case, result))


def test_changed_supplier_risk_is_detected():
    case, result = prepared()
    assert result["supplier_options"]
    result["supplier_options"][0]["supplier_risk"] = "INVENTED"
    assert "QUOTE_FIELD_MISMATCH" in codes(audit_portfolio(case, result))


def test_empty_order_case_cannot_receive_success():
    case, result = prepared()
    case["orders"] = []
    assert "EMPTY_ORDERS" in codes(audit_portfolio(case, result))


def test_legitimate_engine_case_still_passes_without_mutations():
    case, result = prepared()
    assert audit_case(case)["qa_status"] == "PASS"
    assert audit_portfolio(case, result)["qa_status"] == "PASS"
