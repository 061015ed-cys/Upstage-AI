"""Archived C001 integrity checks: actual files, but no new Studio inference."""
import json
import shutil
from pathlib import Path

import pytest

from leadtime_guardian.qa.archive import verify_c001_archive

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "data/results/studio_runs/C001_20261030_v4"


def isolated_archive(tmp_path):
    for source in (
        f"{PREFIX}/execution_record.json",
        f"{PREFIX}/analysis/run_metadata.json",
        f"{PREFIX}/analysis/analysis.json",
        "data/cases/SYN-C001/SYN-C001_delivery_notice.pdf",
        "data/cases/SYN-C001/SYN-C001_purchase_order.pdf",
        "data/cases/SYN-C001/SYN-C001_quotation.pdf",
    ):
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    return tmp_path


def test_actual_archived_c001_sha_and_metadata_pass():
    result = verify_c001_archive(ROOT)
    assert result["qa_status"] == "PASS"
    assert result["source_pdf_hashes_checked"] == 3
    assert result["evidence_type"] == "ARCHIVED_RECORD_ONLY"
    assert result["human_gold_accuracy"] is None
    assert result["live_studio_runs_started_by_this_audit"] == 0


def test_reject_tampered_pdf(tmp_path):
    root = isolated_archive(tmp_path)
    with (root / "data/cases/SYN-C001/SYN-C001_purchase_order.pdf").open("ab") as stream:
        stream.write(b"modified")
    report = verify_c001_archive(root)
    assert "PDF_HASH_MISMATCH" in {x["issue_code"] for x in report["issues"]}


@pytest.mark.parametrize(("filename", "field", "new_value", "expected"), [
    ("execution_record.json", "job_id", "job_fake", "JOB_ID_MISMATCH"),
    ("execution_record.json", "estimated_quote_cost_krw", "1.00", "COST_RECORD_MISMATCH"),
    ("execution_record.json", "human_gold_reviewed", True, "UNSUPPORTED_ACCURACY_OR_HUMAN_REVIEW"),
    ("execution_record.json", "external_procurement_action_taken", True, "EXTERNAL_ACTION_NOT_DISPROVEN"),
    ("analysis/analysis.json", "changed_shortage_quantity", 59, "QUANTITY_RECORD_MISMATCH"),
    ("analysis/run_metadata.json", "config_version", "cfg_fake", "CONFIG_ID_MISMATCH"),
])
def test_reject_tampered_metadata(tmp_path, filename, field, new_value, expected):
    root = isolated_archive(tmp_path)
    path = root / PREFIX / filename
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj[field] = new_value
    path.write_text(json.dumps(obj), encoding="utf-8")
    report = verify_c001_archive(root)
    assert expected in {x["issue_code"] for x in report["issues"]}


def test_missing_source_pdf_does_not_fake_pass(tmp_path):
    root = isolated_archive(tmp_path)
    (root / "data/cases/SYN-C001/SYN-C001_quotation.pdf").unlink()
    assert verify_c001_archive(root)["qa_status"] == "FAIL"
