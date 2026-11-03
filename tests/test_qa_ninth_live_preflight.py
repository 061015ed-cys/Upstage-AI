"""A NEW_LIVE label without original evidence must never invoke Python V6."""
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_combined_e2e_check.py"
ARCHIVE = ROOT / "data/results/studio_runs/C001_20261030_v4/instruct_original.json"
BASE = ROOT / "data/cases/SYN-C001/trusted_base_case.json"


def invoke(*extra):
    job_id = load_json_strict(ARCHIVE.read_bytes())["metadata"]["job_execution_id"]
    proc = subprocess.run(
        [sys.executable, str(CLI),
         "--operational-native", str(ARCHIVE),
         "--trusted-base", str(BASE),
         "--operational-job-id", job_id,
         "--case-id", "C001", "--github-sha", "a" * 40,
         *extra],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=30,
    )
    return proc, json.loads(proc.stdout)


def test_new_live_without_stage_manifest_never_executes_python():
    proc, result = invoke("--execution-kind", "NEW_LIVE_STUDIO")
    assert proc.returncode == 2, proc.stderr
    assert result["status"] == "BLOCKED"
    assert result["python_safety_status"] == "NOT_RUN"
    assert "STAGE_INTAKE_MANIFEST" in result["missing_inputs"]
    assert "python_summary" not in result
    assert result["actual_studio_e2e_status"] == "NOT_VERIFIED"
    assert result["release_or_merge_authorized"] is False


def test_new_live_partial_receipt_set_is_not_silently_accepted():
    proc, result = invoke(
        "--execution-kind", "NEW_LIVE_STUDIO",
        "--qa-native", str(ARCHIVE),
        "--qa-report", str(ARCHIVE),
    )
    assert proc.returncode == 2
    assert result["status"] == "BLOCKED"
    assert "TEAM2_PROVENANCE" in result["missing_inputs"]
    assert "OPERATIONAL_PDF_RECEIPT" in result["missing_inputs"]
    assert result["python_safety_status"] == "NOT_RUN"


def test_existing_archived_replay_cli_is_backward_compatible():
    proc, result = invoke()
    assert proc.returncode == 2, proc.stderr
    assert result["status"] == "BLOCKED"
    assert result["python_safety_status"] == "PASS_LOCAL"
    assert result["release_or_merge_authorized"] is False
