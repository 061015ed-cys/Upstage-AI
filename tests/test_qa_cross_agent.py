"""Synthetic cross-agent manifests; archived C001 bytes are not new Sandbox runs."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.qa.cross_agent import (
    HANDOFF_VERSION,
    SANDBOX_AGENT_ID,
    SANDBOX_COPY_AGENT_ID,
    SANDBOX_COPY_CONFIG_ID,
    audit_cross_agent_handoff,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/results/studio_runs/C001_20261030_v4/analysis/studio_original.json"


def fixture():
    native = ARCHIVE.read_bytes()
    obj = json.loads(native)
    report = json.dumps({"document_qa_status": "PASS",
                         "python_qa_status": "NOT_VERIFIED"}, sort_keys=True).encode()
    manifest = {
        "protocol_version": HANDOFF_VERSION,
        "producer": "UPSTAGE_QA_SANDBOX",
        "studio": {
            "agent_id": SANDBOX_AGENT_ID,
            "config_id": "cfg_synthetic_unverified",
            "config_version": 4,
            "job_id": obj["metadata"]["job_execution_id"],
            "step_run_id": obj["metadata"]["step_run_id"],
            "execution_kind": "ARCHIVED_STUDIO",
            "input_file_ids": [row["file_id"] for row in obj["metadata"]["source_files"]],
            "native_sha256": hashlib.sha256(native).hexdigest(),
            "qa_report_sha256": hashlib.sha256(report).hexdigest(),
        },
        "verdict": {
            "document_qa_status": "PASS",
            "python_qa_status": "NOT_VERIFIED",
            "issues": [{"code": "EXTERNAL_SAFETY_NOT_VERIFIED",
                        "severity": "INFO", "scope": "python"}],
        },
        "github": {
            "repository": "dohun3540-crypto/leadtime-guardian-agent.copy",
            "head_sha": "a" * 40, "contract_version": HANDOFF_VERSION,
        },
    }
    return manifest, native, report


def check(manifest, native=None, report=None, **kw):
    return audit_cross_agent_handoff(manifest, native_bytes=native,
                                     report_bytes=report, **kw)


def codes(response):
    return {problem["issue_code"] for problem in response["issues"]}


def test_document_pass_python_unverified_blocks_integration_not_document():
    manifest, native, report = fixture()
    outcome = check(manifest, native, report)
    assert outcome["document_qa_status"] == "PASS"
    assert outcome["python_qa_status"] == "NOT_VERIFIED"
    assert outcome["qa_status"] == "BLOCKED"
    assert outcome["release_or_merge_authorized"] is False
    assert outcome["new_studio_run_performed_by_validator"] is False
    assert outcome["studio_live_execution_authenticated"] is False


def test_archived_evidence_cannot_claim_new_live_studio_job():
    manifest, native, report = fixture()
    manifest["studio"]["execution_kind"] = "NEW_LIVE_STUDIO"
    assert "ARCHIVED_JOB_REUSED_AS_NEW" in codes(check(manifest, native, report))


def test_archived_replay_cannot_be_promoted_to_live_contract():
    manifest, native, report = fixture()
    manifest["verdict"]["python_qa_status"] = "PASS"
    manifest["verdict"]["issues"] = []
    result_obj = {"document_qa_status": "PASS", "python_qa_status": "PASS"}
    report = json.dumps(result_obj).encode()
    manifest["studio"]["qa_report_sha256"] = hashlib.sha256(report).hexdigest()
    manifest["studio"]["execution_kind"] = "ARCHIVED_REPLAY"
    assert check(manifest, native, report)["qa_status"] == "NOT_VERIFIED"


@pytest.mark.parametrize(("status", "expect"), [
    ("FAIL", "FAIL"),
    ("NEEDS_REVIEW", "FAIL"),
    ("NOT_VERIFIED", "BLOCKED"),
    ("PASS", "BLOCKED"),
])
def test_python_not_verified_does_not_flip_document_verdict(status, expect):
    manifest, native, report = fixture()
    manifest["verdict"]["document_qa_status"] = status
    report = json.dumps({"document_qa_status": status,
                         "python_qa_status": "NOT_VERIFIED"}).encode()
    manifest["studio"]["qa_report_sha256"] = hashlib.sha256(report).hexdigest()
    outcome = check(manifest, native, report)
    assert outcome["document_qa_status"] == status
    assert outcome["qa_status"] == expect


@pytest.mark.parametrize(("part", "key", "value", "issue"), [
    ("studio", "agent_id", "agt_wrong", "SANDBOX_AGENT_ID_MISMATCH"),
    ("studio", "config_id", "", "UNVERIFIED_CONFIG_ID"),
    ("studio", "config_version", True, "INVALID_CONFIG_VERSION"),
    ("studio", "input_file_ids", [], "INVALID_INPUT_FILE_IDS"),
    ("studio", "input_file_ids", ["file_a", "file_a"], "INVALID_INPUT_FILE_IDS"),
    ("studio", "native_sha256", "none", "INVALID_NATIVE_DIGEST"),
    ("studio", "qa_report_sha256", None, "INVALID_REPORT_DIGEST"),
    ("github", "head_sha", "bad", "INVALID_GITHUB_COMMIT"),
    ("github", "repository", "unknown", "GITHUB_REPOSITORY_MISMATCH"),
    ("verdict", "python_qa_status", "SUCCEEDED", "INVALID_PYTHON_QA_STATUS"),
    ("verdict", "document_qa_status", "OK", "INVALID_DOCUMENT_QA_STATUS"),
])
def test_handoff_invalid_contracts_fail(part, key, value, issue):
    manifest, native, report = fixture()
    manifest[part][key] = value
    assert issue in codes(check(manifest, native, report))


def test_wrong_expected_config_and_python_sha():
    manifest, native, report = fixture()
    result = check(manifest, native, report,
                   expected_config_id="cfg_different",
                   expected_github_sha="b" * 40)
    assert "CONFIG_ID_MISMATCH" in codes(result)
    assert "GITHUB_COMMIT_MISMATCH" in codes(result)


def test_tampered_native_bytes_fail():
    manifest, native, report = fixture()
    assert "NATIVE_HASH_MISMATCH" in codes(check(manifest, native + b" ", report))


def test_tampered_qa_report_fail():
    manifest, native, report = fixture()
    assert "QA_REPORT_HASH_MISMATCH" in codes(check(manifest, native, report + b" "))


def test_self_reported_digest_without_actual_bytes_is_not_verification():
    manifest, _, _ = fixture()
    result = check(manifest)
    assert result["qa_status"] == "BLOCKED"
    assert result["studio_live_execution_authenticated"] is False


def test_report_semantic_mismatch_fail():
    manifest, native, report = fixture()
    obj = json.loads(report)
    obj["python_qa_status"] = "PASS"
    report = json.dumps(obj).encode()
    manifest["studio"]["qa_report_sha256"] = hashlib.sha256(report).hexdigest()
    assert "QA_REPORT_VERDICT_MISMATCH" in codes(check(manifest, native, report))


def test_native_input_file_id_mismatch_fail():
    manifest, native, report = fixture()
    manifest["studio"]["input_file_ids"][0] = "file_FAKE"
    assert "NATIVE_INPUT_FILE_MISMATCH" in codes(check(manifest, native, report))


@pytest.mark.parametrize("bad", [[1], [None], [{"x": 1}], "file_1"])
def test_bad_file_ids_do_not_throw(bad):
    manifest, native, report = fixture()
    manifest["studio"]["input_file_ids"] = bad
    assert "INVALID_INPUT_FILE_IDS" in codes(check(manifest, native, report))


@pytest.mark.parametrize("bad", [
    [{"code": "X", "scope": [], "severity": "INFO"}],
    [{"code": "X", "scope": "document", "severity": {}}],
    [{"code": [], "scope": "document", "severity": "INFO"}],
])
def test_unhashable_issue_fields_fail_closed(bad):
    manifest, native, report = fixture()
    manifest["verdict"]["issues"] = bad
    assert "INVALID_QA_ISSUE" in codes(check(manifest, native, report))


def test_python_unverified_issue_cannot_coexist_with_python_pass():
    manifest, native, report = fixture()
    manifest["verdict"]["python_qa_status"] = "PASS"
    assert "UNVERIFIED_PYTHON_MARKED_PASS" in codes(check(manifest, native, report))


def test_document_error_cannot_hide_under_pass():
    manifest, native, report = fixture()
    manifest["verdict"]["issues"] = [
        {"code": "DOC_MISSING_PO", "scope": "document", "severity": "ERROR"},
    ]
    assert "DOCUMENT_FALSE_PASS" in codes(check(manifest, native, report))


def test_no_input_mutation():
    manifest, native, report = fixture()
    original = deepcopy(manifest)
    check(manifest, native, report)
    assert manifest == original


def test_file_id_order_is_not_contract_significant():
    manifest, native, report = fixture()
    manifest["studio"]["input_file_ids"].reverse()
    result = check(manifest, native, report)
    assert result["qa_status"] == "BLOCKED"
    assert "NATIVE_INPUT_FILE_MISMATCH" not in codes(result)


def test_invalid_native_file_identifier_fails_closed():
    manifest, native, report = fixture()
    obj = json.loads(native)
    obj["metadata"]["source_files"][0]["file_id"] = {"bad": "identifier"}
    native = json.dumps(obj).encode()
    manifest["studio"]["native_sha256"] = hashlib.sha256(native).hexdigest()
    result = check(manifest, native, report)
    assert result["qa_status"] == "FAIL"
    assert "NATIVE_INPUT_FILE_MISMATCH" in codes(result)


def test_copy_agent_is_explicitly_selected_and_pinned():
    manifest, native, report = fixture()
    manifest["studio"].update({
        "agent_id": SANDBOX_COPY_AGENT_ID,
        "config_id": SANDBOX_COPY_CONFIG_ID,
        "config_version": 1,
    })
    default_result = check(manifest, native, report)
    assert "SANDBOX_AGENT_ID_MISMATCH" in codes(default_result)
    selected = check(manifest, native, report, expected_agent_id=SANDBOX_COPY_AGENT_ID)
    assert selected["qa_status"] == "BLOCKED"  # Python NOT_VERIFIED
    assert selected["document_qa_status"] == "PASS"
    assert selected["release_or_merge_authorized"] is False


@pytest.mark.parametrize(("field", "invalid", "expected"), [
    ("config_id", "cfg_WRONG", "COPIED_CONFIG_ID_MISMATCH"),
    ("config_version", 5, "COPIED_CONFIG_VERSION_MISMATCH"),
])
def test_copied_sandbox_identity_fails_closed(field, invalid, expected):
    manifest, native, report = fixture()
    manifest["studio"].update({
        "agent_id": SANDBOX_COPY_AGENT_ID,
        "config_id": SANDBOX_COPY_CONFIG_ID,
        "config_version": 1,
    })
    manifest["studio"][field] = invalid
    assert expected in codes(check(
        manifest, native, report, expected_agent_id=SANDBOX_COPY_AGENT_ID,
    ))


def test_arbitrary_agent_id_cannot_be_whitelisted_by_argument():
    manifest, native, report = fixture()
    manifest["studio"]["agent_id"] = "agt_UNTRUSTED"
    result = check(manifest, native, report, expected_agent_id="agt_UNTRUSTED")
    assert "UNAPPROVED_SANDBOX_AGENT" in codes(result)
    assert result["qa_status"] == "FAIL"


def test_copied_historical_job_not_promoted_to_fresh_live():
    manifest, native, report = fixture()
    manifest["studio"].update({
        "agent_id": SANDBOX_COPY_AGENT_ID,
        "config_id": SANDBOX_COPY_CONFIG_ID,
        "config_version": 1,
        "job_id": "job_9DmRWeQsSShHgWUugkELtk",
        "execution_kind": "NEW_LIVE_STUDIO",
    })
    result = check(manifest, native, report, expected_agent_id=SANDBOX_COPY_AGENT_ID)
    assert "ARCHIVED_JOB_REUSED_AS_NEW" in codes(result)


def test_explicit_provenance_mismatch_is_warning_needing_human_review():
    manifest, native, report = fixture()
    manifest["verdict"]["issues"].append({
        "code": "EXECUTION_PROVENANCE_MISMATCH",
        "scope": "provenance",
        "severity": "ERROR",  # Normalize sender classification to a review warning.
    })
    result = check(manifest, native, report)
    flagged = [x for x in result["issues"]
               if x["issue_code"] == "EXECUTION_PROVENANCE_MISMATCH"]
    assert len(flagged) == 1
    assert flagged[0]["severity"] == "WARNING"
    assert result["requires_human_review"] is True
    assert result["qa_status"] == "BLOCKED"
    assert result["studio_live_execution_authenticated"] is False
    assert result["release_or_merge_authorized"] is False


def test_distinct_historical_prediction_is_not_automatically_provenance_error():
    manifest, native, report = fixture()
    # The QA Job is bound to native metadata. No undocumented equality between
    # an explicitly separate historical operational prediction and the QA Job.
    result = check(manifest, native, report)
    assert "EXECUTION_PROVENANCE_MISMATCH" not in codes(result)
    assert result["requires_human_review"] is False


@pytest.mark.parametrize("missing", ["absent", "empty"])
def test_native_source_evidence_missing_fails_closed(missing):
    manifest, native, report = fixture()
    obj = json.loads(native)
    if missing == "absent":
        del obj["metadata"]["source_files"]
    else:
        obj["metadata"]["source_files"] = []
    native = json.dumps(obj).encode()
    manifest["studio"]["native_sha256"] = hashlib.sha256(native).hexdigest()
    outcome = check(manifest, native, report)
    assert outcome["qa_status"] == "FAIL"
    assert "NATIVE_SOURCE_FILE_EVIDENCE_MISSING" in codes(outcome)
