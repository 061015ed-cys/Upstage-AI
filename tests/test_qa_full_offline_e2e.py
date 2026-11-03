"""Offline integration *simulation*: operational archived V4 + synthetic QA.

This test connects code paths while deliberately proving no QA Studio live run,
PDF-grounded accuracy, team-2 PR#12 integration or release authorization.
"""
import json
from pathlib import Path

from leadtime_guardian.qa.cross_agent import audit_cross_agent_handoff
from leadtime_guardian.qa.gate import build_integration_gate
from leadtime_guardian.qa.handoff_builder import build_studio_raw_handoff
from leadtime_guardian.qa.replay import verify_c001_replay

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/results/studio_runs/C001_20261030_v4/analysis/studio_original.json"
QA_AGENT = "agt_HdtUJPQPXir9rGKgPWSyZG"
QA_CONFIG = "cfg_X2xXakDtmDTHh2RoqVysvL"


def test_archived_native_to_python_replay_and_synthetic_qa_gate(tmp_path):
    # The archive is a saved operational v4 run, NOT a QA Sandbox execution.
    replay = verify_c001_replay(ROOT)
    assert replay["qa_status"] == "PASS"

    original_native = ARCHIVE.read_bytes()
    documents = json.loads(json.loads(original_native)["content"])["documents"]
    synthetic_report = json.dumps({
        "case_id": "C001",
        "qa_status": "NOT_VERIFIED",
        "checked_document_ids": [d["document_id"] for d in documents],
        "issues": [{"issue_code": "EXTERNAL_SAFETY_NOT_VERIFIED",
                    "scope": "python", "severity": "INFO"}],
        "evidence_status": "PARTIAL",
        "recommended_action": "Independent source and Python verification",
        "workflow_version": "v1",
        "execution_provenance": None,
        "field_checks": [
            {"field": d["document_id"], "status": "SOURCE_NOT_VERIFIED"}
            for d in documents
        ],
    }).encode("utf-8")

    manifest = build_studio_raw_handoff(
        original_native, synthetic_report, case_id="C001",
        agent_id=QA_AGENT, config_id=QA_CONFIG, config_version=1,
        github_sha="a" * 40, execution_kind="ARCHIVED_REPLAY",
    )
    cross = audit_cross_agent_handoff(
        manifest, native_bytes=original_native, report_bytes=synthetic_report,
        expected_agent_id=QA_AGENT, expected_config_id=QA_CONFIG,
        expected_github_sha="a" * 40,
    )
    assert cross["qa_status"] == "BLOCKED"
    assert cross["python_qa_status"] == "NOT_VERIFIED"
    assert cross["release_or_merge_authorized"] is False

    handoff_path, native_path, qa_path = (
        tmp_path / "handoff.json", tmp_path / "native.json", tmp_path / "qa.json"
    )
    handoff_path.write_text(json.dumps(manifest), encoding="utf-8")
    native_path.write_bytes(original_native)
    qa_path.write_bytes(synthetic_report)
    gate = build_integration_gate(
        ROOT, studio_handoff=handoff_path, studio_native=native_path,
        studio_qa_report=qa_path, expected_agent_id=QA_AGENT,
        expected_config_id=QA_CONFIG, expected_github_sha="a" * 40,
    )
    assert gate["local_checks_passed"] is True
    assert gate["checks"]["studio_qa_sandbox_handoff"]["status"] == "BLOCKED"
    assert gate["overall_status"] == "BLOCKED"
    assert gate["release_or_merge_authorized"] is False
    assert gate["studio_runs_started"] == 0
