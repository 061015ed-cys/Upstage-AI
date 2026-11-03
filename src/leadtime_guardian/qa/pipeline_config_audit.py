"""Static Studio workflow draft audit; no cloud access or execution attestations."""
from __future__ import annotations

from collections import Counter
from itertools import pairwise
from typing import Any

CLASSIFICATIONS = frozenset({"purchase_order", "delivery_notice", "quotation", "other"})
REQUIRED_FLOW = ("parse", "classify", "extract", "merge", "instruct")


def audit_studio_config_draft(config: Any) -> dict[str, Any]:
    """Check graph contract, dispatch and simple null-vs-type contradictions.

    A workflow-config-draft can be audited statically, but this never verifies
    published config, AI extraction accuracy, per-branch runtimes or live Jobs.
    """
    issues: list[dict[str, str]] = []

    def add(code: str, field: str, severity: str = "ERROR") -> None:
        issues.append({"issue_code": code, "field": field, "severity": severity})

    if not isinstance(config, dict) or not isinstance(config.get("workflowConfig"), dict):
        return {"qa_status": "FAIL", "issues": [
            {"issue_code": "INVALID_WORKFLOW_CONFIG", "field": "$",
             "severity": "ERROR"}], "live_run_verified": False}
    if config.get("kind") != "studio.workflow-config-draft":
        add("NOT_RECOGNIZED_DRAFT_KIND", "kind")
    workflow = config["workflowConfig"]
    p = workflow.get("documentParseConfiguration")
    if not isinstance(p, dict):
        add("MISSING_PARSE_CONFIG", "documentParseConfiguration")
    else:
        if p.get("mode") != "standard" or p.get("ocrMode") != "force":
            add("PARSE_MODE_DIFFERS_FROM_BASELINE", "documentParseConfiguration",
                "WARNING")
    classify = workflow.get("documentClassifyConfiguration")
    if not isinstance(classify, dict):
        add("MISSING_CLASSIFY_CONFIG", "documentClassifyConfiguration")
    elif not (classify.get("split") is True and
              isinstance(classify.get("splitCriteria"), list) and
              any(isinstance(x, dict) and x.get("criterion") == "file_boundary"
                  for x in classify["splitCriteria"])):
        add("CLASSIFY_FILE_BOUNDARY_NOT_ENFORCED", "documentClassifyConfiguration")
    extract = workflow.get("informationExtractConfiguration")
    schema_names: set[str] = set()
    if not isinstance(extract, dict) or not isinstance(extract.get("schemas"), list):
        add("EXTRACT_SCHEMAS_MISSING", "informationExtractConfiguration.schemas")
    else:
        for i, entry in enumerate(extract["schemas"]):
            if not isinstance(entry, dict):
                add("INVALID_EXTRACT_BRANCH", f"informationExtractConfiguration.schemas[{i}]")
                continue
            definition = entry.get("json_schema")
            if not isinstance(definition, dict):
                add("INVALID_EXTRACT_SCHEMA", f"informationExtractConfiguration.schemas[{i}]")
                continue
            name = definition.get("name")
            if not isinstance(name, str) or not name:
                add("MISSING_SCHEMA_NAME", f"schemas[{i}]")
                continue
            schema_names.add(name)
            schema = definition.get("schema")
            if not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict):
                add("INVALID_SCHEMA_PROPERTIES", f"schemas[{i}]")
                continue
            for field, value in schema["properties"].items():
                if not isinstance(value, dict):
                    continue
                description = value.get("description", "")
                # Only report text explicitly instructing null for this field;
                # generic instructions copied to every property are advisory.
                own = f"{field} must be null"
                null_explicit = (isinstance(description, str)
                                 and ("Null when" in description
                                      or "Null if" in description
                                      or own in description))
                declared = value.get("type")
                accepts_null = declared == "null" or (
                    isinstance(declared, list) and "null" in declared
                ) or (isinstance(value.get("anyOf"), list)
                      and any(x.get("type") == "null"
                              for x in value["anyOf"] if isinstance(x, dict)))
                if null_explicit and not accepts_null:
                    add("EXTRACT_NULL_SCHEMA_CONFLICT",
                        f"informationExtractConfiguration.schemas[{i}]."
                        f"{name}.{field}")
    edges = workflow.get("pipelineEdges")
    if not isinstance(edges, list) or not edges:
        add("MISSING_PIPELINE_EDGES", "pipelineEdges")
    else:
        graph: list[tuple[str, str]] = []
        routes: list[str] = []
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                add("INVALID_PIPELINE_EDGE", f"pipelineEdges[{i}]")
                continue
            src, target = edge.get("source"), edge.get("target")
            if not isinstance(src, dict) or not isinstance(target, dict):
                add("INVALID_PIPELINE_NODE_REF", f"pipelineEdges[{i}]")
                continue
            a, b = src.get("nodeType"), target.get("nodeType")
            if not isinstance(a, str) or not isinstance(b, str):
                add("INVALID_PIPELINE_NODE_TYPE", f"pipelineEdges[{i}]")
                continue
            graph.append((a, b))
            if a == "classify" and b == "extract":
                route = edge.get("condition")
                cond = route.get("conditionName") if isinstance(route, dict) else None
                if not isinstance(cond, str) or cond not in CLASSIFICATIONS:
                    add("INVALID_CLASSIFY_ROUTE", f"pipelineEdges[{i}].condition")
                else:
                    routes.append(cond)
                    expected_name = "Extract_" + cond
                    if target.get("name") != expected_name or expected_name not in schema_names:
                        add("CLASSIFY_EXTRACT_TARGET_MISMATCH",
                            f"pipelineEdges[{i}].target")
        if set(routes) != CLASSIFICATIONS or any(v != 1 for v in Counter(routes).values()):
            add("CLASSIFY_ROUTE_COVERAGE_MISMATCH", "pipelineEdges")
        for src, dst in pairwise(REQUIRED_FLOW):
            if (src, dst) not in graph:
                add("MISSING_REQUIRED_GRAPH_TRANSITION", f"{src}->{dst}")
    return {
        "qa_status": "FAIL" if any(x["severity"] == "ERROR" for x in issues) else "PASS",
        "issues": issues,
        "evidence_kind": "STATIC_DRAFT_ONLY",
        "live_run_verified": False,
        "published_config_verified": False,
        "extraction_accuracy_verified": False,
    }
