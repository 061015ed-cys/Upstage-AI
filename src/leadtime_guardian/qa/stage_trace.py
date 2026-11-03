"""Strict, read-only trace of original Studio Stage bytes and 22 C001 XLSX blanks.

This is local source-file inspection, NEVER a provider execution attestation.
A sharedStrings pointer 49 is a decoded EMPTY_STRING in the preserved XLSX.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from itertools import pairwise
from typing import Any

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.input_delivery import _read_documents

STAGES = ("Extract", "MergeDocuments", "NormalizeDocuments",
          "IndependentQA_Input", "IndependentQA_Report")
OPERATIONAL = frozenset(STAGES[:3])
DOCUMENT_STAGES = STAGES[:4]
DOC_TYPES = ("purchase_order", "delivery_notice", "quotation")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
FIELDS_BY_TYPE = {
    "purchase_order": (
        ("R2", "supplier_id"), ("T2", "revised_delivery"),
        *( (f"{c}2", f"quote.{k}") for c, k in (
            ("Y", "quote_id"), ("Z", "supplier_id"), ("AA", "product_id"),
            ("AB", "capacity"), ("AC", "arrival_date"),
            ("AD", "unit_price"), ("AE", "shipping_cost"), ("AF", "currency"),
        )),
    ),
    "delivery_notice": (
        ("R3", "supplier_id"),
        *( (f"{c}3", f"quote.{k}") for c, k in (
            ("Y", "quote_id"), ("Z", "supplier_id"), ("AA", "product_id"),
            ("AB", "capacity"), ("AC", "arrival_date"),
            ("AD", "unit_price"), ("AE", "shipping_cost"), ("AF", "currency"),
        )),
    ),
    "quotation": (
        ("S4", "original_delivery"), ("T4", "revised_delivery"),
        ("V4", "items.receipt_id"),
    ),
}
assert sum(map(len, FIELDS_BY_TYPE.values())) == 22


def classify_missing(value: Any, *, present: bool) -> str:
    if not present:
        return "MISSING"
    if value is None:
        return "NULL"
    if type(value) is bool:
        return "INVALID_TYPE"
    if isinstance(value, str):
        if value == "":
            return "EMPTY_STRING"
        if value == "null":
            return "STRING_NULL"
        if value == "0":
            return "STRING_ZERO"
        return "ACTUAL_VALUE"
    if type(value) in (int, float):
        return "NUMBER_ZERO" if value == 0 else "ACTUAL_VALUE"
    return "INVALID_TYPE"


def canonical_documents_sha256(documents: list[dict]) -> str:
    """Semantic same-case comparison; never represents original raw file SHA."""
    ordered = sorted(documents, key=lambda x: (x["document_type"], x["document_id"]))
    canonical = json.dumps(ordered, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _read_field(doc: Any, dotted: str) -> dict[str, Any]:
    value = doc
    for segment in dotted.split("."):
        if isinstance(value, list):
            if len(value) == 0:
                return {"state": "EMPTY_ARRAY", "value": None}
            if len(value) != 1:
                return {"state": "ARRAY_CARDINALITY_UNRESOLVED", "value": None}
            value = value[0]
        if not isinstance(value, dict) or segment not in value:
            return {"state": "MISSING", "value": None}
        value = value[segment]
    if isinstance(value, (dict, list)):
        return {"state": "COMPLEX_VALUE", "value": None}
    state = classify_missing(value, present=True)
    return {"state": state, "value": value if state != "INVALID_TYPE" else None}


def audit_stage_evidence(manifest: Any, raw_artifacts: dict[str, Any]) -> dict:
    """Bind each original raw JSON to explicit Job/Step/SHA before any trace."""
    issues: list[dict[str, str]] = []
    stages_out: dict[str, dict] = {}
    docs_by_stage: dict[str, dict] = {}
    result: dict[str, Any] = {
        "status": "BLOCKED",
        "stage_contract_version": "leadtime-stage-intake/v1",
        "case_id": None,
        "operational_job_id": None,
        "config_id": None,
        "config_version": None,
        "xlsx_reference_sha256": (
            "ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb"
        ),
        "stages": stages_out,
        "field_trace": [],
        "first_observed_conversion": "UNKNOWN",
        "xlsx_actual_literal_49_count": 0,
        "xlsx_shared_index_49_empty_reference_count": 22,
        "studio_live_execution_authenticated": False,
        "pdf_original_bytes_authenticated": False,
        "release_or_merge_authorized": False,
        "issues": issues,
    }

    def note(code: str, stage: str, severity: str = "WARNING") -> None:
        issues.append({"issue_code": code, "stage": stage, "severity": severity})

    if (not isinstance(manifest, dict)
            or manifest.get("schema_version") != "leadtime-stage-intake/v1"
            or manifest.get("case_id") != "C001"
            or not isinstance(manifest.get("operational_job_id"), str)
            or not manifest["operational_job_id"].startswith("job_")
            or not isinstance(manifest.get("config_id"), str)
            or not manifest["config_id"].startswith("cfg_")
            or type(manifest.get("config_version")) is not int
            or manifest["config_version"] < 1
            or not isinstance(manifest.get("stages"), dict)):
        note("INVALID_STAGE_MANIFEST", "$", "ERROR")
        result["status"] = "FAIL"
        return result
    result["case_id"] = manifest["case_id"]
    result["operational_job_id"] = manifest["operational_job_id"]
    result["config_id"] = manifest["config_id"]
    result["config_version"] = manifest["config_version"]
    op_job = manifest["operational_job_id"]
    all_metadata = manifest["stages"]
    unknown = set(all_metadata) - set(STAGES)
    for name in sorted(unknown):
        note("UNEXPECTED_STAGE_NAME", name, "ERROR")
    stage_identities: set[tuple[str, str]] = set()

    def bind_step(job: str, step: str, stage: str) -> None:
        identity = (job, step)
        if identity in stage_identities:
            note("DUPLICATE_JOB_STEP_ID", stage, "ERROR")
        else:
            stage_identities.add(identity)

    for stage in STAGES:
        meta = all_metadata.get(stage)
        raw = raw_artifacts.get(stage)
        observation = {"status": "NOT_PROVIDED", "original_sha256": None,
                       "job_id": None, "step_run_id": None,
                       "document_count": None}
        stages_out[stage] = observation
        if (stage == "Extract" and isinstance(meta, dict)
                and isinstance(meta.get("branches"), dict)):
            branches = meta["branches"]
            unexpected_branches = set(branches) - set(DOC_TYPES)
            for branch_name in sorted(unexpected_branches):
                note("UNEXPECTED_EXTRACT_BRANCH", branch_name, "ERROR")
            raw_branches = raw if isinstance(raw, dict) else {}
            observed = {}
            observations = {}
            for kind in DOC_TYPES:
                branch_meta = branches.get(kind)
                payload = raw_branches.get(kind)
                if branch_meta is None or payload is None:
                    note("EXTRACT_BRANCH_NOT_PROVIDED", kind)
                    continue
                if not isinstance(branch_meta, dict) or type(payload) is not bytes:
                    note("INVALID_EXTRACT_BRANCH_EVIDENCE", kind, "ERROR")
                    continue
                sha = hashlib.sha256(payload).hexdigest()
                observations[kind] = {
                    "sha256": sha, "job_id": branch_meta.get("job_id"),
                    "step_run_id": branch_meta.get("step_run_id"),
                }
                if (branch_meta.get("sha256") != sha
                        or branch_meta.get("job_id") != op_job
                        or branch_meta.get("case_id") != manifest["case_id"]
                        or branch_meta.get("config_id") != manifest["config_id"]
                        or branch_meta.get("config_version") != manifest["config_version"]
                        or not isinstance(branch_meta.get("step_run_id"), str)
                        or not branch_meta["step_run_id"].strip()):
                    note("EXTRACT_BRANCH_SHA_OR_RUN_BINDING_MISMATCH", kind, "ERROR")
                    continue
                bind_step(op_job, branch_meta["step_run_id"], kind)
                try:
                    raw_doc = load_json_strict(payload)
                except (ValueError, TypeError, UnicodeDecodeError, RecursionError):
                    note("STRICT_JSON_FAILED", kind, "ERROR")
                    continue
                if not isinstance(raw_doc, dict):
                    note("EXTRACT_BRANCH_RAW_NOT_OBJECT", kind, "ERROR")
                    continue
                for field, expected in (("case_id", manifest["case_id"]),
                                        ("job_id", op_job),
                                        ("step_run_id", branch_meta["step_run_id"])):
                    if field in raw_doc and raw_doc[field] != expected:
                        note("EXTRACT_BRANCH_RAW_IDENTITY_MISMATCH:" + field,
                             kind, "ERROR")
                if "document" in raw_doc:
                    docs = [raw_doc["document"]]
                    error = None
                else:
                    docs, error, _, _ = _read_documents(raw_doc, qa_side=False)
                if (error is not None or not isinstance(docs, list)
                        or len(docs) != 1 or not isinstance(docs[0], dict)
                        or docs[0].get("document_type") != kind
                        or not isinstance(docs[0].get("document_id"), str)
                        or not docs[0]["document_id"].strip()):
                    note("EXTRACT_BRANCH_DOCUMENT_CONTRACT_FAILED", kind, "ERROR")
                    continue
                observed[kind] = docs[0]
            observation["branches"] = observations
            if len(observed) == 3:
                ids = [d["document_id"] for d in observed.values()]
                if len(set(ids)) != 3:
                    note("EXTRACT_BRANCH_DUPLICATE_DOCUMENT_ID", stage, "ERROR")
                else:
                    docs_by_stage[stage] = observed
                    observation["document_ids"] = ids
                    observation["document_count"] = 3
                    observation["document_content_sha256"] = canonical_documents_sha256(
                        list(observed.values())
                    )
                    observation["status"] = "LOCAL_RAW_PARSED"
            continue
        if meta is None and raw is None:
            note("STAGE_NOT_PROVIDED", stage)
            continue
        if not isinstance(meta, dict):
            note("MISSING_STAGE_METADATA", stage, "ERROR")
            continue
        if raw is None:
            note("STAGE_NOT_PROVIDED", stage)
            continue
        if type(raw) is not bytes:
            note("INVALID_STAGE_BYTES", stage, "ERROR")
            continue
        sha = hashlib.sha256(raw).hexdigest()
        observation["original_sha256"] = sha
        job = meta.get("job_id")
        step_id = meta.get("step_run_id")
        observation["job_id"] = job
        observation["step_run_id"] = step_id
        if (not isinstance(meta.get("sha256"), str)
                or HEX64.fullmatch(meta["sha256"]) is None
                or sha != meta["sha256"].lower()):
            note("STAGE_SHA256_MISMATCH", stage, "ERROR")
            continue
        if (not isinstance(job, str) or not job.startswith("job_")
                or not isinstance(step_id, str) or not step_id.strip()):
            note("JOB_OR_STEP_ID_INVALID", stage, "ERROR")
            continue
        # Extract, Merge and Normalize MUST belong to the same operation.
        # Independent QA Sandbox can have a DIFFERENT Job.
        if stage in OPERATIONAL and job != op_job:
            note("OPERATIONAL_STAGE_JOB_MISMATCH", stage, "ERROR")
            continue
        if (stage in OPERATIONAL and (
                meta.get("config_id") != manifest["config_id"]
                or meta.get("config_version") != manifest["config_version"])):
            note("OPERATIONAL_STAGE_CONFIG_MISMATCH", stage, "ERROR")
            continue
        if meta.get("case_id") != manifest["case_id"]:
            note("STAGE_CASE_ID_MISMATCH", stage, "ERROR")
            continue
        bind_step(job, step_id, stage)
        try:
            parsed = load_json_strict(raw)
        except (ValueError, TypeError, UnicodeDecodeError):
            note("STRICT_JSON_FAILED", stage, "ERROR")
            continue
        if not isinstance(parsed, dict):
            note("STAGE_ROOT_NOT_OBJECT", stage, "ERROR")
            continue
        for field, expected in (
            ("case_id", manifest["case_id"]), ("job_id", job),
            ("step_run_id", step_id),
        ):
            if field in parsed and parsed[field] != expected:
                note("RAW_STAGE_IDENTITY_CONFLICT:" + field, stage, "ERROR")
        if stage == "IndependentQA_Report":
            observation["qa_report_status"] = parsed.get("qa_status", "UNKNOWN")
            observation["status"] = "LOCAL_RAW_PARSED"
            continue
        docs, error, json_path, layers = _read_documents(
            parsed, qa_side=stage == "IndependentQA_Input",
        )
        observation["payload_path"] = json_path
        observation["json_string_layers"] = layers
        if error is not None:
            note("DOCUMENT_PAYLOAD_" + error, stage, "ERROR")
            continue
        if (not isinstance(docs, list) or len(docs) != 3
                or not all(isinstance(d, dict)
                           and isinstance(d.get("document_id"), str)
                           and d["document_id"].strip()
                           and d.get("document_type") in DOC_TYPES
                           for d in docs)):
            note("C001_THREE_DOCUMENT_SCHEMA_FAILED", stage, "ERROR")
            continue
        ids = [d["document_id"] for d in docs]
        kinds = [d["document_type"] for d in docs]
        if (len(set(ids)) != 3
                or Counter(kinds) != Counter(DOC_TYPES)):
            note("C001_DOCUMENT_IDS_OR_TYPES_MISMATCH", stage, "ERROR")
            continue
        docs_by_stage[stage] = {d["document_type"]: d for d in docs}
        observation["document_count"] = 3
        observation["document_ids"] = ids
        observation["document_content_sha256"] = canonical_documents_sha256(docs)
        observation["status"] = "LOCAL_RAW_PARSED"
    # Two independent QA steps may differ from the operational Job, but
    # cannot silently represent two different QA Sandbox Jobs.
    qa_input = stages_out["IndependentQA_Input"]
    qa_report = stages_out["IndependentQA_Report"]
    if (qa_input["status"] == "LOCAL_RAW_PARSED"
            and qa_report["status"] == "LOCAL_RAW_PARSED"
            and qa_input["job_id"] != qa_report["job_id"]):
        note("QA_INPUT_REPORT_JOB_MISMATCH", "IndependentQA_Report", "ERROR")
    result["normalize_qa_input_status"] = "NOT_VERIFIED"
    if ("NormalizeDocuments" in docs_by_stage
            and "IndependentQA_Input" in docs_by_stage):
        if (canonical_documents_sha256(
                list(docs_by_stage["NormalizeDocuments"].values())
            ) == canonical_documents_sha256(
                list(docs_by_stage["IndependentQA_Input"].values())
            )):
            result["normalize_qa_input_status"] = "LOCAL_CONTENT_MATCH"
        else:
            result["normalize_qa_input_status"] = "LOCAL_CONTENT_MISMATCH"
            note("QA_NORMALIZED_CONTENT_MISMATCH", "IndependentQA_Input", "ERROR")
    result["all_expected_raw_stages_present"] = (
        len(docs_by_stage) == len(DOCUMENT_STAGES)
        and stages_out["IndependentQA_Report"]["status"] == "LOCAL_RAW_PARSED"
    )
    for kind in DOC_TYPES:
        for cell, field in FIELDS_BY_TYPE[kind]:
            trace = {}
            for stage in DOCUMENT_STAGES:
                doc = docs_by_stage.get(stage, {}).get(kind)
                trace[stage] = _read_field(doc, field) if doc else {
                    "state": "NOT_PROVIDED", "value": None,
                }
            result["field_trace"].append({
                "cell": cell, "document_type": kind, "field": field,
                "xlsx_state": "EMPTY_STRING",
                "stage_values": trace,
                "first_observed_conversion": "UNKNOWN",
            })
    # Evidence-bounded first adjacent change; absent intermediate stages
    # are NOT bridged, because such bridging invents the conversion boundary.
    for trace in result["field_trace"]:
        states = trace["stage_values"]
        for a, b in pairwise(DOCUMENT_STAGES):
            if (states[a]["state"] == "NOT_PROVIDED"
                    or states[b]["state"] == "NOT_PROVIDED"):
                continue
            if states[a] != states[b]:
                trace["first_observed_conversion"] = a + "->" + b
                break
    if any(i["severity"] == "ERROR" for i in issues):
        result["status"] = "FAIL"
    return result
