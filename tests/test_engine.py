"""B+C3 offline regression suite. Studio accuracy must be tested separately."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.engine import analyze_portfolio
from leadtime_guardian.studio_adapter import AdapterError, apply_studio_extractions


@pytest.fixture
def example():
    source = Path(__file__).resolve().parents[1] / "data/sample/portfolio_case.json"
    return json.loads(source.read_text(encoding="utf-8"))


def test_baseline_and_counterfactual(example):
    out = analyze_portfolio(example)
    assert out["status"] == "OK"
    assert (out["baseline_shortage_quantity"], out["changed_shortage_quantity"]) == (0, 60)
    assert out["additional_shortage_quantity"] == 60
    assert out["estimated_quote_cost_krw"] == "60500.00"
    assert out["external_action_taken"] is False
    assert out["evidence_verified_against_pdf"] is False


def test_po_conflict_blocks(example):
    example["documents"][1]["po_id"] = "OTHER"
    out = analyze_portfolio(example)
    assert out["execution_status"] == "BLOCKED"
    assert any("PO_PRODUCT_MISMATCH" in x for x in out["review_flags"])
    assert out["impacted_orders"] == []


def test_eta_conflict_blocks(example):
    example["documents"][1]["revised_delivery"] = "2026-11-07"
    assert any("DOCUMENT_ETA_MISMATCH" in x
               for x in analyze_portfolio(example)["review_flags"])


def test_no_documents_blocks(example):
    example["documents"] = []
    assert analyze_portfolio(example)["review_flags"] == ["NO_DOCUMENT_EVIDENCE"]


def test_duplicate_receipt_blocks(example):
    example["inbound"].append(deepcopy(example["inbound"][0]))
    assert analyze_portfolio(example)["execution_status"] == "BLOCKED"


def test_partial_receipts_two_orders(example):
    example["inventory"][0]["available_stock"] = 10
    example["orders"] = [
        {"order_id": "O1", "product_id": "A", "due_date": "2026-11-05", "quantity": 80},
        {"order_id": "O2", "product_id": "A", "due_date": "2026-11-07", "quantity": 40},
    ]
    example["inbound"] = [
        {"receipt_id": "R1", "po_id": "PO1", "product_id": "A",
         "original_eta": "2026-11-03", "eta": "2026-11-08", "quantity": 30},
        {"receipt_id": "R2", "po_id": "PO1", "product_id": "A",
         "original_eta": "2026-11-04", "eta": "2026-11-04", "quantity": 70},
    ]
    example["documents"][0].pop("original_delivery")
    example["quotes"] = []
    out = analyze_portfolio(example)
    assert out["status"] == "OK"
    assert out["baseline_shortage_quantity"] == 10
    assert out["changed_shortage_quantity"] == 40
    assert out["additional_shortage_quantity"] == 30
    assert [x["shortage_quantity"] for x in out["impacted_orders"]] == [0, 40]


def test_receipt_ambiguity_blocks(example):
    example["inbound"].append({**example["inbound"][0], "receipt_id": "R2"})
    example["documents"][1]["items"] = [{"product_id": "A"}]
    assert any("AMBIGUOUS_RECEIPT" in x
               for x in analyze_portfolio(example)["review_flags"])


def test_quote_capacity_shared_and_shipping_once(example):
    example["orders"].append({"order_id": "O2", "product_id": "A",
                              "due_date": "2026-11-05", "quantity": 20})
    out = analyze_portfolio(example)
    assert sum(x["quantity"] for x in out["supplier_options"]) == 60
    assert out["estimated_quote_cost_krw"] == "60500.00"


def test_adapter_maps_real_notice_to_one_receipt(example):
    original = deepcopy(example)
    original["documents"] = []
    original["inbound"][0]["eta"] = "2026-11-03"
    updated = apply_studio_extractions(original, example["documents"])
    assert updated["inbound"][0]["eta"] == "2026-11-08"
    assert original["inbound"][0]["eta"] == "2026-11-03"
    assert analyze_portfolio(updated)["status"] == "OK"


def test_adapter_rejects_ambiguous_mapping(example):
    example["inbound"].append({**example["inbound"][0], "receipt_id": "R2"})
    example["documents"][1]["items"] = [{"product_id": "A"}]
    with pytest.raises(AdapterError, match="ambiguous"):
        apply_studio_extractions(example, example["documents"])


@pytest.mark.parametrize("invalid", [True, -1, "3"])
def test_quantity_validation(example, invalid):
    example["orders"][0]["quantity"] = invalid
    assert analyze_portfolio(example)["execution_status"] == "BLOCKED"


def test_nan_quote_blocks(example):
    example["quotes"][0]["unit_price"] = "NaN"
    assert analyze_portfolio(example)["execution_status"] == "BLOCKED"


def test_late_quote_not_allocated(example):
    example["quotes"][0]["arrival_date"] = "2026-11-06"
    out = analyze_portfolio(example)
    assert out["uncovered_quantity"] == 60
    assert out["supplier_options"] == []
