"""Selective PR14 Studio QA adapter contract tests on the PR13 freeze baseline.

Synthetic reports only. A structural adapter PASS does not authenticate Studio.
"""
from copy import deepcopy

import pytest

from leadtime_guardian.qa.studio_qa_adapter import normalize_studio_qa_report


def _report():
    return {
        "case_id": "C001",
        "qa_status": "NOT_VERIFIED",
        "checked_document_ids": ["SYN-PO-DOC"],
        "issues": [{"issue_code": "MISSING_NATIVE", "scope": "integration",
                    "severity": "info"}],
        "evidence_status": "PARTIAL",
        "recommended_action": "Obtain source Native",
        "workflow_version": None,
        "execution_provenance": {
            "workflow_id": None, "config_id": None, "job_id": None,
            "source_files": None,
        },
        "field_checks": [{"field": "po_id", "status": "NOT_VERIFIED"}],
    }


def _adapt(doc):
    return normalize_studio_qa_report(
        doc, expected_case_id="C001", expected_document_ids=["SYN-PO-DOC"],
    )


def test_lowercase_info_null_version_is_triage_not_live_pass():
    source = _report()
    original = deepcopy(source)
    mapped = _adapt(source)
    assert mapped["adapter_status"] == "PASS"
    assert mapped["document_qa_status"] == "NOT_VERIFIED"
    assert mapped["python_qa_status"] == "NOT_VERIFIED"
    assert mapped["workflow_version"] is None
    assert mapped["requires_human_review"] is True
    assert mapped["pdf_grounding_verified"] is False
    assert mapped["python_run_verified"] is False
    assert {"code": "MISSING_NATIVE", "scope": "integration",
            "severity": "INFO"} in mapped["issues"]
    assert {"code": "STUDIO_ISSUE_SEVERITY_CASE_NORMALIZED",
            "scope": "integration", "severity": "WARNING"} in mapped["issues"]
    assert {"code": "STUDIO_WORKFLOW_VERSION_NOT_VERIFIED",
            "scope": "integration", "severity": "WARNING"} in mapped["issues"]
    assert mapped["original_report_modified"] is False
    assert source == original


@pytest.mark.parametrize("severity,normalized", [
    ("info", "INFO"), ("warning", "WARNING"), ("error", "ERROR"),
])
def test_known_lowercase_severity_requires_review(severity, normalized):
    source = _report()
    source["issues"][0]["severity"] = severity
    source["workflow_version"] = "v1"
    result = _adapt(source)
    assert result["adapter_status"] == "PASS"
    assert {"code": "MISSING_NATIVE", "scope": "integration",
            "severity": normalized} in result["issues"]
    assert result["requires_human_review"] is True
    assert source["issues"][0]["severity"] == severity


def test_null_version_cannot_turn_reported_pass_into_verified_pass():
    source = _report()
    source["qa_status"] = "PASS"
    source["evidence_status"] = "VERIFIED"
    source["issues"] = []
    source["field_checks"] = [{"field": "po_id", "status": "VERIFIED"}]
    source["execution_provenance"] = {
        "workflow_id": "wf-source", "config_id": "cfg-source",
        "job_id": "job-source", "source_files": ["file-source"],
    }
    result = _adapt(source)
    assert result["adapter_status"] == "PASS"
    assert result["document_qa_status"] != "PASS"
    assert result["requires_human_review"] is True
    assert result["python_run_verified"] is False


def test_absent_version_key_remains_failure():
    source = _report()
    del source["workflow_version"]
    result = _adapt(source)
    assert result["adapter_status"] == "FAIL"
    assert result["document_qa_status"] != "PASS"


@pytest.mark.parametrize("bad", ["Info", "WARN", "debug", "", None, 7])
def test_unknown_severity_remains_fail_closed(bad):
    source = _report()
    source["issues"][0]["severity"] = bad
    source["workflow_version"] = "v1"
    result = _adapt(source)
    assert result["adapter_status"] == "FAIL"
    assert result["document_qa_status"] != "PASS"


def test_case_and_document_id_mismatch_preserved():
    source = _report()
    source["case_id"] = "C013"
    source["checked_document_ids"] = ["WRONG-DOC"]
    result = _adapt(source)
    assert result["adapter_status"] == "FAIL"
    assert {i["issue_code"] for i in result["adapter_issues"]} >= {
        "STUDIO_CASE_ID_MISMATCH", "STUDIO_DOCUMENT_ID_MISMATCH",
    }
