"""Replay archived C001 without claiming an additional live Studio run."""
import json
import shutil
from pathlib import Path

import pytest

from leadtime_guardian.qa.replay import verify_c001_replay

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "data/results/studio_runs/C001_20261030_v4"


def copy_inputs(tmp_path):
    sources = (
        "data/cases/SYN-C001/trusted_base_case.json",
        "data/cases/SYN-C001/SYN-C001_delivery_notice.pdf",
        "data/cases/SYN-C001/SYN-C001_purchase_order.pdf",
        "data/cases/SYN-C001/SYN-C001_quotation.pdf",
        "configs/schemas/document_extraction.schema.json",
        f"{PREFIX}/execution_record.json",
        f"{PREFIX}/analysis/run_metadata.json",
        f"{PREFIX}/analysis/studio_original.json",
        f"{PREFIX}/analysis/normalized_documents.json",
        f"{PREFIX}/analysis/analysis.json",
    )
    for source in sources:
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / source, target)
    return tmp_path


def test_archived_prediction_replays_exact_result():
    result = verify_c001_replay(ROOT)
    assert result["qa_status"] == "PASS", result
    assert result["mode"] == "ARCHIVED_REPLAY"
    assert result["live_studio_runs_started"] == 0
    assert result["human_verified_extraction_accuracy"] is None


@pytest.mark.parametrize(("filename", "field", "value", "code"), [
    ("analysis/run_metadata.json", "export_sha256", "0" * 64, "EXPORT_HASH_MISMATCH"),
    ("execution_record.json", "job_id", "job_tampered", "NATIVE_EXECUTION_ID_MISMATCH"),
    ("analysis/analysis.json", "estimated_quote_cost_krw", "1.00", "REPLAY_RESULT_MISMATCH"),
])
def test_replay_rejects_mutated_artifacts(tmp_path, filename, field, value, code):
    root = copy_inputs(tmp_path)
    path = root / PREFIX / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data[field] = value
    path.write_text(json.dumps(data), encoding="utf-8")
    report = verify_c001_replay(root)
    assert report["qa_status"] == "FAIL"
    assert code in {item["issue_code"] for item in report["issues"]}


def test_replay_rejects_tampered_normalized_prediction(tmp_path):
    root = copy_inputs(tmp_path)
    path = root / PREFIX / "analysis/normalized_documents.json"
    docs = json.loads(path.read_text(encoding="utf-8"))
    docs[1]["revised_delivery"] = "2026-11-09"
    path.write_text(json.dumps(docs), encoding="utf-8")
    report = verify_c001_replay(root)
    assert "NORMALIZED_DOCUMENT_MISMATCH" in {x["issue_code"] for x in report["issues"]}


def test_replay_fails_closed_when_original_missing(tmp_path):
    root = copy_inputs(tmp_path)
    (root / PREFIX / "analysis/studio_original.json").unlink()
    report = verify_c001_replay(root)
    assert report["qa_status"] == "FAIL"
    assert "UNREADABLE_REPLAY_INPUT" in {x["issue_code"] for x in report["issues"]}
