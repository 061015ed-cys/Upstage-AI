"""Combined same-tree CLI tests. QA report is synthetic, no new Studio run."""
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_combined_e2e_check.py"
OPERATING = ROOT / "data/results/studio_runs/C001_20261030_v4/instruct_original.json"
BASE = ROOT / "data/cases/SYN-C001/trusted_base_case.json"
SCHEMA = ROOT / "configs/schemas/document_extraction.schema.json"
AGENT = "agt_HdtUJPQPXir9rGKgPWSyZG"
CONFIG = "cfg_X2xXakDtmDTHh2RoqVysvL"


def invoke(*extra):
    raw = load_json_strict(OPERATING.read_bytes())
    expected_job = raw["metadata"]["job_execution_id"]
    proc = subprocess.run([
        sys.executable, str(CLI), "--operational-native", str(OPERATING),
        "--trusted-base", str(BASE), "--schema", str(SCHEMA),
        "--operational-job-id", expected_job, "--case-id", "C001",
        "--github-sha", "a" * 40, *extra,
    ], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
    return proc, json.loads(proc.stdout)


def test_verified_archive_to_team2_python_qa_without_live_pair():
    proc, output = invoke()
    assert proc.returncode == 2, proc.stderr
    assert output["python_business_status"] == "COMPLETED"
    assert output["python_safety_status"] == "PASS_LOCAL"
    assert output["python_summary"]["changed_shortage_quantity"] == 60
    assert Decimal(output["python_summary"]["estimated_quote_cost_krw"]) == Decimal(60500)
    assert output["sha256"]["operational_native"] == hashlib.sha256(
        OPERATING.read_bytes()
    ).hexdigest()
    assert output["studio_document_status"] == "NOT_VERIFIED"
    assert output["cross_agent_status"] == "BLOCKED"
    assert output["status"] == "BLOCKED"
    assert output["release_or_merge_authorized"] is False


def test_missing_or_mismatched_operational_job_fails_closed():
    proc, output = invoke("--operational-job-id", "job_WRONG")
    assert proc.returncode == 1
    assert output["status"] == "FAIL"
    assert output["release_or_merge_authorized"] is False


def test_wrong_case_id_cannot_bind_current_operational_native():
    proc, output = invoke("--case-id", "C013")
    assert proc.returncode == 1
    assert output["status"] == "FAIL"


def test_qa_native_without_qa_report_keeps_cross_agent_blocked():
    proc, output = invoke("--qa-native", str(OPERATING))
    assert proc.returncode == 2
    assert output["cross_agent_status"] == "BLOCKED"
    assert "QA_STUDIO_RAW_ARTIFACT_PAIR_INCOMPLETE" in {
        x["issue_code"] for x in output["issues"]
    }


def test_archived_operational_bytes_plus_synthetic_raw_qa_never_release(tmp_path):
    source = load_json_strict(OPERATING.read_bytes())
    document_ids = [
        x["document_id"] for x in load_json_strict(source["content"])["documents"]
    ]
    synthetic_report = {
        "case_id": "C001", "qa_status": "NOT_VERIFIED",
        "checked_document_ids": document_ids, "issues": [],
        "evidence_status": "PARTIAL", "recommended_action": "human review required",
        "workflow_version": "v1", "execution_provenance": None,
        "field_checks": [
            {"field": key, "status": "SOURCE_NOT_VERIFIED"} for key in document_ids
        ],
    }
    qa_file = tmp_path / "synthetic_qa_report.json"
    qa_file.write_bytes(json.dumps(synthetic_report).encode())
    proc, output = invoke(
        "--qa-native", str(OPERATING), "--qa-report", str(qa_file),
        "--qa-agent-id", AGENT, "--qa-config-id", CONFIG,
        "--qa-config-version", "1", "--execution-kind", "ARCHIVED_REPLAY",
    )
    assert proc.returncode == 2, proc.stderr
    assert output["python_safety_status"] == "PASS_LOCAL"
    assert output["studio_document_status"] == "NOT_VERIFIED"
    assert output["cross_agent_status"] == "BLOCKED"
    assert output["actual_studio_e2e_status"] == "NOT_VERIFIED"
    assert output["same_original_pdf_bytes_verified"] is False
    assert output["release_or_merge_authorized"] is False
    assert output["sha256"]["qa_report"] == hashlib.sha256(
        qa_file.read_bytes()
    ).hexdigest()


def test_malformed_trusted_case_json_is_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_bytes(b'{"case_id":"SYN-C001","case_id":"SYN-C013"}')
    proc, output = invoke("--trusted-base", str(bad))
    assert proc.returncode == 1
    assert output["status"] == "FAIL"



def make_synthetic_pdf_receipt_bundle(tmp_path):
    """Local contract fixture, deliberately NOT original real PDF or Studio QA."""
    source = load_json_strict(OPERATING.read_bytes())
    native_sources = source["metadata"]["source_files"]
    doc_ids = [
        d["document_id"] for d in load_json_strict(source["content"])["documents"]
    ]
    synthetic_qa = {
        "case_id": "C001", "qa_status": "NOT_VERIFIED",
        "checked_document_ids": doc_ids,
        "issues": [], "evidence_status": "PARTIAL",
        "recommended_action": "human review required",
        "workflow_version": "v1", "execution_provenance": None,
        "field_checks": [
            {"field": d, "status": "SOURCE_NOT_VERIFIED"} for d in doc_ids
        ],
    }
    rows = []
    for item in native_sources:
        filename = item["file_name"]
        # These are synthetic PDF-like bytes solely for local SHA contract tests.
        content = b"%PDF-1.4\nSynthetic CI bytes for " + filename.encode()
        (tmp_path / filename).write_bytes(content)
        rows.append({
            "filename": filename,
            "file_id": item["file_id"],
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    source_sha = hashlib.sha256(OPERATING.read_bytes()).hexdigest()
    sidecar = {
        "contract_version": "studio-provenance/1",
        "export_sha256": source_sha,
        "studio_metadata_supplied": source["metadata"],
        "business_validation_status": "COMPLETED",
        "evidence_verified_against_pdf": False,
    }
    paths = {
        "qa_report": tmp_path / "synthetic_qa_report.json",
        "sidecar": tmp_path / "synthetic_team2_sidecar.json",
        "qa_receipt": tmp_path / "synthetic_qa_receipt.json",
        "op_receipt": tmp_path / "synthetic_op_receipt.json",
    }
    payloads = {
        "qa_report": synthetic_qa,
        "sidecar": sidecar,
        "qa_receipt": {"case_id": "C001", "files": rows},
        "op_receipt": {"case_id": "C001", "files": rows},
    }
    for key, location in paths.items():
        location.write_text(json.dumps(payloads[key]), encoding="utf-8")
    return paths, payloads


def invoke_with_synthetic_provenance(tmp_path, paths):
    return invoke(
        "--qa-native", str(OPERATING),
        "--qa-report", str(paths["qa_report"]),
        "--qa-agent-id", AGENT, "--qa-config-id", CONFIG,
        "--qa-config-version", "1", "--execution-kind", "ARCHIVED_REPLAY",
        "--team2-provenance", str(paths["sidecar"]),
        "--qa-pdf-receipt", str(paths["qa_receipt"]),
        "--operational-pdf-receipt", str(paths["op_receipt"]),
        "--pdf-root", str(tmp_path),
    )


def test_synthetic_original_pdf_sha_link_never_authenticates_live(tmp_path):
    paths, _ = make_synthetic_pdf_receipt_bundle(tmp_path)
    proc, result = invoke_with_synthetic_provenance(tmp_path, paths)
    assert proc.returncode == 2, proc.stderr
    assert result["python_business_status"] == "COMPLETED"
    assert result["python_safety_status"] == "PASS_LOCAL"
    assert result["provenance_link_status"] == "BLOCKED"
    assert result["same_original_pdf_bytes_verified"] is True
    assert result["actual_studio_e2e_status"] == "NOT_VERIFIED"
    assert result["release_or_merge_authorized"] is False


def test_wrong_operational_upload_file_id_blocks_source_binding(tmp_path):
    paths, payloads = make_synthetic_pdf_receipt_bundle(tmp_path)
    payloads["op_receipt"]["files"][0]["file_id"] = "file_WRONG"
    paths["op_receipt"].write_text(json.dumps(payloads["op_receipt"]), encoding="utf-8")
    proc, result = invoke_with_synthetic_provenance(tmp_path, paths)
    assert proc.returncode == 1, proc.stderr
    assert result["provenance_link_status"] == "FAIL"
    assert "OPERATION_NATIVE_UPLOAD_RECEIPT_MISMATCH" in {
        x["issue_code"] for x in result["issues"]
    }
    assert result["status"] == "FAIL"


def test_wrong_team2_native_sha_blocks_cross_job_provenance(tmp_path):
    paths, payloads = make_synthetic_pdf_receipt_bundle(tmp_path)
    payloads["sidecar"]["export_sha256"] = "0" * 64
    paths["sidecar"].write_text(json.dumps(payloads["sidecar"]), encoding="utf-8")
    proc, result = invoke_with_synthetic_provenance(tmp_path, paths)
    assert proc.returncode == 1, proc.stderr
    assert result["provenance_link_status"] == "FAIL"
    assert "OPERATION_NATIVE_SIDECAR_SHA_MISMATCH" in {
        x["issue_code"] for x in result["issues"]
    }


def test_incomplete_receipt_pair_cannot_claim_pdf_match(tmp_path):
    paths, _ = make_synthetic_pdf_receipt_bundle(tmp_path)
    proc, result = invoke("--team2-provenance", str(paths["sidecar"]))
    assert proc.returncode == 2, proc.stderr
    assert result["same_original_pdf_bytes_verified"] is False
    assert "PDF_PROVENANCE_EVIDENCE_SET_INCOMPLETE" in {
        x["issue_code"] for x in result["issues"]
    }
    assert result["status"] == "BLOCKED"



def test_three_document_c001_cannot_run_with_single_document_native(tmp_path):
    source = load_json_strict(OPERATING.read_bytes())
    docs = load_json_strict(source["content"])["documents"]
    source["content"] = json.dumps({"documents": docs[:1]})
    source["metadata"]["merge"]["items"] = source["metadata"]["merge"]["items"][:1]
    source["metadata"]["source_files"] = source["metadata"]["source_files"][:1]
    fake = tmp_path / "incomplete_c001_native.json"
    fake.write_text(json.dumps(source), encoding="utf-8")
    proc, result = invoke("--operational-native", str(fake))
    assert proc.returncode == 2, proc.stderr
    assert result["status"] == "BLOCKED"
    assert "python_summary" not in result
    assert result["python_business_status"] == "NOT_VERIFIED"
    assert result["single_case_grouping_status"] == "NOT_VERIFIED"
    assert "C001_NOT_SINGLE_THREE_DOCUMENT_JOB" in {
        x["issue_code"] for x in result["issues"]
    }


def test_source_pdf_filename_is_bound_to_native_file_id(tmp_path):
    paths, payloads = make_synthetic_pdf_receipt_bundle(tmp_path)
    payloads["op_receipt"]["files"][0]["filename"] = "UNRELATED.pdf"
    paths["op_receipt"].write_text(json.dumps(payloads["op_receipt"]), encoding="utf-8")
    proc, result = invoke_with_synthetic_provenance(tmp_path, paths)
    assert proc.returncode == 1, proc.stderr
    assert result["status"] == "FAIL"
    assert "OPERATION_NATIVE_UPLOAD_RECEIPT_MISMATCH" in {
        x["issue_code"] for x in result["issues"]
    }
    assert result["same_original_pdf_bytes_verified"] is False


def test_qa_native_one_document_does_not_satisfy_c001_handoff(tmp_path):
    source = load_json_strict(OPERATING.read_bytes())
    docs = load_json_strict(source["content"])["documents"]
    source["content"] = json.dumps({"documents": docs[:1]})
    source["metadata"]["merge"]["items"] = source["metadata"]["merge"]["items"][:1]
    source["metadata"]["source_files"] = source["metadata"]["source_files"][:1]
    qa_native = tmp_path / "synthetic_qa_native.json"
    qa_native.write_text(json.dumps(source), encoding="utf-8")
    qa_report = tmp_path / "synthetic_qa_report.json"
    qa_report.write_text(json.dumps({
        "case_id": "C001", "qa_status": "NOT_VERIFIED",
        "checked_document_ids": [docs[0]["document_id"]], "issues": [],
        "evidence_status": "PARTIAL", "recommended_action": "review",
        "workflow_version": "v1", "execution_provenance": None,
        "field_checks": [{"field": "po_id", "status": "SOURCE_NOT_VERIFIED"}],
    }), encoding="utf-8")
    proc, result = invoke(
        "--qa-native", str(qa_native), "--qa-report", str(qa_report),
        "--qa-agent-id", AGENT, "--qa-config-id", CONFIG,
        "--qa-config-version", "1", "--execution-kind", "ARCHIVED_REPLAY",
    )
    assert proc.returncode == 2, proc.stderr
    assert result["status"] == "BLOCKED"
    assert result["python_safety_status"] == "PASS_LOCAL"
    assert result["studio_document_status"] == "NOT_VERIFIED"
    assert "QA_C001_NATIVE_CASE_INCOMPLETE" in {
        x["issue_code"] for x in result["issues"]
    }
