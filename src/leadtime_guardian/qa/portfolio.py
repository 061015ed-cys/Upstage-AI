"""Independent cross-checks for deterministic portfolio outputs (read only)."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from .reference import reference_allocations


def _valid_int(value):
    return type(value) is int and value >= 0


def _date(value):
    try:
        parsed = date.fromisoformat(value) if isinstance(value, str) else None
        return parsed if parsed is not None and parsed.isoformat() == value else None
    except ValueError:
        return None


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    try:
        d = Decimal(str(value))
        return d if d.is_finite() and d >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def audit_portfolio(case, result):
    """Reject mismatched totals, double-use, excessive quotes and unsupported actions.

    This validates contracts; it does not substitute human PDF verification.
    """
    problems = []

    def flag(code, field):
        problems.append({"issue_code": code, "field": field, "severity": "ERROR"})

    if not isinstance(case, dict) or not isinstance(result, dict):
        return {"qa_status": "FAIL", "issues": [{"issue_code": "INVALID_ARGUMENT", "field": "$"}]}
    if result.get("external_action_taken") is not False:
        flag("EXTERNAL_ACTION_NOT_DISPROVEN", "external_action_taken")
    if result.get("evidence_verified_against_pdf") is True:
        flag("UNSUPPORTED_SOURCE_VERIFICATION", "evidence_verified_against_pdf")
    if case.get("case_id") != result.get("case_id"):
        flag("CASE_ID_MISMATCH", "case_id")

    if result.get("status") == "NEEDS_REVIEW":
        if result.get("needs_review") is not True or result.get("execution_status") != "BLOCKED":
            flag("UNSAFE_REVIEW_STATE", "status")
        if result.get("supplier_options") != []:
            flag("BLOCKED_WITH_OPTIONS", "supplier_options")
        for field in ("impacted_orders", "delays"):
            if result.get(field) != []:
                flag("BLOCKED_WITH_CALCULATION", field)
        for field in ("uncovered_quantity", "baseline_shortage_quantity",
                      "changed_shortage_quantity", "additional_shortage_quantity",
                      "estimated_quote_cost_krw"):
            if result.get(field) is not None:
                flag("BLOCKED_WITH_TOTAL", field)
        flags = result.get("review_flags")
        if not isinstance(flags, list) or not flags or any(
            not isinstance(item, str) or not item.strip() for item in flags
        ):
            flag("MISSING_REVIEW_REASON", "review_flags")
        return {"qa_status": "FAIL" if problems else "PASS", "issues": problems}
    if (result.get("status"), result.get("execution_status"), result.get("needs_review")) != ("OK", "COMPLETED", False):
        flag("INVALID_SUCCESS_STATE", "status")
        return {"qa_status": "FAIL", "issues": problems}

    input_keys = ("inventory", "inbound", "orders", "quotes")
    output_keys = ("impacted_orders", "supplier_options", "delays")
    if any(not isinstance(case.get(k), list) for k in input_keys) or any(
        not isinstance(result.get(k), list) for k in output_keys
    ):
        flag("MISSING_DATA", "$")
        return {"qa_status": "FAIL", "issues": problems}
    arrays = [case[k] for k in input_keys] + [result[k] for k in output_keys]
    if any(not isinstance(row, dict) for rows in arrays for row in rows):
        flag("INVALID_ROW", "$")
        return {"qa_status": "FAIL", "issues": problems}
    if not case["orders"]:
        flag("EMPTY_ORDERS", "orders")
    for section in input_keys:
        for index, row in enumerate(case[section]):
            if not isinstance(row.get("product_id"), str) or not row["product_id"].strip():
                flag("INVALID_SOURCE_PRODUCT", f"{section}[{index}].product_id")
    for section, field in (("inventory", "product_id"), ("inbound", "receipt_id"),
                           ("orders", "order_id"), ("quotes", "quote_id")):
        identifiers = [r.get(field) for r in case[section]]
        if any(not isinstance(x, str) or not x for x in identifiers) or len({x for x in identifiers if isinstance(x, str)}) != len(identifiers):
            flag("INVALID_SOURCE_IDS", section)
    # Validate every source row before using it in arithmetic or dictionary lookup.
    # This gate is intentionally independent of the existing engine.
    for section, qty_field in (("inventory", "available_stock"), ("inbound", "quantity"),
                               ("orders", "quantity"), ("quotes", "capacity")):
        for index, row in enumerate(case[section]):
            if not _valid_int(row.get(qty_field)):
                flag("INVALID_SOURCE_QUANTITY", f"{section}[{index}].{qty_field}")
            required_dates = {
                "inventory": (), "inbound": ("original_eta", "eta"),
                "orders": ("due_date",), "quotes": ("arrival_date",),
            }[section]
            for name in required_dates:
                if _date(row.get(name)) is None:
                    flag("INVALID_SOURCE_DATE", f"{section}[{index}].{name}")
            if section == "quotes":
                for name in ("unit_price", "shipping_cost"):
                    if _decimal(row.get(name)) is None:
                        flag("INVALID_SOURCE_MONEY", f"{section}[{index}].{name}")
    if problems:
        return {"qa_status": "FAIL", "issues": problems}
    orders = {r["order_id"]: r for r in case["orders"]}
    quotes = {r["quote_id"]: r for r in case["quotes"]}
    receipts = {r["receipt_id"]: r for r in case["inbound"]}

    # Actual engine outputs must preserve document provenance; synthetic compact
    # QA fixtures without a documents section are evaluated separately.
    if "documents" in case:
        docs = case["documents"]
        if not isinstance(docs, list) or any(not isinstance(doc, dict) for doc in docs):
            flag("INVALID_SOURCE_DOCUMENTS", "documents")
        elif not docs:
            flag("SUCCESS_WITHOUT_DOCUMENTS", "documents")
        else:
            identifiers = [doc.get("document_id") for doc in docs]
            if (any(not isinstance(ident, str) or not ident.strip() for ident in identifiers)
                    or len({ident for ident in identifiers if isinstance(ident, str)}) != len(identifiers)):
                flag("INVALID_DOCUMENT_IDS", "documents")
            if result.get("evidence_document_ids") != identifiers:
                flag("EVIDENCE_DOCUMENT_IDS_MISMATCH", "evidence_document_ids")
        if result.get("review_flags") != []:
            flag("SUCCESS_WITH_REVIEW_FLAGS", "review_flags")
    effects = result["impacted_orders"]
    if len(effects) != len(orders):
        flag("ORDER_COUNT_MISMATCH", "impacted_orders")
    if len(result["delays"]) != len(receipts):
        flag("RECEIPT_COUNT_MISMATCH", "delays")
    seen = set()
    shortages = {}
    totals = {"changed_shortage_quantity": 0, "baseline_shortage_quantity": 0,
              "additional_shortage_quantity": 0}
    for i, row in enumerate(effects):
        oid = row.get("order_id")
        if not isinstance(oid, str) or oid not in orders or oid in seen:
            flag("INVALID_ORDER_REFERENCE", f"impacted_orders[{i}]")
            continue
        seen.add(oid)
        src = orders[oid]
        if row.get("product_id") != src.get("product_id") or row.get("due_date") != src.get("due_date"):
            flag("ORDER_FIELD_MISMATCH", f"impacted_orders[{i}]")
        required, allocated, shortage = (row.get(k) for k in ("required_quantity", "allocated_quantity", "shortage_quantity"))
        old, added, delta = (row.get(k) for k in ("baseline_shortage_quantity", "additional_shortage_quantity", "shortage_change"))
        if not all(_valid_int(v) for v in (required, allocated, shortage, old, added)) or type(delta) is not int:
            flag("INVALID_ORDER_ARITHMETIC", f"impacted_orders[{i}]")
            continue
        if required != src.get("quantity") or allocated + shortage != required:
            flag("ORDER_CONSERVATION_FAILED", f"impacted_orders[{i}]")
        if delta != shortage - old or added != max(0, delta):
            flag("SHORTAGE_CHANGE_MISMATCH", f"impacted_orders[{i}]")
        shortages[oid] = shortage
        totals["changed_shortage_quantity"] += shortage
        totals["baseline_shortage_quantity"] += old
        totals["additional_shortage_quantity"] += added
    for key, expected in totals.items():
        if not _valid_int(result.get(key)) or result[key] != expected:
            flag("AGGREGATE_SHORTAGE_MISMATCH", key)

    reference = reference_allocations(case)
    if reference is None:
        flag("REFERENCE_INPUT_INVALID", "case")
    else:
        for index, row in enumerate(effects):
            oid = row.get("order_id")
            expected = reference.get(oid) if isinstance(oid, str) else None
            if expected is None:
                continue
            if row.get("allocated_quantity") != expected["revised"]["allocated"] or row.get(
                "shortage_quantity"
            ) != expected["revised"]["shortage"] or row.get(
                "baseline_shortage_quantity"
            ) != expected["baseline"]["shortage"]:
                flag("ALLOCATION_REFERENCE_MISMATCH", f"impacted_orders[{index}]")

    # Prefix constraint: no inventory or inbound can serve two customers.
    for sku in {o.get("product_id") for o in case["orders"]}:
        deadlines = {_date(o.get("due_date")) for o in case["orders"] if o.get("product_id") == sku}
        if None in deadlines:
            flag("INVALID_DEADLINE", "orders")
            continue
        for limit in sorted(deadlines):
            allocated = sum(r["allocated_quantity"] for r in effects if r.get("product_id") == sku
                            and _date(r.get("due_date")) is not None and _date(r["due_date"]) <= limit
                            and _valid_int(r.get("allocated_quantity")))
            available = sum(r["available_stock"] for r in case["inventory"] if r.get("product_id") == sku
                            and _valid_int(r.get("available_stock")))
            available += sum(r["quantity"] for r in case["inbound"] if r.get("product_id") == sku
                             and _date(r.get("eta")) is not None and _date(r["eta"]) <= limit
                             and _valid_int(r.get("quantity")))
            if allocated > available:
                flag("STOCK_DOUBLE_ALLOCATION", f"{sku}:{limit}")

    delays_seen = set()
    for i, row in enumerate(result["delays"]):
        rid = row.get("receipt_id")
        if not isinstance(rid, str) or rid not in receipts or rid in delays_seen:
            flag("INVALID_DELAY_REFERENCE", f"delays[{i}]")
            continue
        delays_seen.add(rid)
        src = receipts[rid]
        first, last = _date(src.get("original_eta")), _date(src.get("eta"))
        if first is None or last is None or row.get("delay_days") != max(0, (last - first).days) or row.get("po_id") != src.get("po_id") or row.get("product_id") != src.get("product_id"):
            flag("DELAY_MISMATCH", f"delays[{i}]")

    capacities = defaultdict(int)
    purchased = defaultdict(int)
    cost = Decimal(0)
    for i, line in enumerate(result["supplier_options"]):
        path = f"supplier_options[{i}]"
        quote_id, order_id = line.get("quote_id"), line.get("order_id")
        if not isinstance(quote_id, str) or not isinstance(order_id, str):
            flag("INVALID_OPTION_REFERENCE", path)
            continue
        quote, order = quotes.get(quote_id), orders.get(order_id)
        if quote is None or order is None:
            flag("UNKNOWN_QUOTE_OR_ORDER", path)
            continue
        count = line.get("quantity")
        if not _valid_int(count) or not count:
            flag("INVALID_OPTION_QUANTITY", path)
            continue
        eta, deadline = _date(quote.get("arrival_date")), _date(order.get("due_date"))
        if eta is None or deadline is None or eta > deadline:
            flag("LATE_SUPPLIER_OPTION", path)
        for key in ("product_id", "supplier_id", "arrival_date", "supplier_risk"):
            if line.get(key) != quote.get(key):
                flag("QUOTE_FIELD_MISMATCH", path + "." + key)
        if line.get("product_id") != order.get("product_id"):
            flag("ORDER_PRODUCT_MISMATCH", path)
        price = _decimal(quote.get("unit_price"))
        if price is None or _decimal(line.get("unit_price")) != price:
            flag("QUOTE_PRICE_MISMATCH", path)
        else:
            cost += price * count
        capacities[quote["quote_id"]] += count
        purchased[order["order_id"]] += count
    for qid, count in capacities.items():
        if not _valid_int(quotes[qid].get("capacity")) or count > quotes[qid]["capacity"]:
            flag("QUOTE_CAPACITY_EXCEEDED", qid)
        shipping = _decimal(quotes[qid].get("shipping_cost"))
        if shipping is None:
            flag("INVALID_SHIPPING", qid)
        else:
            cost += shipping
    for oid, count in purchased.items():
        if oid in shortages and count > shortages[oid]:
            flag("OVERPURCHASE", oid)
    if not _valid_int(result.get("uncovered_quantity")) or result["uncovered_quantity"] != sum(
        shortages.values()
    ) - sum(purchased.values()):
        flag("UNCOVERED_MISMATCH", "uncovered_quantity")
    if _decimal(result.get("estimated_quote_cost_krw")) != cost:
        flag("COST_MISMATCH", "estimated_quote_cost_krw")
    return {"qa_status": "FAIL" if problems else "PASS", "issues": problems}
