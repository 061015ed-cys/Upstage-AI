"""Cross-agent CLI and optional integration-gate validation of actual file bytes.

All handoffs in this test are synthetic; historical C001 native bytes are reused
only to test structural binding and MUST NOT be described as new Studio runs.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from leadtime_guardian.qa.gate import build_integration_gate

ROOT = Path(__file__).resolve().parents[1]
ARCHIVED_NATIVE = ROOT / "data/results/studio_runs/C001_20261030_v4/analysis/studio_original.json"
CLI = ROOT / "scripts/qa_cross_agent_check.py"
GATE_CLI = ROOT / "scripts/qa_gate_check.py"


def fixture(tmp_path):
    native = ARCHIVED_NATIVE.read_bytes()
    parsed = json.loads(native)
    report = json.dumps({"document_qa_status": "PASS",
                         "python_qa_status": "NOT_VERIFIED"}).encode()
    manifest = {
        "protocol_version": "leadtime-cross-agent/v1",
        "producer": "UPSTAGE_QA_SANDBOX",
        "studio": {
            "agent_id": "agt_GhP9GywhbcDWquFqWTsmtq",
            "config_id": "cfg_synthetic_unverified",
            "config_version": 4,
            "job_id": parsed["metadata"]["job_execution_id"],
            "step_run_id": parsed["metadata"]["step_run_id"],
            "execution_kind": "ARCHIVED_STUDIO",
            "input_file_ids": [r["file_id"] for r in parsed["metadata"]["source_files"]],
            "native_sha256": hashlib.sha256(native).hexdigest(),
            "qa_report_sha256": hashlib.sha256(report).hexdigest(),
        },
        "verdict": {"document_qa_status": "PASS", "python_qa_status": "NOT_VERIFIED",
                    "issues": [{"code": "EXTERNAL_SAFETY_NOT_VERIFIED",
                                "scope": "python", "severity": "INFO"}]},
        "github": {"repository": "dohun3540-crypto/leadtime-guardian-agent.copy",
                   "head_sha": "a" * 40,
                   "contract_version": "leadtime-cross-agent/v1"},
    }
    paths = [tmp_path / name for name in ("handoff.json", "native.json", "qa-report.json")]
    for path, data in zip(paths, (json.dumps(manifest).encode(), native, report), strict=True):
        path.write_bytes(data)
    return paths, manifest


def run_script(script, *args):
    p = subprocess.run([sys.executable, str(script), *map(str, args)],
                       capture_output=True, text=True, cwd=ROOT, check=False, timeout=30)
    assert p.stderr == "", p.stderr
    return p.returncode, json.loads(p.stdout)


def test_cross_agent_cli_preserves_document_pass_python_blocked(tmp_path):
    (manifest, native, report), _ = fixture(tmp_path)
    rc, result = run_script(CLI, "--manifest", manifest, "--native", native, "--qa-report", report)
    assert rc == 0
    assert result["qa_status"] == "BLOCKED"
    assert result["document_qa_status"] == "PASS"


def test_cross_agent_strict_requires_more_than_a_document_pass(tmp_path):
    (manifest, native, report), _ = fixture(tmp_path)
    rc, result = run_script(CLI, "--manifest", manifest, "--native", native,
                            "--qa-report", report, "--require-contract")
    assert rc == 2
    assert result["release_or_merge_authorized"] is False


def test_cross_agent_missing_manifest_is_json_failure(tmp_path):
    rc, result = run_script(CLI, "--manifest", tmp_path / "missing.json")
    assert rc == 1
    assert result["qa_status"] == "FAIL"


def test_cross_agent_wrong_expected_config_fails(tmp_path):
    (manifest, native, report), _ = fixture(tmp_path)
    rc, result = run_script(CLI, "--manifest", manifest, "--native", native,
                            "--qa-report", report, "--expected-config-id", "cfg_actual_other")
    assert rc == 1
    assert "CONFIG_ID_MISMATCH" in {x["issue_code"] for x in result["issues"]}


def test_gate_with_valid_manifest_remains_release_blocked(tmp_path):
    (manifest, native, report), _ = fixture(tmp_path)
    result = build_integration_gate(ROOT, studio_handoff=manifest, studio_native=native,
                                    studio_qa_report=report)
    assert result["local_checks_passed"] is True
    assert result["overall_status"] == "BLOCKED"
    assert result["release_or_merge_authorized"] is False
    assert result["checks"]["studio_qa_sandbox_handoff"]["status"] == "BLOCKED"


def test_gate_rejects_mixed_run_manifest(tmp_path):
    (manifest_path, native, report), manifest = fixture(tmp_path)
    manifest["studio"]["job_id"] = "job_another"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = build_integration_gate(ROOT, studio_handoff=manifest_path,
                                    studio_native=native, studio_qa_report=report)
    assert result["local_checks_passed"] is False
    assert result["overall_status"] == "FAIL"
    assert result["checks"]["studio_qa_sandbox_handoff"]["status"] == "FAIL"


def test_gate_cli_optional_handoff_stays_blocked(tmp_path):
    (manifest, native, report), _ = fixture(tmp_path)
    rc, output = run_script(GATE_CLI, "--root", ROOT, "--studio-handoff", manifest,
                            "--studio-native", native, "--studio-qa-report", report)
    assert rc == 0
    assert output["overall_status"] == "BLOCKED"
    rc, output = run_script(GATE_CLI, "--root", ROOT, "--studio-handoff", manifest,
                            "--studio-native", native, "--studio-qa-report", report,
                            "--require-release")
    assert rc == 2
    assert output["release_or_merge_authorized"] is False


def test_cli_selects_pinned_copy_without_allowing_original_by_default(tmp_path):
    (manifest_file, native, report), manifest = fixture(tmp_path)
    manifest["studio"].update({
        "agent_id": "agt_HdtUJPQPXir9rGKgPWSyZG",
        "config_id": "cfg_X2xXakDtmDTHh2RoqVysvL",
        "config_version": 1,
    })
    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    rc, result = run_script(CLI, "--manifest", manifest_file, "--native", native,
                            "--qa-report", report)
    assert rc == 1
    assert "SANDBOX_AGENT_ID_MISMATCH" in {
        x["issue_code"] for x in result["issues"]
    }
    rc, result = run_script(
        CLI, "--manifest", manifest_file, "--native", native,
        "--qa-report", report,
        "--expected-agent-id", "agt_HdtUJPQPXir9rGKgPWSyZG",
        "--expected-config-id", "cfg_X2xXakDtmDTHh2RoqVysvL",
    )
    assert rc == 0
    assert result["qa_status"] == "BLOCKED"
    assert result["release_or_merge_authorized"] is False


def test_gate_cli_selects_pinned_copy_but_never_releases(tmp_path):
    (manifest_file, native, report), manifest = fixture(tmp_path)
    manifest["studio"].update({
        "agent_id": "agt_HdtUJPQPXir9rGKgPWSyZG",
        "config_id": "cfg_X2xXakDtmDTHh2RoqVysvL",
        "config_version": 1,
    })
    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    rc, result = run_script(
        GATE_CLI, "--root", ROOT, "--studio-handoff", manifest_file,
        "--studio-native", native, "--studio-qa-report", report,
        "--expected-agent-id", "agt_HdtUJPQPXir9rGKgPWSyZG",
        "--require-release",
    )
    assert rc == 2
    assert result["overall_status"] == "BLOCKED"
    assert result["release_or_merge_authorized"] is False
