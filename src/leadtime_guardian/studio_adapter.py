"""Normalize Studio-extracted delivery notice dates onto uniquely matched CSV receipts."""
from copy import deepcopy
from datetime import date


class AdapterError(ValueError):
    """A document cannot be safely mapped to trusted inventory records."""


def apply_studio_extractions(base_case, predictions):
    """Low-level mapping; use analyze_studio_documents for the full validation boundary."""
    if not isinstance(predictions, list):
        raise AdapterError("predictions: expected list")
    case = deepcopy(base_case)
    case["documents"] = deepcopy(predictions)
    notices = set()
    for doc in predictions:
        if not isinstance(doc, dict):
            raise AdapterError("prediction: expected object")
        if doc.get("document_type") != "delivery_notice":
            continue
        if doc.get("warnings"):
            raise AdapterError("delivery_notice: requires review")
        eta = doc.get("revised_delivery")
        try:
            if not isinstance(eta, str) or date.fromisoformat(eta).isoformat() != eta:
                raise ValueError("bad date")
        except ValueError as exc:
            raise AdapterError("delivery_notice: revised_delivery missing/invalid") from exc
        items = doc.get("items")
        if not isinstance(items, list) or not items:
            raise AdapterError("delivery_notice: items missing")
        for item in items:
            if not isinstance(item, dict):
                raise AdapterError("delivery_notice: item malformed")
            matches = [
                row for row in case["inbound"]
                if row.get("po_id") == doc.get("po_id")
                and row.get("product_id") == item.get("product_id")
                and (not item.get("receipt_id")
                     or row.get("receipt_id") == item.get("receipt_id"))
            ]
            if len(matches) != 1:
                raise AdapterError(f"ambiguous/unknown receipt: {doc.get('document_id')}")
            receipt = matches[0]
            if receipt["receipt_id"] in notices:
                raise AdapterError("duplicate/conflicting receipt notice")
            notices.add(receipt["receipt_id"])
            if (doc.get("original_delivery") is not None
                    and doc["original_delivery"] != receipt["original_eta"]):
                raise AdapterError("original date conflicts with inbound")
            if "quantity" in item and (type(item["quantity"]) is not int
                                        or item["quantity"] != receipt["quantity"]):
                raise AdapterError("document quantity conflicts with inbound")
            receipt["eta"] = eta
    return case
