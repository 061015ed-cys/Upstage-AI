"""Independent reference allocation: catch internally consistent false PASS data."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.engine import analyze_portfolio
from leadtime_guardian.qa.portfolio import audit_portfolio
from leadtime_guardian.qa.reference import reference_allocations

ROOT = Path(__file__).resolve().parents[1]


def sample():
    return json.loads((ROOT / "data/sample/portfolio_case.json").read_text(encoding="utf-8"))


def issue_codes(report):
    return {x["issue_code"] for x in report["issues"]}


def test_reference_agrees_with_original_engine_for_local_case():
    case = sample()
    result = analyze_portfolio(case)
    assert result["status"] == "OK"
    assert audit_portfolio(case, result)["qa_status"] == "PASS"


def test_false_pass_consistent_revised_shortage_is_rejected():
    case = sample()
    result = analyze_portfolio(case)
    row = result["impacted_orders"][0]
    row.update({"allocated_quantity": 30, "shortage_quantity": 70,
                "additional_shortage_quantity": 70, "shortage_change": 70})
    result.update({"changed_shortage_quantity": 70, "additional_shortage_quantity": 70,
                   "uncovered_quantity": 10})
    assert "ALLOCATION_REFERENCE_MISMATCH" in issue_codes(audit_portfolio(case, result))


def test_false_pass_consistent_baseline_shortage_is_rejected():
    case = sample()
    result = analyze_portfolio(case)
    row = result["impacted_orders"][0]
    row.update({"baseline_shortage_quantity": 10,
                "additional_shortage_quantity": 50, "shortage_change": 50})
    result.update({"baseline_shortage_quantity": 10, "additional_shortage_quantity": 50})
    assert "ALLOCATION_REFERENCE_MISMATCH" in issue_codes(audit_portfolio(case, result))


def test_reference_partial_receipts_and_two_customers():
    case = sample()
    case["orders"] = [
        {"order_id": "O1", "product_id": "A", "due_date": "2026-11-05", "quantity": 50},
        {"order_id": "O2", "product_id": "A", "due_date": "2026-11-06", "quantity": 90},
    ]
    case["inbound"] = [
        {"receipt_id": "R1", "po_id": "PO1", "product_id": "A",
         "original_eta": "2026-11-03", "eta": "2026-11-06", "quantity": 50},
        {"receipt_id": "R2", "po_id": "PO1", "product_id": "A",
         "original_eta": "2026-11-03", "eta": "2026-11-08", "quantity": 50},
    ]
    reference = reference_allocations(case)
    assert reference == {
        "O1": {
            "baseline": {"allocated": 50, "shortage": 0},
            "revised": {"allocated": 40, "shortage": 10},
        },
        "O2": {
            "baseline": {"allocated": 90, "shortage": 0},
            "revised": {"allocated": 50, "shortage": 40},
        },
    }


def test_reference_order_input_permutation_is_invariant():
    case = sample()
    case["orders"].append({"order_id": "O2", "product_id": "A", "due_date": "2026-11-05", "quantity": 30})
    expected = reference_allocations(case)
    changed = deepcopy(case)
    changed["orders"].reverse()
    assert reference_allocations(changed) == expected


@pytest.mark.parametrize(("field", "value"), [
    ("due_date", "2026-02-30"), ("quantity", -1), ("quantity", True)
])
def test_reference_does_not_infer_bad_order_values(field, value):
    case = sample()
    case["orders"][0][field] = value
    assert reference_allocations(case) is None
