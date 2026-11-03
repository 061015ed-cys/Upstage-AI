"""Static export contract checks: archived draft is not a live Studio run."""
import json
from copy import deepcopy
from pathlib import Path

from leadtime_guardian.qa.pipeline_config_audit import audit_studio_config_draft

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "configs/studio_native/config_v4.export.json"


def original():
    return json.loads(DRAFT.read_text(encoding="utf-8"))


def codes(r):
    return {i["issue_code"] for i in r["issues"]}


def test_actual_archived_config_detects_explicit_nullable_schema_conflict():
    result = audit_studio_config_draft(original())
    assert result["evidence_kind"] == "STATIC_DRAFT_ONLY"
    assert result["published_config_verified"] is False
    assert result["live_run_verified"] is False
    assert "EXTRACT_NULL_SCHEMA_CONFLICT" in codes(result)
    assert "CLASSIFY_ROUTE_COVERAGE_MISMATCH" not in codes(result)


def test_mismatched_condition_target_fails():
    raw = original()
    edges = raw["workflowConfig"]["pipelineEdges"]
    edge = next(x for x in edges if x.get("condition", {}).get("conditionName")
                == "quotation")
    edge["target"]["name"] = "Extract_delivery_notice"
    assert "CLASSIFY_EXTRACT_TARGET_MISMATCH" in codes(audit_studio_config_draft(raw))


def test_missing_classification_route_fails():
    raw = original()
    raw["workflowConfig"]["pipelineEdges"] = [
        x for x in raw["workflowConfig"]["pipelineEdges"]
        if x.get("condition", {}).get("conditionName") != "other"
    ]
    assert "CLASSIFY_ROUTE_COVERAGE_MISMATCH" in codes(audit_studio_config_draft(raw))


def test_null_split_criteria_fails_without_exception():
    raw = original()
    raw["workflowConfig"]["documentClassifyConfiguration"]["splitCriteria"] = None
    assert "CLASSIFY_FILE_BOUNDARY_NOT_ENFORCED" in codes(
        audit_studio_config_draft(raw)
    )


def test_draft_is_never_marked_live():
    raw = deepcopy(original())
    raw["kind"] = "malformed"
    result = audit_studio_config_draft(raw)
    assert result["qa_status"] == "FAIL"
    assert result["live_run_verified"] is False
