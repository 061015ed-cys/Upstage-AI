"""Synthetic comparison manifests never stand in for actual Studio raw files."""
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from leadtime_guardian.qa.experiment_compare import (
    REQUIRED_STEPS,
    audit_b0_e1_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_b0_e1_compare_check.py"
REPORTED_B0 = ROOT / "data/observations/B0_C001_NCik_20261101_REPORTED_SINGLE_JOB.json"


def example(alias, job):
    return {
        "schema_version": "leadtime-experiment-compare/v1",
        "experiment": alias,
        "case_id": "C001", "single_case_job_count": 1,
        "job_id": job, "config_id": "cfg_SYNTHETIC",
        "config_version": 1, "saved_config_evidence": True,
        "source_pdfs": [
            {"filename": f"C001_{t}.pdf", "sha256": "a" * 64,
             "file_id": f"file_{alias}_{t}", "document_type": t}
            for t in ("purchase_order", "delivery_notice", "quotation")
        ],
        "step_artifacts": {
            t: {"step_run_id": f"step_{alias}_{t}", "original_sha256": "b" * 64}
            for t in REQUIRED_STEPS
        },
        "execution_conditions": {"workflow": "B0", "mode": "test"},
    }


def test_new_ncik_report_is_not_full_raw_b0_comparison_manifest():
    report = json.loads(REPORTED_B0.read_text())
    assert report["jobs"][0]["job_id"] == "job_NCik8shwrgM93PDnNNYukT"
    result = audit_b0_e1_readiness(
        report, example("E1", "job_SYNTHETIC_E1"),
    )
    assert result["eligibility"] == "FAIL"
    assert result["comparison_status"] == "NOT_MEASURED"
    assert result["accuracy"] == "NOT_MEASURED"


def test_even_complete_self_reported_manifests_do_not_authenticate_studio():
    b0 = example("B0", "job_SYNTHETIC_B0")
    e1 = example("E1", "job_SYNTHETIC_E1")
    baseline = deepcopy((b0, e1))
    output = audit_b0_e1_readiness(b0, e1)
    assert output["eligibility"] == "BLOCKED"
    assert output["pdf_sha256_sets_equal"] is True
    assert output["local_pdf_bytes_verified"] is False
    assert output["studio_job_authenticity_verified"] is False
    assert output["comparison_status"] == "NOT_MEASURED"
    assert output["null_and_zero_preservation"] == "NOT_MEASURED"
    assert output["qa_status_change"] == "NOT_MEASURED"
    assert output["release_or_merge_authorized"] is False
    assert (b0, e1) == baseline


def test_different_pdf_digests_fail_even_if_filenames_match():
    b0 = example("B0", "job_B0")
    e1 = example("E1", "job_E1")
    e1["source_pdfs"][0]["sha256"] = "c" * 64
    output = audit_b0_e1_readiness(b0, e1)
    assert output["eligibility"] == "FAIL"
    assert "B0_E1_PDF_SOURCE_MISMATCH" in {
        i["issue_code"] for i in output["issues"]
    }


def test_three_split_jobs_cannot_count_as_single_b0():
    b0 = example("B0", "job_B0")
    b0["single_case_job_count"] = 3
    result = audit_b0_e1_readiness(b0, example("E1", "job_E1"))
    assert result["eligibility"] == "BLOCKED"
    assert "SINGLE_CASE_JOB_NOT_CONFIRMED" in {
        i["issue_code"] for i in result["issues"]
    }


def test_cli_synthetic_pair_does_not_generate_accuracy_numbers(tmp_path):
    b0 = tmp_path / "b0.json"
    e1 = tmp_path / "e1.json"
    b0.write_text(json.dumps(example("B0", "job_B0")), encoding="utf-8")
    e1.write_text(json.dumps(example("E1", "job_E1")), encoding="utf-8")
    proc = subprocess.run([
        sys.executable, str(CLI), "--b0", str(b0), "--e1", str(e1),
    ], cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    result = json.loads(proc.stdout)
    assert proc.returncode == 2, proc.stderr
    assert result["comparison_status"] == "NOT_MEASURED"
    assert result["eligibility"] == "BLOCKED"
