"""Local evidence bridge for team 2 studio-provenance/1 and QA handoff.

Separate operational and QA Studio Jobs may legitimately have different IDs.
Matching local PDFs is necessary but never authenticates their cloud uploads.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")


def audit_team2_provenance_link(
    qa_handoff: Any,
    team2_sidecar: Any,
    qa_pdf_receipt: Any,
    operational_pdf_receipt: Any,
    *,
    pdf_root: str | Path | None = None,
) -> dict[str, Any]:
    """Compare explicit local SHA evidence without asserting live/cloud identity."""
    issues: list[dict[str, str]] = []
    root = Path(pdf_root) if pdf_root is not None else None

    def flag(code: str, field: str, severity: str = "ERROR") -> None:
        issues.append({"issue_code": code, "field": field, "severity": severity})

    def result() -> dict[str, Any]:
        return {
            "qa_status": ("FAIL" if any(i["severity"] == "ERROR" for i in issues)
                          else "BLOCKED"),
            "python_qa_status": "NOT_VERIFIED",
            "same_local_pdf_bytes_verified": local_match,
            "operational_studio_job_authenticated": False,
            "qa_studio_job_authenticated": False,
            "cross_agent_release_authorized": False,
            "issues": issues,
            "team2_contract": "studio-provenance/1",
            "qa_contract": "leadtime-cross-agent/v1",
        }

    local_match = False
    if not isinstance(qa_handoff, dict) or not isinstance(qa_handoff.get("studio"), dict):
        flag("INVALID_QA_HANDOFF", "qa_handoff")
        return result()
    if qa_handoff.get("protocol_version") != "leadtime-cross-agent/v1":
        flag("QA_PROTOCOL_MISMATCH", "qa_handoff.protocol_version")
    if not isinstance(team2_sidecar, dict):
        flag("INVALID_TEAM2_SIDECAR", "team2_sidecar")
        return result()
    if team2_sidecar.get("contract_version") != "studio-provenance/1":
        flag("TEAM2_CONTRACT_MISMATCH", "team2_sidecar.contract_version")
    operational_export_sha = team2_sidecar.get("export_sha256")
    if (not isinstance(operational_export_sha, str)
            or not HEX64.fullmatch(operational_export_sha)):
        flag("INVALID_TEAM2_EXPORT_DIGEST", "team2_sidecar.export_sha256")
    if team2_sidecar.get("evidence_verified_against_pdf") is not False:
        # True here would be a self-asserted claim, never independent PDF proof.
        flag("UNSUPPORTED_PDF_VERIFICATION_CLAIM",
             "team2_sidecar.evidence_verified_against_pdf")
    qa_studio = qa_handoff["studio"]
    if not isinstance(qa_studio.get("job_id"), str) or not qa_studio["job_id"].startswith("job_"):
        flag("INVALID_QA_JOB_ID", "qa_handoff.studio.job_id")

    # Distinct past operational Job IDs are not evidence of a mismatch.
    metadata = team2_sidecar.get("studio_metadata_supplied")
    if metadata is not None and not isinstance(metadata, dict):
        flag("INVALID_TEAM2_STUDIO_METADATA", "team2_sidecar.studio_metadata_supplied")
    if (not isinstance(metadata, dict) or not metadata.get("job_execution_id")):
        flag("TEAM2_JOB_ID_NOT_VERIFIED", "team2_sidecar.studio_metadata_supplied",
             "WARNING")
    # Business validation is a supplied result, not an independently run Python QA.
    if not isinstance(team2_sidecar.get("business_validation_status"), str):
        flag("TEAM2_BUSINESS_STATUS_NOT_VERIFIED",
             "team2_sidecar.business_validation_status", "WARNING")

    def receipt(payload: Any, name: str) -> dict[str, str] | None:
        if not isinstance(payload, dict):
            flag("INVALID_PDF_RECEIPT", name)
            return None
        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            flag("INVALID_PDF_CASE_ID", name + ".case_id")
            return None
        if case_id != qa_studio.get("case_id"):
            flag("PDF_CASE_ID_MISMATCH", name + ".case_id")
        rows = payload.get("files")
        if not isinstance(rows, list) or not rows:
            flag("INVALID_PDF_FILE_LIST", name + ".files")
            return None
        found: dict[str, str] = {}
        ids: set[str] = set()
        for idx, row in enumerate(rows):
            loc = f"{name}.files[{idx}]"
            if not isinstance(row, dict):
                flag("INVALID_PDF_FILE", loc)
                continue
            filename, sha, fid = (row.get("filename"), row.get("sha256"),
                                  row.get("file_id"))
            if (not isinstance(filename, str) or not filename.endswith(".pdf")
                    or Path(filename).name != filename or filename in found):
                flag("INVALID_PDF_FILENAME", loc + ".filename")
                continue
            if not isinstance(fid, str) or not fid.startswith("file_") or fid in ids:
                flag("INVALID_PDF_SOURCE_ID", loc + ".file_id")
                continue
            ids.add(fid)
            if not isinstance(sha, str) or not HEX64.fullmatch(sha):
                flag("INVALID_PDF_DIGEST", loc + ".sha256")
                continue
            found[filename] = sha.lower()
        if len(found) != len(rows):
            flag("INCOMPLETE_PDF_RECEIPT", name + ".files")
        return found

    qa = receipt(qa_pdf_receipt, "qa_pdf_receipt")
    operation = receipt(operational_pdf_receipt, "operational_pdf_receipt")
    if qa is not None and operation is not None:
        if qa != operation:
            flag("SOURCE_PDF_SET_MISMATCH", "pdf_receipts")
        elif root is None:
            flag("PDF_BYTES_NOT_PROVIDED", "pdf_root", "WARNING")
        else:
            try:
                # Reject symlink escapes; a receipt cannot authorize arbitrary
                # files outside the supplied PDF directory.
                actual_root = root.resolve(strict=True)
                pdf_paths = [actual_root / name for name in qa]
                if any(p.is_symlink() or not p.resolve().is_relative_to(actual_root)
                       for p in pdf_paths):
                    flag("PDF_PATH_OUTSIDE_TRUSTED_ROOT", "pdf_root")
                elif all(
                    p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == sha
                    for p, sha in zip(pdf_paths, qa.values(), strict=True)
                ):
                    local_match = True
                else:
                    flag("PDF_BYTES_HASH_MISMATCH", "pdf_root")
            except OSError:
                flag("PDF_BYTES_UNREADABLE", "pdf_root")
        # QA input IDs are checked against the QA manifest; the two providers'
        # own file IDs are not required to be identical.
        if isinstance(qa_pdf_receipt, dict):
            qa_ids = [x.get("file_id") for x in qa_pdf_receipt.get("files", [])
                      if isinstance(x, dict)]
            manifest_ids = qa_studio.get("input_file_ids")
            if (not isinstance(manifest_ids, list)
                    or len(qa_ids) != len(manifest_ids)
                    or set(qa_ids) != set(manifest_ids)):
                flag("QA_PDF_SOURCE_ID_MISMATCH", "qa_handoff.studio.input_file_ids")
    if local_match:
        flag("STUDIO_UPLOAD_BINDING_NOT_AUTHENTICATED",
             "execution_receipts", "WARNING")
    return result()
