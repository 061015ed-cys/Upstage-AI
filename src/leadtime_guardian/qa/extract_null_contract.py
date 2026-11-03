"""Compare preserved Studio Extract DRAFT schemas to final Python schema.

This is a static contract audit, NOT proof of the Studio UI/schema runtime.
Do not silently coerce 0, "null", absent values, array quote or valid PDF facts.
"""
from __future__ import annotations

from typing import Any

BRANCHES = frozenset({
    "Extract_purchase_order", "Extract_delivery_notice",
    "Extract_quotation", "Extract_other",
})
REQUIRED_FIELDS = frozenset({
    "po_id", "supplier_id", "original_delivery", "revised_delivery",
    "items.receipt_id", "items.quantity", "quote", "quote.capacity",
    "quote.unit_price", "quote.shipping_cost",
})
EXPLICIT_HINTS = (
    "null when", "null if", "null unless", "null for", "or null",
    "(null", "must be null",
)


def _allows_null(field: Any) -> bool:
    if not isinstance(field, dict):
        return False
    typ = field.get("type")
    if typ == "null" or (isinstance(typ, list) and "null" in typ):
        return True
    if isinstance(field.get("anyOf"), list):
        return any(_allows_null(x) for x in field["anyOf"])
    return False


def _flatten(schema: Any, prefix: str = "") -> list[tuple[str, dict]]:
    if not isinstance(schema, dict):
        return []
    answer = []
    props = schema.get("properties")
    if not isinstance(props, dict):
        return answer
    for name, prop in props.items():
        if not isinstance(name, str) or not isinstance(prop, dict):
            continue
        path = f"{prefix}.{name}" if prefix else name
        answer.append((path, prop))
        answer.extend(_flatten(prop, path))
        if isinstance(prop.get("items"), dict):
            answer.extend(_flatten(prop["items"], path))
    return answer


def analyze_extract_nullable_contract(
    studio_config: Any, python_schema: Any,
) -> dict[str, Any]:
    """Report explicit conflicts without guessing Studio nullable support."""
    rows: list[dict[str, Any]] = []
    issues = []
    if (not isinstance(studio_config, dict)
            or studio_config.get("kind") != "studio.workflow-config-draft"
            or not isinstance(studio_config.get("workflowConfig"), dict)
            or not isinstance(python_schema, dict)):
        return {
            "qa_status": "FAIL", "issues": ["INVALID_CONFIG_OR_SCHEMA"],
            "fields": [], "studio_nullable_support_verified": False,
            "live_run_verified": False,
        }
    config = studio_config["workflowConfig"].get("informationExtractConfiguration")
    entries = config.get("schemas") if isinstance(config, dict) else None
    if not isinstance(entries, list):
        return {
            "qa_status": "FAIL", "issues": ["EXTRACT_SCHEMAS_NOT_OBSERVED"],
            "fields": [], "studio_nullable_support_verified": False,
            "live_run_verified": False,
        }
    final = dict(_flatten(python_schema))
    observed_branches = set()
    for entry in entries:
        spec = entry.get("json_schema") if isinstance(entry, dict) else None
        if not isinstance(spec, dict):
            issues.append("INVALID_BRANCH_SCHEMA")
            continue
        branch = spec.get("name")
        extracted = spec.get("schema")
        if branch not in BRANCHES or branch in observed_branches:
            issues.append("UNKNOWN_OR_DUPLICATE_BRANCH")
            continue
        observed_branches.add(branch)
        if not isinstance(extracted, dict):
            issues.append("MISSING_SCHEMA_OBJECT")
            continue
        required = set(extracted.get("required", [])) if isinstance(
            extracted.get("required"), list
        ) else set()
        for path, field in _flatten(extracted):
            description = field.get("description", "")
            text = description.lower() if isinstance(description, str) else ""
            # Generic instruction copied across each field is less specific
            # than "Null if absent"; keep both so Studio can adjudicate.
            specific = any(token in text for token in EXPLICIT_HINTS[:-1])
            generic = "missing values must be null" in text
            if not specific and not generic and path not in REQUIRED_FIELDS:
                continue
            declared = field.get("type")
            accepts_null = _allows_null(field)
            final_field = final.get(path)
            final_declared = final_field.get("type") if final_field else None
            if final_field is None and path.startswith("quote."):
                q = final.get("quote")
                inner = q.get("properties") if isinstance(q, dict) else None
                final_declared = (inner.get(path.split(".", 1)[1], {}).get("type")
                                  if isinstance(inner, dict) else None)
            collision = (specific or generic) and not accepts_null
            row = {
                "extract_branch": branch,
                "field_path": path,
                "declared_type": declared,
                "extract_required_top_level": path.split(".", 1)[0] in required,
                "description": description,
                "null_hint": "EXPLICIT" if specific else
                             "GENERIC" if generic else "NOT_OBSERVED",
                "extract_accepts_json_null": accepts_null,
                "python_normalized_type": final_declared,
                "python_contract_observed": final_field is not None,
                "null_type_conflict": collision,
                "studio_runtime_nullable_supported": "NOT_VERIFIED",
                "studio_change_recommendation": (
                    "PRESERVE_DRAFT_AND_VERIFY_NULLABLE_SCHEMA_IN_STUDIO"
                    if collision else "NO_UNVERIFIED_SCHEMA_CHANGE"
                ),
                "risk": ("MODEL_MAY_INVENT_A_VALUE_OR_REJECT_JSON_NULL"
                         if collision else "REQUIRES_FIELD_LEVEL_EVIDENCE"),
            }
            # The Studio Extract quote is an array, but final normalized
            # quote is an object|null; a conversion boundary is expected.
            if path == "quote":
                row["stage_type_difference_expected"] = (
                    declared == "array" and final_declared == ["object", "null"]
                )
            rows.append(row)
    for branch in sorted(BRANCHES - observed_branches):
        issues.append("MISSING_EXTRACT_BRANCH:" + branch)
    collisions = [row for row in rows if row["null_type_conflict"]]
    return {
        "qa_status": "FAIL_STATIC_CONTRACT" if collisions or issues else "PASS_STATIC_ONLY",
        "issues": issues,
        "fields": rows,
        "conflict_count": len(collisions),
        "observed_branches": sorted(observed_branches),
        "studio_nullable_support_verified": False,
        "published_config_verified": False,
        "live_run_verified": False,
        "no_source_data_modified": True,
        "gold_accuracy_verified": False,
        "known_value_policy": {
            "json_null": "ACCEPT_ONLY_IF_EXPLICITLY_ALLOWED_BY_STAGE_SCHEMA",
            "absent": "NOT_EQUIVALENT_TO_NULL",
            "empty_string": "NOT_EQUIVALENT_TO_NULL",
            "quoted_null": "NOT_EQUIVALENT_TO_NULL",
            "numeric_zero": "PRESERVE_ZERO",
            "string_zero": "NOT_SILENTLY_COERCED",
            "negative_quantity": "BLOCK_IF_UNSAFE",
        },
    }
