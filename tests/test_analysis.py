import pytest

from leadtime_guardian.analysis import analyze_case


@pytest.fixture
def sample():
    return {
        "case_id": "SYN-C001",
        "po_id": "SYN-PO-1024",
        "product_id": "SYN-PART-A17",
        "original_delivery": "2026-11-03",
        "revised_delivery": "2026-11-08",
        "customer_deadline": "2026-11-05",
        "available_stock": 40,
        "required_quantity": 100,
        "incoming_quantity": 100,
    }


def test_delay_causes_shortage(sample):
    result = analyze_case(sample)
    assert result["delay_days"] == 5
    assert result["shortage_quantity"] == 60
    assert result["risk_level"] == "HIGH"


def test_on_time_covers_demand(sample):
    sample["revised_delivery"] = "2026-11-04"
    assert analyze_case(sample)["shortage_quantity"] == 0


def test_on_time_shortage_medium(sample):
    sample["revised_delivery"] = "2026-11-04"
    sample["incoming_quantity"] = 40
    result = analyze_case(sample)
    assert result["shortage_quantity"] == 20
    assert result["risk_level"] == "MEDIUM"


def test_missing_field(sample):
    del sample["required_quantity"]
    with pytest.raises(ValueError, match="Missing fields"):
        analyze_case(sample)


def test_negative_quantity(sample):
    sample["available_stock"] = -5
    with pytest.raises(ValueError, match="nonnegative integer"):
        analyze_case(sample)
