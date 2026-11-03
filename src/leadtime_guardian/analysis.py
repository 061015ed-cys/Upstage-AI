"""Deterministic lead-time risk calculations for a synthetic demo case."""
from __future__ import annotations

from datetime import date
from typing import Any

REQUIRED_FIELDS = (
    "case_id", "po_id", "product_id", "original_delivery",
    "revised_delivery", "customer_deadline", "available_stock",
    "required_quantity", "incoming_quantity",
)


def nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def analyze_case(case: dict[str, Any]) -> dict[str, Any]:
    """One customer order + one changed purchase-order arrival (MVP assumption)."""
    missing = [field for field in REQUIRED_FIELDS if field not in case]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    original = date.fromisoformat(case["original_delivery"])
    revised = date.fromisoformat(case["revised_delivery"])
    deadline = date.fromisoformat(case["customer_deadline"])

    stock = nonnegative_int(case["available_stock"], "available_stock")
    required = nonnegative_int(case["required_quantity"], "required_quantity")
    incoming = nonnegative_int(case["incoming_quantity"], "incoming_quantity")

    available = stock + (incoming if revised <= deadline else 0)
    shortage = max(0, required - available)
    delay_days = max(0, (revised - original).days)

    if shortage == 0:
        risk = "LOW"
        action = "고객 납기 내 수량 확보 가능. 변경 사항 기록 및 모니터링."
    elif revised > deadline:
        risk = "HIGH"
        action = f"납기 전 {shortage}개 부족 예상. 대체 업체·긴급 발주 검토."
    else:
        risk = "MEDIUM"
        action = f"납기 전 {shortage}개 부족 예상. 추가 물량 확보 검토."

    return {
        "case_id": case["case_id"],
        "po_id": case["po_id"],
        "product_id": case["product_id"],
        "original_delivery": original.isoformat(),
        "revised_delivery": revised.isoformat(),
        "customer_deadline": deadline.isoformat(),
        "delay_days": delay_days,
        "available_by_deadline": available,
        "shortage_quantity": shortage,
        "risk_level": risk,
        "recommended_action": action,
        "needs_review": False,
    }
