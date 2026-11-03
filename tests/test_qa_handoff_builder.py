"""Synthetic examples using archived operational V4 bytes, not new Studio QA."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from leadtime_guardian.qa.cross_agent import audit_cross_agent_handoff
from leadtime_guardian.qa.handoff_builder import build_studio_raw_handoff

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/results/studio_runs/C001_20261030_v4/analysis/studio_original.json"
CLI = ROOT / "scripts/qa_prepare_studio_raw_handoff.py"
AGENT = "agt_HdtUJPQPXir9rGKgPWSyZG"
CONFIG = "cfg_X2xXakDtmDTHh2RoqVysvL"
SHA = "a" * 40


def inputs():
    native = ARCHIVE.read_bytes()
    report = json.dumps({
        "case_id": "C001",
        "qa_status": "NOT_VERIFIED",
        "checked_document_ids": ["PO-DOC", "NOTICE-DOC", "QUOTE-DOC"],
        "issues": [],
        "evidence_status": "PARTIAL",
        "recommended_action": "Verify source",
        "workflow_version": "v1",
        "execution_provenance": None,
        "field_checks": [{"status": "SOURCE_NOT_VERIFIED", "field": "po_id"}],
    }).encode()
    return native, report


def build(native=None, report=None, **changes):
    supplied_native, supplied_report = inputs()
    options = {"case_id": "C001", "agent_id": AGENT, "config_id": CONFIG,
               "config_version": 1, "github_sha": SHA}
    options.update(changes)
    return build_studio_raw_handoff(
        supplied_native if native is None else native,
        supplied_report if report is None else report, **options,
    )


def test_builder_explicit_contract_with_archived_replay():
    manifest = build(execution_kind="ARCHIVED_REPLAY")
    native, report = inputs()
    response = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=report,
        expected_agent_id=AGENT, expected_config_id=CONFIG,
    )
    assert response["qa_status"] == "BLOCKED"
    assert manifest["verdict"]["python_qa_status"] == "NOT_VERIFIED"
    assert response["studio_live_execution_authenticated"] is False


@pytest.mark.parametrize(("field", "value"), [
    ("agent_id", "agt_random"),
    ("config_id", "cfg_fake"),
    ("config_version", 2),
    ("github_sha", "bad"),
    ("case_id", "C013"),
    ("execution_kind", "SDK_HTTP_MOCK"),
])
def test_builder_rejects_unapproved_or_mismatched_identifier(field, value):
    with pytest.raises(ValueError):
        build(**{field: value})


def test_builder_preserves_exact_raw_sha():
    native, report = inputs()
    manifest = build(native, report)
    import hashlib

    assert manifest["studio"]["native_sha256"] == hashlib.sha256(native).hexdigest()
    assert manifest["studio"]["qa_report_sha256"] == hashlib.sha256(report).hexdigest()


def test_builder_rejects_duplicate_json_keys():
    native, _ = inputs()
    tampered = b'{"case_id":"C001","case_id":"C013"}'
    with pytest.raises(ValueError):
        build(native, tampered)


def test_builder_rejects_unbound_document_ids():
    native, report = inputs()
    data = json.loads(report)
    data["checked_document_ids"] = ["WRONG"]
    with pytest.raises(ValueError):
        build(native, json.dumps(data).encode())


def test_builder_cli_writes_a_blocked_not_approved_manifest(tmp_path):
    native, report = inputs()
    np, rp, mp = (tmp_path / x for x in ("native.json", "qa.json", "manifest.json"))
    np.write_bytes(native)
    rp.write_bytes(report)
    process = subprocess.run([
        sys.executable, str(CLI), "--native", str(np), "--qa-report", str(rp),
        "--case-id", "C001", "--agent-id", AGENT, "--config-id", CONFIG,
        "--config-version", "1", "--github-sha", SHA,
        "--execution-kind", "ARCHIVED_REPLAY", "--manifest-output", str(mp),
    ], check=False, capture_output=True, text=True, timeout=30, cwd=ROOT)
    assert process.returncode == 2, process.stderr
    output = json.loads(process.stdout)
    assert output["qa_status"] == "BLOCKED"
    assert output["release_or_merge_authorized"] is False
    assert json.loads(mp.read_text())["verdict"]["python_qa_status"] == "NOT_VERIFIED"


def test_builder_cli_no_manifest_when_raw_report_invalid(tmp_path):
    native, report = inputs()
    np, rp, mp = (tmp_path / x for x in ("native.json", "qa.json", "manifest.json"))
    np.write_bytes(native)
    rp.write_bytes(report.replace(b"NOT_VERIFIED", b"ALLEGED_PASS"))
    process = subprocess.run([
        sys.executable, str(CLI), "--native", str(np), "--qa-report", str(rp),
        "--case-id", "C001", "--agent-id", AGENT, "--config-id", CONFIG,
        "--config-version", "1", "--github-sha", SHA,
        "--manifest-output", str(mp),
    ], check=False, capture_output=True, text=True, timeout=30, cwd=ROOT)
    assert process.returncode == 1
    assert not mp.exists()
