"""Offline handoff preparation must use real matching exports, never guessed fields.

All QA Sandbox IDs in this test are synthetic mappings over historical C001
operational bytes; this is NOT a fresh Upstage QA Sandbox execution.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.cross_agent import audit_cross_agent_handoff
from leadtime_guardian.qa.evidence import audit_export_binding

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "data/results/studio_runs/C001_20261030_v4"
PREP = ROOT / "scripts/qa_prepare_handoff.py"
SHA = "b" * 40
SANDBOX = "agt_GhP9GywhbcDWquFqWTsmtq"


def prepare_files(tmp_path):
    native = (OLD / "analysis/studio_original.json").read_bytes()
    original = json.loads(native)
    record = {
        "agent_id": SANDBOX,
        "config_id": "cfg_SYNTHETIC_QA_ONLY",
        "config_version": 4,
        "job_id": original["metadata"]["job_execution_id"],
        "native_step_run_id": original["metadata"]["step_run_id"],
        "execution_mode": "live_studio_web",
        "studio_execution_completed": True,
    }
    config = {
        "kind": "studio.workflow-config-draft",
        "exportedFrom": {"workflowId": SANDBOX, "configId": "cfg_SYNTHETIC_QA_ONLY", "configVer": 4},
        "workflowConfig": {"instructConfiguration": {"customName": "IndependentQA"}},
    }
    report = {
        "document_qa_status": "PASS",
        "python_qa_status": "NOT_VERIFIED",
        "issues": [
            {"code": "EXTERNAL_SAFETY_NOT_VERIFIED", "severity": "INFO", "scope": "python"}
        ],
    }
    paths = [tmp_path / name for name in ("config.json", "record.json", "native.json", "report.json")]
    for p, obj in zip(paths, (config, record, native, report), strict=True):
        p.write_bytes(obj if isinstance(obj, bytes) else json.dumps(obj).encode())
    return paths


def call(paths, output, *, kind="ARCHIVED_STUDIO"):
    config, record, native, report = paths
    cmd = [
        sys.executable, str(PREP), "--config-export", str(config),
        "--execution-record", str(record), "--native", str(native),
        "--qa-report", str(report), "--github-sha", SHA,
        "--execution-kind", kind, "--output", str(output),
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    assert result.stderr == "", result.stderr
    return result.returncode, json.loads(result.stdout)


def test_can_prepare_reviewed_structured_handoff_from_matching_bytes(tmp_path):
    paths = prepare_files(tmp_path)
    out = tmp_path / "manifest.json"
    rc, result = call(paths, out)
    assert rc == 0
    assert result["manifest_written"] is True
    assert result["qa_status"] == "BLOCKED"
    assert result["studio_authenticated"] is False
    manifest = load_json_strict(out.read_bytes())
    native_bytes = paths[2].read_bytes()
    report_bytes = paths[3].read_bytes()
    assert manifest["studio"]["native_sha256"] == hashlib.sha256(native_bytes).hexdigest()
    assert manifest["studio"]["qa_report_sha256"] == hashlib.sha256(report_bytes).hexdigest()
    assert audit_export_binding(manifest, load_json_strict(paths[0].read_bytes()),
                                load_json_strict(paths[1].read_bytes()))["qa_status"] == "PASS"
    assert audit_cross_agent_handoff(manifest, native_bytes=native_bytes,
                                     report_bytes=report_bytes)["qa_status"] == "BLOCKED"


def test_reject_unmapped_raw_studio_report(tmp_path):
    paths = prepare_files(tmp_path)
    paths[3].write_text(json.dumps({"status": "PASS", "issues": []}))
    out = tmp_path / "manifest.json"
    rc, result = call(paths, out)
    assert rc == 1
    assert result["issue_code"] == "QA_REPORT_MAPPING_REVIEW_REQUIRED"
    assert not out.exists()


def test_reject_operational_config_not_qa_sandbox(tmp_path):
    paths = prepare_files(tmp_path)
    cfg = load_json_strict(paths[0].read_bytes())
    cfg["exportedFrom"]["workflowId"] = "agt_bXRXFSAgFmBayPjZF7VqRQ"
    paths[0].write_text(json.dumps(cfg))
    rc, result = call(paths, tmp_path / "manifest.json")
    assert rc == 1
    assert "UNEXPECTED_QA_SANDBOX_AGENT" in {x["issue_code"] for x in result["binding_issues"]}


def test_reject_mismatched_config_version(tmp_path):
    paths = prepare_files(tmp_path)
    cfg = load_json_strict(paths[0].read_bytes())
    cfg["exportedFrom"]["configVer"] = 5
    paths[0].write_text(json.dumps(cfg))
    rc, result = call(paths, tmp_path / "manifest.json")
    assert rc == 1
    assert "RUN_CONFIG_VERSION_MISMATCH" in {x["issue_code"] for x in result["binding_issues"]}


def test_reject_run_id_mismatch_in_native(tmp_path):
    paths = prepare_files(tmp_path)
    record = load_json_strict(paths[1].read_bytes())
    record["job_id"] = "job_unrelated"
    paths[1].write_text(json.dumps(record))
    rc, result = call(paths, tmp_path / "manifest.json")
    assert rc == 1
    assert "NATIVE_CROSS_JOB_MISMATCH" in {x["issue_code"] for x in result["contract_issues"]}


def test_prevent_old_operational_job_claimed_new_live(tmp_path):
    paths = prepare_files(tmp_path)
    rc, result = call(paths, tmp_path / "manifest.json", kind="NEW_LIVE_STUDIO")
    assert rc == 1
    assert "ARCHIVED_JOB_REUSED_AS_NEW" in {x["issue_code"] for x in result["contract_issues"]}


def test_never_overwrite_existing_manifest(tmp_path):
    paths = prepare_files(tmp_path)
    output = tmp_path / "manifest.json"
    output.write_text("preserve")
    rc, result = call(paths, output)
    assert rc == 1
    assert result["issue_code"] == "MANIFEST_OUTPUT_EXISTS"
    assert output.read_text() == "preserve"


def test_reject_incomplete_live_execution_record(tmp_path):
    paths = prepare_files(tmp_path)
    rec = load_json_strict(paths[1].read_bytes())
    rec["studio_execution_completed"] = False
    paths[1].write_text(json.dumps(rec))
    rc, result = call(paths, tmp_path / "manifest.json", kind="NEW_LIVE_STUDIO")
    assert rc == 1
    assert "RUN_NOT_COMPLETED" in {x["issue_code"] for x in result["binding_issues"]}


def test_bad_export_structure_returns_fail_not_exception():
    assert audit_export_binding({}, [], None)["qa_status"] == "FAIL"
    assert audit_export_binding(None, {}, {})["release_or_merge_authorized"] is False
