"""Synthetic contract regressions. These are NOT Studio accuracy/integration runs."""
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from leadtime_guardian.studio_adapter import AdapterError
from leadtime_guardian.studio_integration import (
    analyze_studio_documents,
    documents_from_export,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inputs():
    case = json.loads((ROOT / "data/sample/portfolio_case.json").read_text(encoding="utf-8"))
    docs = deepcopy(case["documents"])
    for doc in docs:
        doc["warnings"] = []
        doc["original_delivery"] = "2026-11-03"
        doc["items"] = [{"product_id": "A", "receipt_id": "R1", "quantity": 100,
                         "unit": "EA"}]
    docs.append({"document_id": "QUOTE-DOC", "document_type": "quotation",
                 "po_id": "PO1", "supplier_id": "S1", "warnings": [],
                 "items": [{"product_id": "A", "receipt_id": None, "quantity": 60,
                            "unit": "EA"}],
                 "quote": {**case["quotes"][0], "currency": "KRW"}})
    docs[-1]["quote"].pop("supplier_risk")
    case["documents"] = []
    case["quotes"] = []
    case["inbound"][0]["eta"] = "2026-11-03"
    schema = json.loads((ROOT / "configs/schemas/document_extraction.schema.json")
                        .read_text(encoding="utf-8"))
    return case, docs, schema


def test_c001_uses_extracted_quote_and_existing_engine(inputs):
    base, docs, schema = inputs
    original = deepcopy(base)
    result = analyze_studio_documents(base, docs, schema)
    assert result["status"] == "OK"
    assert (result["baseline_shortage_quantity"], result["changed_shortage_quantity"],
            result["additional_shortage_quantity"]) == (0, 60, 60)
    assert result["estimated_quote_cost_krw"] == "60500.00"
    assert result["evidence_verified_against_pdf"] is False
    assert base == original


@pytest.mark.parametrize("mutation", [
    lambda d: d[1].update(po_id="PO-OTHER"),
    lambda d: d[1].update(revised_delivery=None),
    lambda d: d[1].update(original_delivery="2026-11-02"),
    lambda d: d[1]["items"][0].update(quantity=99),
    lambda d: d[1]["items"][0].update(quantity=-1),
    lambda d: d[1]["items"][0].update(unit="BOX"),
    lambda d: d[1].update(warnings=["uncertain date"]),
    lambda d: d[2]["quote"].update(currency="USD"),
    lambda d: d[2]["quote"].update(unit_price="NaN"),
    lambda d: d[2]["quote"].update(capacity=61),
    lambda d: d[2].update(po_id="PO-OTHER"),
    lambda d: d[2]["quote"].update(supplier_id="OTHER"),
    lambda d: d[0].update(unapproved_field="value"),
])
def test_unsafe_documents_block_calculation(inputs, mutation):
    base, docs, schema = inputs
    mutation(docs)
    result = analyze_studio_documents(base, docs, schema)
    assert result["status"] == "NEEDS_REVIEW"
    assert result["execution_status"] == "BLOCKED"
    assert result["changed_shortage_quantity"] is None
    assert result["supplier_options"] == []


def test_conflicting_notices_do_not_silently_use_last_date(inputs):
    base, docs, schema = inputs
    docs.append({**deepcopy(docs[1]), "document_id": "NOTICE-2",
                 "revised_delivery": "2026-11-09"})
    assert "duplicate/conflicting" in analyze_studio_documents(base, docs, schema)["review_flags"][0]


def test_ambiguous_partial_receipt_does_not_match(inputs):
    base, docs, schema = inputs
    base["inbound"].append({**base["inbound"][0], "receipt_id": "R2"})
    docs[1]["items"][0]["receipt_id"] = None
    assert analyze_studio_documents(base, docs, schema)["status"] == "NEEDS_REVIEW"


def test_quote_value_conflict_with_trusted_data_blocks(inputs):
    base, docs, schema = inputs
    base["quotes"] = [{**docs[2]["quote"], "unit_price": "999"}]
    assert analyze_studio_documents(base, docs, schema)["status"] == "NEEDS_REVIEW"


def test_native_documented_output_envelope(inputs):
    _, docs, _ = inputs
    raw = {"id": "job_SYNTHETIC", "status": "completed", "output": [
        {"type": "message", "status": "completed", "content": [
            {"type": "output_text", "text": json.dumps({"documents": docs})}]}]}
    assert documents_from_export(raw) == docs


def test_multiple_final_messages_require_observed_mapping():
    with pytest.raises(AdapterError, match="ambiguous"):
        documents_from_export({"id": "job_SYNTHETIC", "status": "completed", "output": [
            {"type": "message", "status": "completed", "content": [
                {"type": "output_text", "text": "[]"}]}] * 2})


def test_fixture_wrapper_cannot_be_ingested_as_prediction(inputs):
    with pytest.raises(AdapterError, match="gold/fixture"):
        documents_from_export({"provenance": "generator", "documents": inputs[1]})


def test_duplicate_po_facts_with_different_id_block(inputs):
    base, docs, schema = inputs
    docs.append({**deepcopy(docs[0]), "document_id": "PO-COPY"})
    assert "duplicate document facts" in analyze_studio_documents(base, docs, schema)["review_flags"][0]


def test_top_level_review_flag_is_not_lost(inputs):
    with pytest.raises(AdapterError, match="explicitly requires review"):
        documents_from_export({"needs_review": True, "documents": inputs[1]})


def test_malformed_export_archives_original_and_reports_blocked(tmp_path, inputs):
    raw = tmp_path / "invalid.json"
    raw.write_text("{malformed", encoding="utf-8")
    base = tmp_path / "base.json"
    base.write_text(json.dumps(inputs[0]), encoding="utf-8")
    out = tmp_path / "run"
    proc = subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_studio_export.py"),
        "--export", str(raw), "--base", str(base), "--output", str(out),
        "--run-id", "SYNTHETIC-CONTRACT-TEST", "--config-version", "test",
        "--prompt-version", "test"], capture_output=True, text=True, check=False)
    assert proc.returncode == 2
    assert (out / "studio_original.json").read_bytes() == raw.read_bytes()
    assert json.loads((out / "analysis.json").read_text())["execution_status"] == "BLOCKED"
    assert json.loads((out / "run_metadata.json").read_text())["run_id"] == "SYNTHETIC-CONTRACT-TEST"


@pytest.mark.parametrize("status", ["failed", "queued", "in_progress", "incomplete", "cancelled"])
def test_noncompleted_job_never_calculates(status):
    with pytest.raises(AdapterError, match="did not complete"):
        documents_from_export({"status": status, "documents": []})


def test_observed_native_instruct_envelope_preserves_predictions():
    documents = [{"document_id": "RAW-UNCHANGED", "warnings": ["retain this"]}]
    raw = {"content": json.dumps({"documents": documents}),
           "metadata": {"job_execution_id": "job_OBSERVED", "step_run_id": "step_OBSERVED"}}
    assert documents_from_export(raw) == documents


@pytest.mark.parametrize("change", [
    {"content": {}}, {"metadata": {}}, {"documents": []}, {"output_text": "{}"},
])
def test_native_instruct_missing_or_ambiguous_envelope_is_rejected(change):
    raw = {"content": '{"documents": []}',
           "metadata": {"job_execution_id": "job_TEST", "step_run_id": "step_TEST"}}
    raw.update(change)
    with pytest.raises(AdapterError):
        documents_from_export(raw)


def test_native_instruct_cannot_hide_gold_wrapper():
    raw = {"content": '{"human_reviewed": false, "documents": []}',
           "metadata": {"job_execution_id": "job_TEST", "step_run_id": "step_TEST"}}
    with pytest.raises(AdapterError, match="gold/fixture"):
        documents_from_export(raw)
