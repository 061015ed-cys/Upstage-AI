"""Preserved v4 Studio draft is NOT today's saved B0 native execution."""
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.extract_null_contract import analyze_extract_nullable_contract

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studio_native/config_v4.export.json"
NORMALIZED = ROOT / "configs/schemas/document_extraction.schema.json"
CLI = ROOT / "scripts/qa_extract_null_contract_check.py"


def test_v4_all_extract_branches_and_explicit_nullable_conflicts():
    config = load_json_strict(CONFIG.read_bytes())
    normal = load_json_strict(NORMALIZED.read_bytes())
    output = analyze_extract_nullable_contract(config, normal)
    assert output["qa_status"] == "FAIL_STATIC_CONTRACT"
    assert len(output["observed_branches"]) == 4
    assert output["conflict_count"] >= 4
    assert output["live_run_verified"] is False
    assert output["studio_nullable_support_verified"] is False
    for branch in output["observed_branches"]:
        rows = [x for x in output["fields"] if x["extract_branch"] == branch]
        po = next(x for x in rows if x["field_path"] == "po_id")
        quote = next(x for x in rows if x["field_path"] == "quote")
        assert po["declared_type"] == "string"
        assert po["null_type_conflict"] is True
        assert po["python_normalized_type"] == ["string", "null"]
        assert quote["declared_type"] == "array"
        assert quote["null_type_conflict"] is True
        assert quote["stage_type_difference_expected"] is True
        q_capacity = next(x for x in rows if x["field_path"] == "quote.capacity")
        assert q_capacity["declared_type"] == "integer"
        assert q_capacity["null_type_conflict"] is True


def test_schema_is_not_modified_by_static_inspection():
    before = CONFIG.read_bytes()
    normal = NORMALIZED.read_bytes()
    analyze_extract_nullable_contract(
        load_json_strict(before), load_json_strict(normal),
    )
    assert before == CONFIG.read_bytes()
    assert normal == NORMALIZED.read_bytes()


def test_invalid_unapproved_config_does_not_claim_null_support():
    out = analyze_extract_nullable_contract(
        {"kind": "studio.workflow-config-draft", "workflowConfig": {}}, {}
    )
    assert out["qa_status"] == "FAIL"
    assert out["live_run_verified"] is False


def test_cli_output_does_not_change_or_publish_studio_config():
    proc = subprocess.run([
        sys.executable, str(CLI), "--config", str(CONFIG),
    ], cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    output = json.loads(proc.stdout)
    assert proc.returncode == 2, proc.stderr
    assert output["qa_status"] == "FAIL_STATIC_CONTRACT"
    assert output["published_config_verified"] is False
    assert output["no_source_data_modified"] is True
