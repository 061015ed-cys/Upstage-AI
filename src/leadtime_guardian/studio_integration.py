"""Fail-closed boundary for normalized Studio exports; the existing engine is reused."""
from copy import deepcopy
from decimal import Decimal

from leadtime_guardian.engine import (
    analyze_portfolio,
    blocked_result,
    date_value,
    money,
    nonempty,
    prepare,
    quantity,
)
from leadtime_guardian.strict_json import loads_strict, validate_json_value
from leadtime_guardian.studio_adapter import AdapterError, apply_studio_extractions


def documents_from_export(raw, *, expected_job_id=None):
    """Accept one unambiguous normalized, observed native, or Agents envelope."""
    validate_json_value(raw)
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, dict):
        raise AdapterError("export must be a normalized array or object")
    if "human_reviewed" in raw or "provenance" in raw:
        raise AdapterError("gold/fixture wrappers are not accepted as Studio exports")
    if (("needs_review" in raw and raw["needs_review"] is not False)
            or raw.get("status") == "NEEDS_REVIEW" or raw.get("error")
            or raw.get("review_flags")):
        raise AdapterError("Studio output explicitly requires review or reports an error")
    if (("status" in raw and raw["status"] not in ("completed", "OK"))
            or ("execution_status" in raw and raw["execution_status"] != "COMPLETED")):
        raise AdapterError("Studio job did not complete")
    forms = [key for key in ("documents", "content", "output_text", "output") if key in raw]
    if len(forms) != 1:
        raise AdapterError("unsupported/ambiguous Studio envelope")
    if "metadata" in raw and "content" not in raw:
        raise AdapterError("unexpected native metadata without content")
    # Observed native Studio Instruct JSON download (C001, config v4).
    # Do not mutate its content or mistake its metadata for extraction facts.
    if "content" in raw:
        meta = raw.get("metadata")
        if (not isinstance(raw["content"], str)
                or not isinstance(meta, dict)
                or not isinstance(meta.get("job_execution_id"), str)
                or not meta["job_execution_id"].startswith("job_")
                or not meta["job_execution_id"][4:].strip()
                or not isinstance(meta.get("step_run_id"), str)
                or not meta["step_run_id"].strip()):
            raise AdapterError("invalid native Studio Instruct metadata/content")
        if "status" in meta and meta["status"] != "completed":
            raise AdapterError("native Studio job did not complete")
        if expected_job_id is not None and meta["job_execution_id"] != expected_job_id:
            raise AdapterError("native Studio job ID conflicts with requested run ID")
        return documents_from_export(loads_strict(raw["content"]),
                                     expected_job_id=meta["job_execution_id"])
    if "documents" in raw:
        if not isinstance(raw["documents"], list):
            raise AdapterError("documents must be an array")
        return raw["documents"]
    if "id" in raw and (not isinstance(raw["id"], str) or not raw["id"].strip()
                         or (expected_job_id is not None and raw["id"] != expected_job_id)):
        raise AdapterError("Agents job ID missing/conflicts with requested run ID")
    if (("output" in raw or "id" in raw or "status" in raw)
            and (raw.get("status") != "completed" or not isinstance(raw.get("id"), str))):
        raise AdapterError("Agents completed status and job ID required")
    if "output_text" in raw:
        if not isinstance(raw["output_text"], str):
            raise AdapterError("output_text must be a JSON string")
        return documents_from_export(loads_strict(raw["output_text"]),
                                     expected_job_id=raw.get("id", expected_job_id))
    messages = raw["output"]
    if not isinstance(messages, list) or not messages:
        raise AdapterError("output must be a nonempty array")
    texts = []
    for message in messages:
        if not isinstance(message, dict):
            raise AdapterError("output message must be an object")
        if message.get("type") != "message":
            raise AdapterError("unsupported output step; request include=last")
        if message.get("status") != "completed" or not isinstance(message.get("content"), list):
            raise AdapterError("output message incomplete/malformed")
        for part in message["content"]:
            if (not isinstance(part, dict) or part.get("type") != "output_text"
                    or not isinstance(part.get("text"), str)):
                raise AdapterError("unsupported output content")
            texts.append(part["text"])
    if len(texts) != 1:
        raise AdapterError("unsupported/ambiguous native export; inspect actual response first")
    return documents_from_export(loads_strict(texts[0]), expected_job_id=raw["id"])


def validate_documents(base_case, documents, schema):
    """Check schema, receipt facts, duplicate notices and quote facts before mutation."""
    from jsonschema import Draft202012Validator, FormatChecker

    if not isinstance(base_case, dict):
        raise AdapterError("trusted base case must be an object")
    prepare(deepcopy(base_case))
    validate_json_value(documents)
    if not isinstance(documents, list) or not documents:
        raise AdapterError("documents: nonempty array required")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    identifiers, notices, quote_ids, fingerprints = set(), set(), set(), set()
    extracted_quotes = []
    purchase_receipts = set()
    for doc in documents:
        errors = sorted(validator.iter_errors(doc), key=lambda error: str(error.path))
        if errors:
            raise AdapterError(f"schema: {errors[0].message}")
        did, kind = doc["document_id"], doc["document_type"]
        nonempty(doc, "document_id")
        if did in identifiers:
            raise AdapterError(f"duplicate document: {did}")
        identifiers.add(did)
        import json

        fingerprint = json.dumps({key: value for key, value in doc.items()
                                  if key not in {"document_id", "evidence"}}, sort_keys=True)
        if fingerprint in fingerprints:
            raise AdapterError(f"duplicate document facts: {did}")
        fingerprints.add(fingerprint)
        if doc["warnings"] or kind == "other":
            raise AdapterError(f"document requires review: {did}")
        if not doc["items"]:
            raise AdapterError(f"missing items: {did}")
        if kind in {"purchase_order", "delivery_notice"}:
            if kind == "purchase_order" and not doc.get("original_delivery"):
                raise AdapterError(f"missing original delivery: {did}")
            for item in doc["items"]:
                if item.get("receipt_id") is not None:
                    nonempty(item, "receipt_id")
                if item.get("unit") != "EA":
                    raise AdapterError(f"missing/unsupported unit: {did}")
                quantity(item, "quantity")
                matches = [row for row in base_case["inbound"]
                           if row["po_id"] == doc.get("po_id")
                           and row["product_id"] == item["product_id"]
                           and (not item.get("receipt_id")
                                or row["receipt_id"] == item["receipt_id"])]
                if len(matches) != 1:
                    raise AdapterError(f"ambiguous/unknown receipt: {did}")
                receipt = matches[0]
                if kind == "purchase_order":
                    if receipt["receipt_id"] in purchase_receipts:
                        raise AdapterError(f"duplicate purchase receipt: {did}")
                    purchase_receipts.add(receipt["receipt_id"])
                if item["quantity"] != receipt["quantity"]:
                    raise AdapterError(f"document quantity conflicts with inbound: {did}")
                if doc.get("original_delivery") != receipt["original_eta"]:
                    raise AdapterError(f"original date missing/conflicts with inbound: {did}")
                if kind == "delivery_notice":
                    if receipt["receipt_id"] in notices:
                        raise AdapterError(f"duplicate/conflicting receipt notice: {did}")
                    notices.add(receipt["receipt_id"])
        elif kind == "quotation":
            if any(item.get("unit") != "EA" for item in doc["items"]):
                raise AdapterError(f"missing/unsupported quote unit: {did}")
            q = deepcopy(doc.get("quote"))
            required = {"quote_id", "supplier_id", "product_id", "capacity", "arrival_date",
                        "unit_price", "shipping_cost", "currency"}
            if not isinstance(q, dict) or not required.issubset(q):
                raise AdapterError(f"missing quote fields: {did}")
            if q["currency"] != "KRW":
                raise AdapterError(f"unsupported currency: {did}")
            if any(not isinstance(q[key], str) or not q[key].strip()
                   for key in ("quote_id", "supplier_id", "product_id")):
                raise AdapterError(f"missing quote identifiers: {did}")
            if q["quote_id"] in quote_ids:
                raise AdapterError(f"duplicate quote: {did}")
            quote_ids.add(q["quote_id"])
            if q["supplier_id"] != doc.get("supplier_id") or len(doc["items"]) != 1:
                raise AdapterError(f"quote supplier/items conflict: {did}")
            item = doc["items"][0]
            quantity(item, "quantity")
            if q["product_id"] != item["product_id"] or q["capacity"] != item.get("quantity"):
                raise AdapterError(f"quote product/capacity conflict: {did}")
            if not any(row["po_id"] == doc.get("po_id")
                       and row["product_id"] == q["product_id"] for row in base_case["inbound"]):
                raise AdapterError(f"quote PO/product conflict: {did}")
            quantity(q, "capacity")
            date_value(q["arrival_date"], "arrival_date")
            money(q, "unit_price")
            money(q, "shipping_cost")
            for trusted in base_case.get("quotes", []):
                if trusted["quote_id"] == q["quote_id"]:
                    if trusted.get("currency", "KRW") != q["currency"]:
                        raise AdapterError(f"quote conflicts with trusted data: {did}:currency")
                    for key in required - {"currency"}:
                        if key in {"unit_price", "shipping_cost"}:
                            equal = Decimal(str(trusted[key])) == Decimal(str(q[key]))
                        else:
                            equal = trusted[key] == q[key]
                        if not equal:
                            raise AdapterError(f"quote conflicts with trusted data: {did}:{key}")
            # Risk is policy metadata, NOT a supplier fact inferred from the PDF.
            q["supplier_risk"] = "UNKNOWN"
            extracted_quotes.append(q)
    kinds = {doc["document_type"] for doc in documents}
    if not {"purchase_order", "delivery_notice", "quotation"}.issubset(kinds):
        raise AdapterError("C001 requires purchase_order, delivery_notice and quotation")
    if not notices.issubset(purchase_receipts):
        raise AdapterError("delivery notice has no matching purchase document receipt")
    return extracted_quotes


def analyze_studio_documents(base_case, documents, schema):
    """Normalized calculations only. This does not certify PDF source evidence."""
    try:
        quotes = validate_documents(base_case, documents, schema)
        case = apply_studio_extractions(base_case, documents)
        case["quotes"] = quotes
        return analyze_portfolio(case)
    except (AdapterError, ValueError, TypeError, KeyError) as exc:
        return blocked_result(base_case, [f"STUDIO_BOUNDARY:{exc}"])
