"""Strict, read-only mapping of a supplied Studio IndependentQA report.

The report is NOT a leadtime-cross-agent/v1 handoff manifest. This module
does not infer Python execution, source-PDF accuracy or authenticated cloud
execution. The original bytes must be retained and hashed by the caller.
"""
from __future__ import annotations

from typing import Any

STUDIO_REPORT_FORMAT = "STUDIO_INDEPENDENT_QA_V1"
DOCUMENT_STATES = frozenset({"PASS", "FAIL", "NOT_VERIFIED", "NEEDS_REVIEW"})
ISSUE_SCOPES = frozenset({"document", "python", "integration", "provenance"})
SEVERITIES = frozenset({"INFO", "WARNING", "ERROR"})
# Deliberately narrow: an unknown verification vocabulary must not promote PASS.
VERIFIED_STATES = frozenset({"VERIFIED", "SOURCE_VERIFIED"})
REQUIRED_FIELDS = frozenset({
    "case_id", "qa_status", "checked_document_ids", "issues",
    "evidence_status", "recommended_action", "workflow_version",
    "execution_provenance", "field_checks",
})


def normalize_studio_qa_report(
    report: Any, *, expected_case_id: str | None = None,
    expected_document_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Map only explicitly observed fields; no invented Python QA result.

    A well-formed, non-PASS Studio verdict can be adapted successfully. The
    adapter's own status concerns structural validity, not document quality.
    """
    problems: list[dict[str, str]] = []
    mapped: list[dict[str, str]] = []
    human_review = False

    def error(code: str, field: str) -> None:
        problems.append({"issue_code": code, "field": field, "severity": "ERROR"})

    def advisory(code: str, field: str) -> None:
        mapped.append({"code": code, "scope": "integration", "severity": "WARNING"})

    def result(document_status: str = "NOT_VERIFIED") -> dict[str, Any]:
        return {
            "adapter_status": "FAIL" if problems else "PASS",
            "document_qa_status": document_status,
            "python_qa_status": "NOT_VERIFIED",
            "issues": mapped,
            "adapter_issues": problems,
            "requires_human_review": human_review,
            "case_id": report.get("case_id") if isinstance(report, dict) else None,
            "checked_document_ids": (
                report.get("checked_document_ids") if isinstance(report, dict) else None
            ),
            "evidence_status": (
                report.get("evidence_status") if isinstance(report, dict) else None
            ),
            "workflow_version": (
                report.get("workflow_version") if isinstance(report, dict) else None
            ),
            "execution_provenance": (
                report.get("execution_provenance") if isinstance(report, dict) else None
            ),
            "field_checks": report.get("field_checks") if isinstance(report, dict) else None,
            "original_report_modified": False,
            "pdf_grounding_verified": False,
            "python_run_verified": False,
        }

    if not isinstance(report, dict):
        error("STUDIO_REPORT_NOT_OBJECT", "$")
        return result()
    for field in sorted(REQUIRED_FIELDS - report.keys()):
        error("STUDIO_REQUIRED_FIELD_MISSING", field)

    case_id = report.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        error("STUDIO_INVALID_CASE_ID", "case_id")
    if (expected_case_id is None or not isinstance(expected_case_id, str)
            or not expected_case_id.strip()):
        error("EXPECTED_CASE_ID_REQUIRED", "expected_case_id")
    elif case_id != expected_case_id:
        error("STUDIO_CASE_ID_MISMATCH", "case_id")

    checked = report.get("checked_document_ids")
    if (not isinstance(checked, list) or not checked
            or any(not isinstance(x, str) or not x.strip() for x in checked)
            or len({x for x in checked if isinstance(x, str)}) != len(checked)):
        error("STUDIO_INVALID_DOCUMENT_IDS", "checked_document_ids")
    if (not isinstance(expected_document_ids, list) or not expected_document_ids
            or any(not isinstance(x, str) or not x.strip() for x in expected_document_ids)
            or len({x for x in expected_document_ids if isinstance(x, str)})
            != len(expected_document_ids)):
        error("EXPECTED_DOCUMENT_IDS_REQUIRED", "expected_document_ids")
    elif isinstance(checked, list) and (
        len(checked) != len(expected_document_ids)
        or any(x not in expected_document_ids for x in checked)
    ):
        error("STUDIO_DOCUMENT_ID_MISMATCH", "checked_document_ids")

    original_status = report.get("qa_status")
    if not isinstance(original_status, str) or original_status not in DOCUMENT_STATES:
        error("STUDIO_INVALID_QA_STATUS", "qa_status")
        original_status = "NOT_VERIFIED"
    document_status = original_status

    feedback = report.get("issues")
    if not isinstance(feedback, list):
        error("STUDIO_INVALID_ISSUES", "issues")
    else:
        for i, item in enumerate(feedback):
            if not isinstance(item, dict):
                error("STUDIO_INVALID_ISSUE", f"issues[{i}]")
                continue
            code = item.get("issue_code", item.get("code"))
            severity = item.get("severity")
            scope = item.get("scope")
            if not isinstance(code, str) or not code.strip():
                error("STUDIO_INVALID_ISSUE_CODE", f"issues[{i}]")
                continue
            # Recognized lowercase Studio vocabulary is mapped only in the
            # adapter output; the raw report is not rewritten or authenticated.
            if isinstance(severity, str) and severity in ("info", "warning", "error"):
                severity = severity.upper()
                human_review = True
                advisory("STUDIO_ISSUE_SEVERITY_CASE_NORMALIZED",
                         f"issues[{i}].severity")
            if not isinstance(severity, str) or severity not in SEVERITIES:
                error("STUDIO_INVALID_ISSUE_SEVERITY", f"issues[{i}]")
                continue
            if scope is None:
                # Unknown scope must not be guessed as a Python or document issue.
                scope = "integration"
                human_review = True
            elif not isinstance(scope, str) or scope not in ISSUE_SCOPES:
                error("STUDIO_UNSUPPORTED_ISSUE_SCOPE", f"issues[{i}]")
                continue
            if code == "EXECUTION_PROVENANCE_MISMATCH":
                severity = "WARNING"
                scope = "provenance"
                human_review = True
            if code == "NORMALIZED_OUTPUT_NOT_PROVIDED":
                # This is a QA report claim, not proof the prior node failed.
                human_review = True
            if item.get("requires_human_review") is True:
                human_review = True
            mapped.append({"code": code, "scope": scope, "severity": severity})

    if not isinstance(report.get("recommended_action"), str):
        error("STUDIO_INVALID_RECOMMENDATION", "recommended_action")
    version = report.get("workflow_version")
    if version is None and "workflow_version" in report:
        # An explicitly unknown version is triage-only: preserve null and
        # require human review instead of inventing or verifying a version.
        human_review = True
        advisory("STUDIO_WORKFLOW_VERSION_NOT_VERIFIED", "workflow_version")
    elif not isinstance(version, (str, int)) or isinstance(version, bool) or not version:
        error("STUDIO_INVALID_WORKFLOW_VERSION", "workflow_version")
    provenance = report.get("execution_provenance")
    if provenance is not None and not isinstance(provenance, dict):
        error("STUDIO_INVALID_PROVENANCE", "execution_provenance")
    if isinstance(provenance, dict) and any(
        provenance.get(k) is None for k in ("workflow_id", "config_id", "job_id", "source_files")
    ):
        # Missing provenance is not a proven conflict.
        human_review = True
        advisory("STUDIO_PROVENANCE_UNVERIFIED", "execution_provenance")

    checks = report.get("field_checks")
    all_checks_verified = isinstance(checks, list) and bool(checks)
    if not isinstance(checks, list) or not checks:
        error("STUDIO_INVALID_FIELD_CHECKS", "field_checks")
        all_checks_verified = False
    else:
        for i, entry in enumerate(checks):
            if not isinstance(entry, dict):
                error("STUDIO_INVALID_FIELD_CHECK", f"field_checks[{i}]")
                all_checks_verified = False
                continue
            state = entry.get("status", entry.get("verification_status"))
            if not isinstance(state, str) or not state.strip():
                error("STUDIO_FIELD_CHECK_STATUS_MISSING", f"field_checks[{i}]")
                all_checks_verified = False
            elif state not in VERIFIED_STATES:
                all_checks_verified = False

    evidence_status = report.get("evidence_status")
    if not isinstance(evidence_status, str) or not evidence_status.strip():
        error("STUDIO_INVALID_EVIDENCE_STATUS", "evidence_status")
    if original_status == "PASS":
        if (evidence_status not in VERIFIED_STATES or not all_checks_verified
                or not isinstance(provenance, dict)
                or any(provenance.get(k) is None
                       for k in ("workflow_id", "config_id", "job_id", "source_files"))):
            document_status = "NOT_VERIFIED"
            human_review = True
            advisory("STUDIO_PASS_NOT_SOURCE_VERIFIED", "evidence_status")
        if any(x["severity"] == "ERROR" for x in mapped):
            document_status = "NEEDS_REVIEW"
            human_review = True
    if human_review and document_status == "PASS":
        document_status = "NEEDS_REVIEW"
    return result(document_status)
