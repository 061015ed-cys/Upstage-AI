"""Independent portfolio validation with explicit adversarial mutations."""
from copy import deepcopy

import pytest

from leadtime_guardian.qa.portfolio import audit_portfolio


def sample():
    case = {
        "case_id": "SYN-C001",
        "inventory": [{"product_id": "A", "available_stock": 40}],
        "inbound": [{"receipt_id": "R1", "po_id": "PO1", "product_id": "A",
                     "original_eta": "2026-11-03", "eta": "2026-11-08", "quantity": 100}],
        "orders": [{"order_id": "O1", "product_id": "A", "due_date": "2026-11-05", "quantity": 100}],
        "quotes": [{"quote_id": "Q1", "supplier_id": "S1", "product_id": "A", "capacity": 60,
                    "arrival_date": "2026-11-04", "unit_price": "1000.00", "shipping_cost": "500.00"}],
    }
    result = {
        "case_id": "SYN-C001", "status": "OK", "execution_status": "COMPLETED",
        "needs_review": False, "external_action_taken": False, "evidence_verified_against_pdf": False,
        "delays": [{"receipt_id": "R1", "po_id": "PO1", "product_id": "A", "delay_days": 5}],
        "impacted_orders": [{"order_id": "O1", "product_id": "A", "due_date": "2026-11-05",
                             "required_quantity": 100, "allocated_quantity": 40, "shortage_quantity": 60,
                             "baseline_shortage_quantity": 0, "additional_shortage_quantity": 60,
                             "shortage_change": 60}],
        "supplier_options": [{"order_id": "O1", "quote_id": "Q1", "supplier_id": "S1",
                              "product_id": "A", "quantity": 60, "arrival_date": "2026-11-04",
                              "unit_price": "1000.00"}],
        "uncovered_quantity": 0, "baseline_shortage_quantity": 0,
        "changed_shortage_quantity": 60, "additional_shortage_quantity": 60,
        "estimated_quote_cost_krw": "60500.00",
    }
    return case, result


def error_codes(case, result):
    return {x["issue_code"] for x in audit_portfolio(case, result)["issues"]}


def test_compatible_with_c001_calculation_shape():
    case, result = sample()
    assert audit_portfolio(case, result)["qa_status"] == "PASS"


@pytest.mark.parametrize(("field", "value", "code"), [
    ("case_id", "WRONG", "CASE_ID_MISMATCH"),
    ("external_action_taken", True, "EXTERNAL_ACTION_NOT_DISPROVEN"),
    ("evidence_verified_against_pdf", True, "UNSUPPORTED_SOURCE_VERIFICATION"),
    ("changed_shortage_quantity", 59, "AGGREGATE_SHORTAGE_MISMATCH"),
    ("baseline_shortage_quantity", 2, "AGGREGATE_SHORTAGE_MISMATCH"),
    ("estimated_quote_cost_krw", "60000", "COST_MISMATCH"),
    ("uncovered_quantity", 3, "UNCOVERED_MISMATCH"),
    ("needs_review", True, "INVALID_SUCCESS_STATE"),
    ("supplier_options", [], "UNCOVERED_MISMATCH"),
])
def test_output_failures(field, value, code):
    case, result = sample()
    result[field] = value
    assert code in error_codes(case, result)


@pytest.mark.parametrize(("section", "field", "value", "code"), [
    ("supplier_options", "quantity", 61, "QUOTE_CAPACITY_EXCEEDED"),
    ("supplier_options", "quote_id", "Q999", "UNKNOWN_QUOTE_OR_ORDER"),
    ("supplier_options", "product_id", "B", "QUOTE_FIELD_MISMATCH"),
    ("supplier_options", "arrival_date", "2026-11-07", "QUOTE_FIELD_MISMATCH"),
    ("impacted_orders", "shortage_quantity", 50, "ORDER_CONSERVATION_FAILED"),
    ("impacted_orders", "allocated_quantity", 100, "ORDER_CONSERVATION_FAILED"),
    ("impacted_orders", "additional_shortage_quantity", 59, "SHORTAGE_CHANGE_MISMATCH"),
    ("delays", "delay_days", 0, "DELAY_MISMATCH"),
])
def test_mutated_lines_fail(section, field, value, code):
    case, result = sample()
    result[section][0][field] = value
    assert code in error_codes(case, result)


def test_late_quote_rejected():
    case, result = sample()
    case["quotes"][0]["arrival_date"] = "2026-11-06"
    result["supplier_options"][0]["arrival_date"] = "2026-11-06"
    assert "LATE_SUPPLIER_OPTION" in error_codes(case, result)


def test_duplicate_quote_capacity_overseas():
    case, result = sample()
    case["orders"].append({"order_id": "O2", "product_id": "A", "due_date": "2026-11-05", "quantity": 20})
    second = deepcopy(result["impacted_orders"][0])
    second.update({"order_id": "O2", "required_quantity": 20, "allocated_quantity": 0,
                   "shortage_quantity": 20, "additional_shortage_quantity": 20, "shortage_change": 20})
    result["impacted_orders"].append(second)
    option = deepcopy(result["supplier_options"][0])
    option.update({"order_id": "O2", "quantity": 10})
    result["supplier_options"].append(option)
    result.update({"changed_shortage_quantity": 80, "additional_shortage_quantity": 80,
                   "uncovered_quantity": 10, "estimated_quote_cost_krw": "70500.00"})
    assert "QUOTE_CAPACITY_EXCEEDED" in error_codes(case, result)


def test_cannot_reuse_stock():
    case, result = sample()
    case["orders"].append({"order_id": "O2", "product_id": "A", "due_date": "2026-11-05", "quantity": 40})
    second = deepcopy(result["impacted_orders"][0])
    second.update({"order_id": "O2", "required_quantity": 40, "allocated_quantity": 40,
                   "shortage_quantity": 0, "additional_shortage_quantity": 0, "shortage_change": 0})
    result["impacted_orders"].append(second)
    assert "STOCK_DOUBLE_ALLOCATION" in error_codes(case, result)


def test_blocked_result_cannot_contain_options():
    case, result = sample()
    result.update({"status": "NEEDS_REVIEW", "needs_review": True, "execution_status": "BLOCKED"})
    assert "BLOCKED_WITH_OPTIONS" in error_codes(case, result)


def test_clean_blocked_result_allowed():
    case, result = sample()
    result.update({
        "status": "NEEDS_REVIEW", "needs_review": True, "execution_status": "BLOCKED",
        "supplier_options": [], "impacted_orders": [], "delays": [],
        "uncovered_quantity": None, "review_flags": ["MISMATCHED_PO"],
        "baseline_shortage_quantity": None, "changed_shortage_quantity": None,
        "additional_shortage_quantity": None, "estimated_quote_cost_krw": None,
    })
    assert audit_portfolio(case, result)["qa_status"] == "PASS"


def test_non_iso_date_and_missing_data_fail_safely():
    case, result = sample()
    case["orders"][0]["due_date"] = "2026년 11월 5일"
    result["impacted_orders"][0]["due_date"] = "2026년 11월 5일"
    assert audit_portfolio(case, result)["qa_status"] == "FAIL"
    assert audit_portfolio({}, result)["qa_status"] == "FAIL"


@pytest.mark.parametrize(("field", "value", "code"), [
    ("impacted_orders", [{"order_id": "O1"}], "BLOCKED_WITH_CALCULATION"),
    ("delays", [{"receipt_id": "R1"}], "BLOCKED_WITH_CALCULATION"),
    ("changed_shortage_quantity", 60, "BLOCKED_WITH_TOTAL"),
    ("estimated_quote_cost_krw", "60500", "BLOCKED_WITH_TOTAL"),
    ("review_flags", [], "MISSING_REVIEW_REASON"),
    ("review_flags", [""], "MISSING_REVIEW_REASON"),
])
def test_blocked_state_does_not_leak_results(field, value, code):
    case, result = sample()
    result.update({
        "status": "NEEDS_REVIEW", "needs_review": True, "execution_status": "BLOCKED",
        "supplier_options": [], "impacted_orders": [], "delays": [],
        "uncovered_quantity": None, "review_flags": ["DATA_CONFLICT"],
        "baseline_shortage_quantity": None, "changed_shortage_quantity": None,
        "additional_shortage_quantity": None, "estimated_quote_cost_krw": None,
    })
    result[field] = value
    assert code in error_codes(case, result)
