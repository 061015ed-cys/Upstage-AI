"""Read-only native Studio Instruct envelope contract and run-binding checks.

A PASS proves only internal JSON/metadata consistency against supplied expected
run IDs, not source-PDF accuracy, job authenticity or fresh cloud execution.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .audit import load_json_strict

KINDS = frozenset({"purchase_order", "delivery_notice", "quotation", "other"})


def audit_native_envelope(
    raw: Any, *, expected_job_id: str | None = None, expected_step_run_id: str | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []

    def fail(code: str, field: str) -> None:
        issues.append({"issue_code": code, "field": field, "severity": "ERROR"})

    def report() -> dict[str, Any]:
        status = "FAIL" if issues else ("PASS" if expected_job_id else "NOT_VERIFIED")
        return {"qa_status": status, "issues": issues,
                "evidence_type": "NATIVE_ENVELOPE_CONTRACT_ONLY",
                "new_studio_run_started": False, "pdf_grounding_verified": False}

    if not isinstance(raw, dict):
        fail("INVALID_NATIVE_ENVELOPE", "$")
        return report()
    for field in ("documents", "output", "output_text", "provenance", "human_reviewed", "gold"):
        if field in raw:
            fail("AMBIGUOUS_OR_GOLD_NATIVE_ENVELOPE", field)
    if raw.get("needs_review") is True or raw.get("status") in (
        "failed", "cancelled", "incomplete", "queued", "in_progress", "NEEDS_REVIEW"
    ) or raw.get("error"):
        fail("INCOMPLETE_OR_REVIEW_RUN", "status")

    meta = raw.get("metadata")
    if not isinstance(meta, dict):
        fail("INVALID_NATIVE_METADATA", "metadata")
        return report()
    job_id, step_id = meta.get("job_execution_id"), meta.get("step_run_id")
    if not isinstance(job_id, str) or not job_id.startswith("job_"):
        fail("INVALID_JOB_ID", "metadata.job_execution_id")
    if not isinstance(step_id, str) or not step_id.strip():
        fail("INVALID_STEP_RUN_ID", "metadata.step_run_id")
    if isinstance(meta.get("occurrence_id"), str) and meta["occurrence_id"] != step_id:
        fail("STEP_OCCURRENCE_MISMATCH", "metadata.occurrence_id")
    if expected_job_id is not None and (not isinstance(expected_job_id, str) or job_id != expected_job_id):
        fail("CROSS_JOB_MISMATCH", "metadata.job_execution_id")
    if expected_step_run_id is not None and (
        not isinstance(expected_step_run_id, str) or step_id != expected_step_run_id
    ):
        fail("CROSS_STEP_MISMATCH", "metadata.step_run_id")

    content = raw.get("content")
    if not isinstance(content, str):
        fail("INVALID_NATIVE_CONTENT", "content")
        return report()
    try:
        decoded = load_json_strict(content)
    except (ValueError, TypeError, UnicodeDecodeError):
        fail("INVALID_OR_DUPLICATE_NATIVE_JSON", "content")
        return report()
    if not isinstance(decoded, dict) or set(decoded) != {"documents"}:
        fail("INVALID_NATIVE_DOCUMENT_WRAPPER", "content")
        return report()
    documents = decoded["documents"]
    if not isinstance(documents, list) or not documents:
        fail("MISSING_NATIVE_DOCUMENTS", "content.documents")
        return report()
    identifiers: set[str] = set()
    kinds = []
    for index, doc in enumerate(documents):
        if not isinstance(doc, dict):
            fail("INVALID_NATIVE_DOCUMENT", f"content.documents[{index}]")
            continue
        doc_id, kind = doc.get("document_id"), doc.get("document_type")
        if not isinstance(doc_id, str) or not doc_id.strip() or doc_id in identifiers:
            fail("MISSING_OR_DUPLICATE_DOCUMENT_ID", f"content.documents[{index}].document_id")
        else:
            identifiers.add(doc_id)
        if not isinstance(kind, str) or kind not in KINDS:
            fail("INVALID_NATIVE_DOCUMENT_TYPE", f"content.documents[{index}].document_type")
        else:
            kinds.append(kind)

    sources = meta.get("source_files")
    source_ids: dict[str, str] = {}
    if sources is not None:
        if not isinstance(sources, list) or not sources:
            fail("INVALID_SOURCE_MANIFEST", "metadata.source_files")
        else:
            for index, entry in enumerate(sources):
                if not isinstance(entry, dict):
                    fail("INVALID_SOURCE_MANIFEST_ENTRY", f"metadata.source_files[{index}]")
                    continue
                file_id, name = entry.get("file_id"), entry.get("file_name")
                if (not isinstance(file_id, str) or not file_id.strip() or
                        not isinstance(name, str) or not name.strip() or file_id in source_ids):
                    fail("INVALID_OR_DUPLICATE_SOURCE", f"metadata.source_files[{index}]")
                    continue
                source_ids[file_id] = name

    merge = meta.get("merge")
    if merge is not None:
        items = merge.get("items") if isinstance(merge, dict) else None
        if not isinstance(items, list) or len(items) != len(documents):
            fail("MERGE_DOCUMENT_COUNT_MISMATCH", "metadata.merge.items")
        else:
            merge_kinds = []
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    fail("INVALID_MERGE_ITEM", f"metadata.merge.items[{index}]")
                    continue
                kind = item.get("document_type")
                if not isinstance(kind, str) or kind not in KINDS:
                    fail("INVALID_MERGE_TYPE", f"metadata.merge.items[{index}].document_type")
                else:
                    merge_kinds.append(kind)
                refs = item.get("source_files")
                if not isinstance(refs, list) or not refs:
                    fail("MERGE_SOURCE_MISSING", f"metadata.merge.items[{index}].source_files")
                    continue
                for ref in refs:
                    if not isinstance(ref, dict):
                        fail("MERGE_SOURCE_MISMATCH", f"metadata.merge.items[{index}].source_files")
                        continue
                    ref_id = ref.get("file_id")
                    if not isinstance(ref_id, str) or ref_id not in source_ids or source_ids[ref_id] != ref.get("file_name"):
                        fail("MERGE_SOURCE_MISMATCH", f"metadata.merge.items[{index}].source_files")
            if Counter(merge_kinds) != Counter(kinds):
                fail("MERGE_TYPE_COUNTS_MISMATCH", "metadata.merge.items")
    return report()
