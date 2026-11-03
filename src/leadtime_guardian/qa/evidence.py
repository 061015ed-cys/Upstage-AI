"""Validate actual Studio config export and execution record against a handoff.

This is an *additional* evidence layer; it does not authenticate the Studio
cloud, run a workflow, verify PDF truth, or authorize publication.
"""
from __future__ import annotations

from typing import Any

from .cross_agent import SANDBOX_AGENT_ID


def audit_export_binding(
    manifest: Any, config_export: Any, execution_record: Any,
    *, expected_agent_id: str = SANDBOX_AGENT_ID,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []

    def fail(code: str, field: str) -> None:
        issues.append({"issue_code": code, "field": field, "severity": "ERROR"})

    if not isinstance(manifest, dict) or not isinstance(manifest.get("studio"), dict):
        fail("INVALID_HANDOFF_MANIFEST", "manifest.studio")
        studio: dict[str, Any] = {}
    else:
        studio = manifest["studio"]

    if not isinstance(config_export, dict):
        fail("INVALID_CONFIG_EXPORT", "config_export")
        exported: dict[str, Any] = {}
    else:
        exported = config_export.get("exportedFrom")
        if not isinstance(exported, dict):
            fail("INVALID_CONFIG_PROVENANCE", "config_export.exportedFrom")
            exported = {}
        if not isinstance(config_export.get("workflowConfig"), dict):
            fail("INVALID_WORKFLOW_CONFIG", "config_export.workflowConfig")

    if not isinstance(execution_record, dict):
        fail("INVALID_EXECUTION_RECORD", "execution_record")
        record: dict[str, Any] = {}
    else:
        record = execution_record

    for field, manifest_name, export_name in (
        ("agent_id", "agent_id", "workflowId"),
        ("config_id", "config_id", "configId"),
        ("config_version", "config_version", "configVer"),
    ):
        expected = studio.get(manifest_name)
        actual = exported.get(export_name)
        if field == "config_version":
            valid = type(actual) is int and actual > 0 and type(expected) is int
        else:
            valid = isinstance(actual, str) and bool(actual) and isinstance(expected, str)
        if not valid or actual != expected:
            fail("CONFIG_" + field.upper() + "_MISMATCH", "config_export.exportedFrom." + export_name)
        if record.get(field) != expected or (field == "config_version" and type(record.get(field)) is not int):
            fail("RUN_" + field.upper() + "_MISMATCH", "execution_record." + field)

    if studio.get("agent_id") != expected_agent_id:
        fail("UNEXPECTED_QA_SANDBOX_AGENT", "manifest.studio.agent_id")

    for manifest_key, record_key in (
        ("job_id", "job_id"), ("step_run_id", "native_step_run_id"),
    ):
        value = studio.get(manifest_key)
        if not isinstance(value, str) or not value.strip() or record.get(record_key) != value:
            fail("RUN_" + manifest_key.upper() + "_MISMATCH", "execution_record." + record_key)

    kind = studio.get("execution_kind")
    mode = record.get("execution_mode")
    if kind == "NEW_LIVE_STUDIO":
        if record.get("studio_execution_completed") is not True:
            fail("RUN_NOT_COMPLETED", "execution_record.studio_execution_completed")
        if mode not in ("live_studio_web", "live_studio_agents_api"):
            fail("NEW_RUN_MODE_MISMATCH", "execution_record.execution_mode")
    elif kind in ("SDK_HTTP_MOCK", "FAKE_CLIENT_TEST", "SYNTHETIC_FIXTURE"):
        if isinstance(mode, str) and mode.startswith("live_studio_"):
            fail("MOCK_MARKED_LIVE", "execution_record.execution_mode")
    elif kind not in ("ARCHIVED_STUDIO", "ARCHIVED_REPLAY"):
        fail("UNSUPPORTED_RUN_KIND", "manifest.studio.execution_kind")

    return {
        "qa_status": "FAIL" if issues else "PASS",
        "issues": issues,
        "evidence_type": "EXPORT_RECORD_CONSISTENCY_ONLY",
        "studio_cloud_authenticated": False,
        "release_or_merge_authorized": False,
    }
