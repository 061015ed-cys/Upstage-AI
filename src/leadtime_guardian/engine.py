"""Deterministic B+C3 lead-time engine. No live ordering, email, or AI arithmetic."""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation

VERSION = "1.1.0"
KINDS = {"purchase_order", "delivery_notice", "quotation", "other"}


def date_value(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name}: expected ISO YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name}: invalid ISO date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{name}: expected ISO YYYY-MM-DD")
    return parsed


def nonempty(row, name):
    value = row.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: nonempty string required")
    return value.strip()


def quantity(row, name):
    value = row.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name}: nonnegative integer required")
    return value


def money(row, name):
    value = row.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError(f"{name}: decimal string or integer required")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{name}: invalid decimal") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{name}: finite nonnegative decimal required")
    return amount


def rows(case, key):
    value = case.get(key)
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise ValueError(f"{key}: list of objects required")
    return value


def unique(items, field):
    identifiers = [nonempty(item, field) for item in items]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{field}: duplicate identifier")


def prepare(case):
    nonempty(case, "case_id")
    snapshot = date_value(case.get("snapshot_date"), "snapshot_date")
    stock, orders, inbound, quotes, documents = (
        rows(case, key) for key in ("inventory", "orders", "inbound", "quotes", "documents")
    )
    unique(stock, "product_id")
    unique(orders, "order_id")
    unique(inbound, "receipt_id")
    unique(quotes, "quote_id")
    known = {x["product_id"] for x in stock}
    inventory = {x["product_id"]: quantity(x, "available_stock") for x in stock}
    if not orders:
        raise ValueError("orders: empty")
    for row in orders:
        known.add(nonempty(row, "product_id"))
        quantity(row, "quantity")
        date_value(row.get("due_date"), "due_date")
    for row in inbound:
        nonempty(row, "po_id")
        sku = nonempty(row, "product_id")
        if sku not in known:
            raise ValueError(f"unknown inbound product: {sku}")
        row["_original"] = date_value(row.get("original_eta"), "original_eta")
        row["_revised"] = date_value(row.get("eta"), "eta")
        if row["_revised"] <= snapshot:
            raise ValueError("inbound ETA must be after snapshot_date")
        quantity(row, "quantity")
    for row in quotes:
        nonempty(row, "supplier_id")
        if row.get("currency", "KRW") != "KRW":
            raise ValueError("quote: unsupported currency")
        if nonempty(row, "product_id") not in known:
            raise ValueError("quote: unknown product")
        date_value(row.get("arrival_date"), "arrival_date")
        quantity(row, "capacity")
        money(row, "unit_price")
        money(row, "shipping_cost")
        nonempty(row, "supplier_risk")
    return inventory, orders, inbound, quotes, documents


def evidence_flags(inbound, documents):
    """Checks normalized extraction consistency, NOT PDF-origin verification."""
    if not documents:
        return ["NO_DOCUMENT_EVIDENCE"]
    flags, ids = [], set()
    pairs = {(x["po_id"], x["product_id"]) for x in inbound}
    for doc in documents:
        did = nonempty(doc, "document_id")
        if did in ids:
            flags.append(f"DUPLICATE_DOCUMENT:{did}")
        ids.add(did)
        kind = nonempty(doc, "document_type")
        if kind not in KINDS:
            flags.append(f"INVALID_TYPE:{did}")
            continue
        if doc.get("warnings"):
            flags.append(f"DOCUMENT_WARNINGS:{did}")
        if kind not in {"purchase_order", "delivery_notice"}:
            continue
        po = doc.get("po_id")
        items = doc.get("items")
        if not isinstance(po, str) or not isinstance(items, list) or not items:
            flags.append(f"MISSING_PO_OR_ITEMS:{did}")
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("product_id"):
                flags.append(f"MISSING_PRODUCT:{did}")
                continue
            sku = item["product_id"]
            if (po, sku) not in pairs:
                flags.append(f"PO_PRODUCT_MISMATCH:{did}:{po}:{sku}")
                continue
            matched = [r for r in inbound if r["po_id"] == po and r["product_id"] == sku]
            if item.get("receipt_id"):
                matched = [r for r in matched if r["receipt_id"] == item["receipt_id"]]
            elif kind == "delivery_notice" and len(matched) > 1:
                flags.append(f"AMBIGUOUS_RECEIPT:{did}:{sku}")
                continue
            if not matched:
                flags.append(f"RECEIPT_NOT_FOUND:{did}:{sku}")
                continue
            key = "revised_delivery" if kind == "delivery_notice" else "original_delivery"
            if kind == "delivery_notice" and not doc.get(key):
                flags.append(f"MISSING_REVISED_DATE:{did}")
                continue
            if doc.get(key):
                try:
                    parsed = date_value(doc[key], key)
                except ValueError:
                    flags.append(f"INVALID_DATE:{did}")
                    continue
                receipt_key = "_revised" if kind == "delivery_notice" else "_original"
                if any(r[receipt_key] != parsed for r in matched):
                    flags.append(f"DOCUMENT_ETA_MISMATCH:{did}:{sku}")
    if not any(d.get("document_type") == "purchase_order" for d in documents):
        flags.append("NO_PURCHASE_ORDER_DOCUMENT")
    if not any(d.get("document_type") == "delivery_notice" for d in documents):
        flags.append("NO_DELIVERY_NOTICE_DOCUMENT")
    return sorted(set(flags))


def allocate(inventory, orders, inbound, baseline):
    """Per SKU, earliest due date first; no customer receives the same stock twice."""
    by_sku = defaultdict(list)
    for receipt in inbound:
        eta = receipt["_original"] if baseline else receipt["_revised"]
        by_sku[receipt["product_id"]].append(
            (eta, receipt["receipt_id"], receipt["quantity"])
        )
    grouped = defaultdict(list)
    for order in orders:
        grouped[order["product_id"]].append(order)
    result = {}
    for sku, items in grouped.items():
        timeline = sorted(by_sku[sku])
        available, idx = inventory.get(sku, 0), 0
        for order in sorted(items, key=lambda o: (o["due_date"], o["order_id"])):
            deadline = date_value(order["due_date"], "due_date")
            while idx < len(timeline) and timeline[idx][0] <= deadline:
                available += timeline[idx][2]
                idx += 1
            granted = min(order["quantity"], available)
            available -= granted
            result[order["order_id"]] = {
                "order_id": order["order_id"], "product_id": sku,
                "due_date": order["due_date"], "required_quantity": order["quantity"],
                "allocated_quantity": granted,
                "shortage_quantity": order["quantity"] - granted,
            }
    return result


def quote_draft(orders, revised, quotes):
    """Draft only: shared capacity, one shipping charge per used quote, not optimal."""
    capacity = {q["quote_id"]: q["capacity"] for q in quotes}
    lines, uncovered = [], 0
    for order in sorted(orders, key=lambda o: (o["due_date"], o["order_id"])):
        need = revised[order["order_id"]]["shortage_quantity"]
        valid = [q for q in quotes if q["product_id"] == order["product_id"]
                 and q["arrival_date"] <= order["due_date"]]
        valid.sort(key=lambda q: (money(q, "unit_price"), q["quote_id"]))
        for quote in valid:
            take = min(need, capacity[quote["quote_id"]])
            if not take:
                continue
            capacity[quote["quote_id"]] -= take
            need -= take
            lines.append({
                "order_id": order["order_id"], "quote_id": quote["quote_id"],
                "supplier_id": quote["supplier_id"], "product_id": quote["product_id"],
                "quantity": take, "arrival_date": quote["arrival_date"],
                "unit_price": str(money(quote, "unit_price")),
                "supplier_risk": quote["supplier_risk"],
            })
            if need == 0:
                break
        uncovered += need
    used = {line["quote_id"] for line in lines}
    total = sum((Decimal(line["unit_price"]) * line["quantity"] for line in lines),
                Decimal(0))
    total += sum((money(q, "shipping_cost") for q in quotes if q["quote_id"] in used),
                 Decimal(0))
    return lines, uncovered, str(total)


def blocked_result(payload, flags):
    """Build a blocked response without attempting any allocation or quote calculation."""
    case_id = payload.get("case_id") if isinstance(payload, dict) else None
    return {
        "schema_version": VERSION,
        "case_id": case_id if isinstance(case_id, str) and case_id.strip() else "UNKNOWN",
        "status": "NEEDS_REVIEW",
        "execution_status": "BLOCKED", "needs_review": True,
        "review_flags": flags, "delays": [], "impacted_orders": [],
        "supplier_options": [], "uncovered_quantity": None,
        "baseline_shortage_quantity": None, "changed_shortage_quantity": None,
        "additional_shortage_quantity": None, "estimated_quote_cost_krw": None,
        "evidence_document_ids": [], "evidence_verified_against_pdf": False,
        "external_action_taken": False,
    }


def analyze_portfolio(payload):
    """Return safe, reproducible JSON. Never send purchases or email."""
    result = blocked_result(payload, [])
    try:
        if not isinstance(payload, dict):
            raise TypeError("payload must be object")
        inventory, orders, inbound, quotes, docs = prepare(deepcopy(payload))
        flags = evidence_flags(inbound, docs)
        result["evidence_document_ids"] = [d["document_id"] for d in docs]
    except (ValueError, TypeError, KeyError) as exc:
        result["review_flags"] = [f"INVALID_INPUT:{exc}"]
        return result
    if flags:
        result["review_flags"] = flags
        return result
    before = allocate(inventory, orders, inbound, True)
    after = allocate(inventory, orders, inbound, False)
    effects = []
    for order in sorted(orders, key=lambda o: (o["due_date"], o["order_id"])):
        oid = order["order_id"]
        old, new = before[oid]["shortage_quantity"], after[oid]["shortage_quantity"]
        effects.append({
            **after[oid], "baseline_shortage_quantity": old,
            "additional_shortage_quantity": max(0, new - old),
            "shortage_change": new - old,
        })
    choices, gap, cost = quote_draft(orders, after, quotes)
    result.update({
        "status": "OK", "execution_status": "COMPLETED", "needs_review": False,
        "delays": [{
            "receipt_id": r["receipt_id"], "po_id": r["po_id"],
            "product_id": r["product_id"],
            "delay_days": max(0, (r["_revised"] - r["_original"]).days),
        } for r in inbound],
        "impacted_orders": effects, "supplier_options": choices,
        "uncovered_quantity": gap,
        "baseline_shortage_quantity": sum(x["shortage_quantity"] for x in before.values()),
        "changed_shortage_quantity": sum(x["shortage_quantity"] for x in after.values()),
        "additional_shortage_quantity": sum(x["additional_shortage_quantity"] for x in effects),
        "estimated_quote_cost_krw": cost,
    })
    return result
