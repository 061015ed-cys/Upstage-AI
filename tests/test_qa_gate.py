"""An offline PASS never upgrades unverified cloud or human gates."""
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.gate import build_integration_gate

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_gate_check.py"


def run_gate(*args):
    proc = subprocess.run(
        [sys.executable, str(CLI), *args], capture_output=True, text=True,
        cwd=ROOT, check=False, timeout=30,
    )
    assert proc.stderr == "", proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_local_gate_passes_archives_but_blocks_live_release():
    result = build_integration_gate(ROOT)
    assert result["local_checks_passed"] is True
    assert result["overall_status"] == "BLOCKED"
    assert result["release_or_merge_authorized"] is False
    assert result["studio_runs_started"] == 0
    assert result["human_gold_verified"] is False
    for key in ("c001_archive_integrity", "c001_offline_replay", "c001_native_envelope"):
        assert result["checks"][key]["status"] == "PASS"
    assert result["checks"]["new_live_c013"]["status"] == "NOT_RUN"
    assert result["checks"]["new_live_c017"]["status"] == "NOT_RUN"
    assert result["checks"]["team3_source_verified_gold"]["status"] == "BLOCKED"
    assert result["checks"]["measured_extraction_accuracy"]["status"] == "NOT_VERIFIED"


def test_missing_archive_cannot_pass(tmp_path):
    report = build_integration_gate(tmp_path)
    assert report["local_checks_passed"] is False
    assert report["overall_status"] == "FAIL"
    assert report["release_or_merge_authorized"] is False


def test_gate_cli_default_reports_blocked_but_exits_zero_for_local_checks():
    code, result = run_gate("--root", str(ROOT))
    assert code == 0
    assert result["overall_status"] == "BLOCKED"
    assert result["release_or_merge_authorized"] is False


def test_gate_cli_strict_refuses_release_without_external_evidence():
    code, result = run_gate("--root", str(ROOT), "--require-release")
    assert code == 2
    assert result["overall_status"] == "BLOCKED"


def test_gate_cli_fails_local_checks_if_archive_missing(tmp_path):
    code, result = run_gate("--root", str(tmp_path))
    assert code == 1
    assert result["overall_status"] == "FAIL"
