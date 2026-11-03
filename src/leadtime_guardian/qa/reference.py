"""Small independent allocation oracle for QA, deliberately not importing engine."""
from __future__ import annotations

from collections import defaultdict
from datetime import date


def _iso(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def _qty(value):
    return type(value) is int and value >= 0


def reference_allocations(case):
    """Return per-order baseline and revised allocation; None for invalid inputs.

    This independently computes deadline-aware quantity allocations using
    stock plus dated receipts and earliest-deadline / order-ID precedence.
    It never mutates inputs, issues purchases, or consults gold labels.
    """
    if not isinstance(case, dict):
        return None
    orders, receipts, inventory = (case.get(key) for key in ("orders", "inbound", "inventory"))
    if not all(isinstance(items, list) for items in (orders, receipts, inventory)):
        return None
    for stock in inventory:
        if not isinstance(stock, dict) or not isinstance(stock.get("product_id"), str) or not _qty(
            stock.get("available_stock")
        ):
            return None
    for incoming in receipts:
        if not isinstance(incoming, dict) or not isinstance(incoming.get("product_id"), str) or not _qty(
            incoming.get("quantity")
        ) or _iso(incoming.get("original_eta")) is None or _iso(incoming.get("eta")) is None:
            return None
    for order in orders:
        if not isinstance(order, dict) or not isinstance(order.get("order_id"), str) or not isinstance(
            order.get("product_id"), str
        ) or not _qty(order.get("quantity")) or _iso(order.get("due_date")) is None:
            return None
    if len({row["product_id"] for row in inventory}) != len(inventory) or len({
        row["order_id"] for row in orders
    }) != len(orders):
        return None
    output = defaultdict(dict)
    for mode, field in (("baseline", "original_eta"), ("revised", "eta")):
        for sku in {o["product_id"] for o in orders}:
            customer_orders = sorted(
                (o for o in orders if o["product_id"] == sku),
                key=lambda item: (item["due_date"], item["order_id"]),
            )
            initial = sum(s["available_stock"] for s in inventory if s["product_id"] == sku)
            received = sorted(
                (_iso(r[field]), r["quantity"]) for r in receipts if r["product_id"] == sku
            )
            receipt_index = 0
            for order in customer_orders:
                limit = _iso(order["due_date"])
                while receipt_index < len(received) and received[receipt_index][0] <= limit:
                    initial += received[receipt_index][1]
                    receipt_index += 1
                allocated = min(order["quantity"], initial)
                initial -= allocated
                output[order["order_id"]][mode] = {
                    "allocated": allocated,
                    "shortage": order["quantity"] - allocated,
                }
    return dict(output)
