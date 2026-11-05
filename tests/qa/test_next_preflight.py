"""Synthetic, local-only safety regressions; no official evidence here."""
import hashlib
import json
import zipfile

from qa.intake_preflight import inspect as intake
from qa.submission_preflight import inspect as submission


def dump(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_intake_missing_and_malformed(tmp_path):
    manifest = tmp_path / "intake.json"
    dump(manifest, {"case_id": "C001", "job_id": "job_1", "artifacts": {}})
    report = intake(manifest)
    assert report["status"] == "BLOCKED"
    assert "studio_native:NOT_PROVIDED" in report["blocking_reasons"]
    assert report["official_metrics_eligible"] is False
    source = tmp_path / "draft.json"
    source.write_bytes(b"{}")
    dump(manifest, {"case_id": "C001", "job_id": "job_1", "artifacts": {
        "frozen_gold": {"path": "draft.json", "sha256": "0" * 64}}})
    report = intake(manifest)
    assert report["status"] == "FAIL"
    assert any("frozen_gold" in x for x in report["failures"])


def test_intake_rejects_draft_mixed_job_bad_xlsx_and_sidecar(tmp_path):
    artifacts = {}
    payloads = {
        "reviewed_xlsx": b"not-xlsx", "baseline_csv": b"case_id\n",
        "human_review_record": b"{}", "team_approval_record": b"{}",
        "frozen_gold": json.dumps({"case_id": "SYN-OTHER", "label_status": "AI_CANDIDATE",
                                   "approval_provenance": {}}).encode(),
        "studio_native": b"{}",
        "native_binding": json.dumps({"case_id": "OTHER", "job_id": "job_other"}).encode(),
        "execution_record": b"{}",
        "v6_sidecar": json.dumps({"export_sha256": "0" * 64}).encode(),
    }
    for name, raw in payloads.items():
        (tmp_path / name).write_bytes(raw)
        artifacts[name] = {"path": name, "sha256": hashlib.sha256(raw).hexdigest()}
    manifest = tmp_path / "intake.json"
    dump(manifest, {"case_id": "C001", "job_id": "job_1", "artifacts": artifacts})
    report = intake(manifest)
    assert report["status"] == "FAIL"
    assert "XLSX_REVIEW_CONTRACT_FAILED" in report["failures"] or any(
        x.startswith("INVALID_INPUT:") for x in report["failures"])
    assert "FROZEN_GOLD_NOT_APPROVED" in report["failures"]
    assert "APPROVED_FIELD_EVIDENCE_INVALID" in report["failures"]
    assert "CASE_OR_JOB_MISMATCH" in report["failures"]
    assert "SIDECAR_NATIVE_SHA_MISMATCH" in report["failures"]
    assert "NATIVE_CONTRACT_FAILED" in report["failures"]
    assert "EXECUTION_IDENTITY_MISMATCH" in report["failures"]
    review_csv = b"invalid-header\n"
    (tmp_path / "review.csv").write_bytes(review_csv)
    artifacts["human_review_record"] = {
        "path": "review.csv", "sha256": hashlib.sha256(review_csv).hexdigest()}
    dump(manifest, {"case_id": "C001", "job_id": "job_1", "artifacts": artifacts})
    assert "HUMAN_REVIEW_CONTRACT_FAILED" in intake(manifest)["failures"]


def test_submission_missing_sha_and_sensitive(tmp_path):
    candidate = tmp_path / "package"
    candidate.mkdir()
    (candidate / "report.txt").write_bytes(b"safe")
    manifest = tmp_path / "manifest.json"
    dump(manifest, {"files": [{"path": "report.txt", "sha256": "0" * 64,
                                "size_bytes": 4}],
                    "required_evidence_references": ["report.txt"]})
    assert "CONTENT_MISMATCH:report.txt" in submission(candidate, manifest)["blockers"]
    (candidate / "raw_native.json").write_bytes(b"{}")
    raw = b"{}"
    dump(manifest, {"files": [
        {"path": "report.txt", "sha256": hashlib.sha256(b"safe").hexdigest(),
         "size_bytes": 4},
        {"path": "raw_native.json", "sha256": hashlib.sha256(raw).hexdigest(),
         "size_bytes": 2}], "required_evidence_references": ["report.txt"]})
    assert "SENSITIVE_FILE_UNAPPROVED:raw_native.json" in submission(candidate, manifest)["blockers"]


def test_submission_blocks_secret_content(tmp_path):
    candidate = tmp_path / "package"
    candidate.mkdir()
    raw = b"OPENAI_API_KEY=example-only"
    (candidate / "notes.txt").write_bytes(raw)
    manifest = tmp_path / "manifest.json"
    dump(manifest, {"files": [{"path": "notes.txt",
                                "sha256": hashlib.sha256(raw).hexdigest(),
                                "size_bytes": len(raw)}],
                    "required_evidence_references": ["notes.txt"]})
    assert "SECRET_CONTENT_DETECTED:notes.txt" in submission(candidate, manifest)["blockers"]


def test_submission_zip_duplicate_and_precheck_only(tmp_path):
    archive = tmp_path / "candidate.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("report.txt", "safe")
        z.writestr("report.txt", "safe")
    manifest = tmp_path / "manifest.json"
    dump(manifest, {"files": [{"path": "report.txt",
                                "sha256": hashlib.sha256(b"safe").hexdigest(),
                                "size_bytes": 4}],
                    "required_evidence_references": ["report.txt"]})
    assert "DUPLICATE_ZIP_PATH" in submission(archive, manifest)["blockers"]
    archive.unlink()
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("report.txt", "safe")
    report = submission(archive, manifest)
    assert report["status"] == "PRECHECK_ONLY"
    assert report["submission_authorized"] is False


def test_submission_rejects_unsafe_zip_directory(tmp_path):
    archive = tmp_path / "candidate.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../escape/", b"")
        z.writestr("report.txt", b"safe")
    manifest = tmp_path / "manifest.json"
    dump(manifest, {"files": [{"path": "report.txt",
                                "sha256": hashlib.sha256(b"safe").hexdigest(),
                                "size_bytes": 4}],
                    "required_evidence_references": ["report.txt"]})
    report = submission(archive, manifest)
    assert report["status"] == "FAIL"
    assert "UNSAFE_ZIP_ENTRY" in report["blockers"]


def test_submission_rejects_empty_public_approval_reference(tmp_path):
    candidate = tmp_path / "package"
    candidate.mkdir()
    raw = b"{}"
    (candidate / "raw_native.json").write_bytes(raw)
    manifest = tmp_path / "manifest.json"
    dump(manifest, {"files": [{"path": "raw_native.json",
                                "sha256": hashlib.sha256(raw).hexdigest(),
                                "size_bytes": len(raw)}],
                    "required_evidence_references": ["raw_native.json"],
                    "approved_sensitive_paths": ["raw_native.json"],
                    "public_approval_reference": ""})
    report = submission(candidate, manifest)
    assert report["status"] == "FAIL"
    assert "PUBLIC_APPROVAL_REFERENCE_MISSING" in report["blockers"]
