"""Optional Stage trace must not bypass existing Python V6 + QA E2E safety."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_combined_e2e_check.py"
OPERATING = ROOT / "data/results/studio_runs/C001_20261030_v4/instruct_original.json"
BASE = ROOT / "data/cases/SYN-C001/trusted_base_case.json"
SCHEMA = ROOT / "configs/schemas/document_extraction.schema.json"


def run(manifest):
    op = load_json_strict(OPERATING.read_bytes())
    job = op["metadata"]["job_execution_id"]
    args = [sys.executable, str(CLI),
            "--operational-native", str(OPERATING),
            "--trusted-base", str(BASE), "--schema", str(SCHEMA),
            "--operational-job-id", job, "--case-id", "C001",
            "--github-sha", "a" * 40]
    if manifest is not None:
        args.extend(("--stage-intake-manifest", str(manifest)))
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                          check=False, timeout=30)
    return proc, json.loads(proc.stdout)


def create_manifest(tmp_path, *, job_override=None, mutate=False):
    op = load_json_strict(OPERATING.read_bytes())
    job = op["metadata"]["job_execution_id"]
    docs = load_json_strict(op["content"])["documents"]
    if mutate:
        docs[0]["items"][0]["quantity"] = 999
    raw = {
        "case_id": "C001", "job_id": job,
        "step_run_id": "synthetic_normalize_step", "documents": docs,
    }
    raw_bytes = json.dumps(raw).encode()
    (tmp_path / "normalized.json").write_bytes(raw_bytes)
    manifest = {
        "schema_version": "leadtime-stage-intake/v1",
        "case_id": "C001",
        "operational_job_id": job_override or job,
        "config_id": "cfg_SYNTHETIC", "config_version": 1,
        "stages": {
            "NormalizeDocuments": {
                "path": "normalized.json",
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "job_id": job, "case_id": "C001",
                "config_id": "cfg_SYNTHETIC", "config_version": 1,
                "step_run_id": "synthetic_normalize_step",
            },
        },
    }
    path = tmp_path / "stage_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_archived_python_still_blocks_when_stage_manifest_is_incomplete(tmp_path):
    path = create_manifest(tmp_path)
    proc, out = run(path)
    assert proc.returncode == 2, proc.stderr
    assert out["stage_intake_status"] == "BLOCKED"
    assert out["stage_intake"]["stages"]["NormalizeDocuments"]["document_count"] == 3
    assert out["python_safety_status"] == "PASS_LOCAL"
    assert out["status"] == "BLOCKED"
    assert out["actual_studio_e2e_status"] == "NOT_VERIFIED"
    assert out["release_or_merge_authorized"] is False


def test_raw_normalize_diff_from_archived_native_fails(tmp_path):
    path = create_manifest(tmp_path, mutate=True)
    proc, out = run(path)
    assert proc.returncode == 1, proc.stderr
    assert out["status"] == "FAIL"
    assert "NATIVE_AND_NORMALIZE_CONTENT_MISMATCH" in {
        x["issue_code"] for x in out["issues"]
    }


def test_cross_job_stage_manifest_cannot_bind_existing_operational_job(tmp_path):
    path = create_manifest(tmp_path, job_override="job_OTHER")
    proc, out = run(path)
    assert proc.returncode == 1, proc.stderr
    assert out["status"] == "FAIL"


def test_original_combined_cli_keeps_backward_compatibility():
    proc, out = run(None)
    assert proc.returncode == 2, proc.stderr
    assert out["python_safety_status"] == "PASS_LOCAL"
    assert out["status"] == "BLOCKED"
    assert "stage_intake_status" not in out



def test_bad_stage_sha_is_rejected_before_python_safety_execution(tmp_path):
    path = create_manifest(tmp_path)
    meta = json.loads(path.read_text())
    meta["stages"]["NormalizeDocuments"]["sha256"] = "a" * 64
    path.write_text(json.dumps(meta))
    proc, out = run(path)
    assert proc.returncode == 1
    assert out["status"] == "FAIL"
    assert out["python_safety_status"] == "NOT_RUN"
    assert "python_summary" not in out
    assert out["actual_studio_e2e_status"] == "NOT_VERIFIED"
    assert out["release_or_merge_authorized"] is False


def test_stage_job_mismatch_is_rejected_before_python_execution(tmp_path):
    path = create_manifest(tmp_path, job_override="job_WRONG")
    proc, out = run(path)
    assert proc.returncode == 1
    assert out["python_safety_status"] == "NOT_RUN"
    assert "python_summary" not in out


def test_normalize_same_document_values_different_array_order_stays_blocked(tmp_path):
    path = create_manifest(tmp_path)
    meta = json.loads(path.read_text())
    source = tmp_path / "normalized.json"
    parsed = json.loads(source.read_text())
    parsed["documents"].reverse()
    raw = json.dumps(parsed).encode()
    source.write_bytes(raw)
    meta["stages"]["NormalizeDocuments"]["sha256"] = hashlib.sha256(raw).hexdigest()
    path.write_text(json.dumps(meta))
    proc, out = run(path)
    assert proc.returncode == 2, proc.stderr
    assert out["status"] == "BLOCKED"
    assert out["python_safety_status"] == "PASS_LOCAL"
    assert out["stage_intake_status"] == "BLOCKED"
    assert out["release_or_merge_authorized"] is False
