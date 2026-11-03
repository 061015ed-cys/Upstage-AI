"""Construct an explicit v1 manifest from exact Studio raw file bytes.

Output is a local derived assertion, not an Upstage attestation or live run.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from .audit import load_json_strict
from .cross_agent import (
    APPROVED_SANDBOX_AGENTS,
    HANDOFF_VERSION,
    SANDBOX_COPY_AGENT_ID,
    SANDBOX_COPY_CONFIG_ID,
    SANDBOX_COPY_CONFIG_VERSION,
)
from .studio_contract import audit_native_envelope
from .studio_qa_adapter import STUDIO_REPORT_FORMAT, normalize_studio_qa_report

HEX40 = re.compile(r"^[a-fA-F0-9]{40}$")


def build_studio_raw_handoff(
    native_bytes: bytes, report_bytes: bytes, *, case_id: str,
    agent_id: str, config_id: str, config_version: int,
    github_sha: str, execution_kind: str = "ARCHIVED_STUDIO",
) -> dict[str, Any]:
    """Fail closed on invalid raw artifacts, identifiers and format."""
    if not isinstance(native_bytes, bytes) or not isinstance(report_bytes, bytes):
        raise TypeError("original raw file bytes required")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("explicit nonempty case_id required")
    if agent_id not in APPROVED_SANDBOX_AGENTS:
        raise ValueError("QA Agent is not on the approved allow-list")
    if not isinstance(config_id, str) or not config_id.startswith("cfg_"):
        raise ValueError("explicit Config ID required")
    if type(config_version) is not int or config_version < 1:
        raise ValueError("explicit positive Config version required")
    if (agent_id == SANDBOX_COPY_AGENT_ID
            and (config_id != SANDBOX_COPY_CONFIG_ID
                 or config_version != SANDBOX_COPY_CONFIG_VERSION)):
        raise ValueError("copied QA Sandbox config/version not approved")
    if not isinstance(github_sha, str) or not HEX40.fullmatch(github_sha):
        raise ValueError("actual 40-character Git SHA required")
    if execution_kind not in ("ARCHIVED_STUDIO", "ARCHIVED_REPLAY",
                              "NEW_LIVE_STUDIO"):
        raise ValueError("unsupported evidence kind")
    native = load_json_strict(native_bytes)
    report = load_json_strict(report_bytes)
    if not isinstance(native, dict) or not isinstance(native.get("metadata"), dict):
        raise TypeError("Native envelope metadata missing")
    meta = native["metadata"]
    job_id, step_run_id = meta.get("job_execution_id"), meta.get("step_run_id")
    native_check = audit_native_envelope(
        native, expected_job_id=job_id, expected_step_run_id=step_run_id,
    )
    if native_check["qa_status"] != "PASS":
        raise ValueError("Native envelope does not satisfy existing QA contract")
    source_files = meta.get("source_files")
    if (not isinstance(source_files, list) or not source_files
            or any(not isinstance(x, dict)
                   or not isinstance(x.get("file_id"), str)
                   for x in source_files)):
        raise ValueError("actual Native source file IDs missing")
    file_ids = [x["file_id"] for x in source_files]
    raw_documents = load_json_strict(native["content"])["documents"]
    doc_ids = [x["document_id"] for x in raw_documents]
    mapped = normalize_studio_qa_report(
        report, expected_case_id=case_id, expected_document_ids=doc_ids,
    )
    if mapped["adapter_status"] != "PASS":
        raise ValueError("raw Studio IndependentQA schema/binding invalid")
    return {
        "protocol_version": HANDOFF_VERSION,
        "producer": "UPSTAGE_QA_SANDBOX",
        "studio": {
            "agent_id": agent_id,
            "config_id": config_id,
            "config_version": config_version,
            "case_id": case_id,
            "checked_document_ids": doc_ids,
            "job_id": job_id,
            "step_run_id": step_run_id,
            "execution_kind": execution_kind,
            "input_file_ids": file_ids,
            "qa_report_format": STUDIO_REPORT_FORMAT,
            "native_sha256": hashlib.sha256(native_bytes).hexdigest(),
            "qa_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        },
        "verdict": {
            "document_qa_status": mapped["document_qa_status"],
            "python_qa_status": "NOT_VERIFIED",
            "issues": mapped["issues"],
        },
        "github": {
            "repository": "dohun3540-crypto/leadtime-guardian-agent.copy",
            "head_sha": github_sha,
            "contract_version": HANDOFF_VERSION,
        },
    }
