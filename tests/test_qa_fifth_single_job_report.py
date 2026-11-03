"""The new C001 single Job is reported, not independently Native verified."""
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.studio_batch import audit_studio_case_batch

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/observations/B0_C001_NCik_20261101_REPORTED_SINGLE_JOB.json"
CLI = ROOT / "scripts/qa_studio_batch_check.py"


def test_new_ncik_studio_report_is_single_job_but_raw_not_authenticated():
    raw = load_json_strict(REPORT.read_bytes())
    assert raw["jobs"][0]["job_id"] == "job_NCik8shwrgM93PDnNNYukT"
    result = audit_studio_case_batch(
        raw, expected_case_id="C001",
        expected_job_id="job_NCik8shwrgM93PDnNNYukT",
        expected_config_id="cfg_X2xXakDtmDTHh2RoqVysvL",
        expected_config_version=1,
    )
    assert result["qa_status"] == "BLOCKED"
    assert result["single_case_grouping_status"] == (
        "REPORTED_SINGLE_JOB_UNAUTHENTICATED"
    )
    assert "SINGLE_JOB_SOURCE_FILE_IDS_NOT_OBSERVED" in {
        x["issue_code"] for x in result["issues"]
    }
    assert result["experiment_comparison_allowed"] is False
    assert result["native_bytes_authenticated"] is False


def test_new_ncik_claim_cannot_rebind_archive_job():
    output = audit_studio_case_batch(
        load_json_strict(REPORT.read_bytes()), expected_case_id="C001",
        expected_job_id="job_gPmEYKzuJdBA6BmKhVnujs",
    )
    assert output["qa_status"] == "FAIL"
    assert "BATCH_EXPECTED_JOB_ID_MISMATCH" in {
        x["issue_code"] for x in output["issues"]
    }


def test_report_cli_yields_blocked_not_pass():
    proc = subprocess.run([
        sys.executable, str(CLI), "--report", str(REPORT),
        "--case-id", "C001", "--expected-job-id", "job_NCik8shwrgM93PDnNNYukT",
    ], cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    result = json.loads(proc.stdout)
    assert proc.returncode == 2, proc.stderr
    assert result["qa_status"] == "BLOCKED"
    assert result["studio_qa_verdict"] == "UNKNOWN"
