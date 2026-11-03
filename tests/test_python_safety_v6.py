"""Safety regressions; synthetic mutations are never measured Studio predictions."""
import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from leadtime_guardian.engine import analyze_portfolio
from leadtime_guardian.provenance import provenance_sidecar
from leadtime_guardian.strict_json import loads_strict
from leadtime_guardian.studio_adapter import AdapterError, apply_studio_extractions
from leadtime_guardian.studio_integration import analyze_studio_documents, documents_from_export

ROOT = Path(__file__).resolve().parents[1]
ACTUAL = ROOT / "data/results/studio_runs/C001_20261030_v4/instruct_original.json"
SCHEMA = loads_strict((ROOT / "configs/schemas/document_extraction.schema.json").read_bytes())


@pytest.fixture
def inputs():
    base = loads_strict((ROOT / "data/cases/SYN-C001/trusted_base_case.json").read_bytes())
    docs = documents_from_export(loads_strict(ACTUAL.read_bytes()))
    return base, docs


def assert_blocked(result):
    assert result["status"] == "NEEDS_REVIEW"
    assert result["execution_status"] == "BLOCKED"
    assert result["needs_review"] is True
    assert result["external_action_taken"] is False
    assert result["evidence_verified_against_pdf"] is False
    assert result["review_flags"]
    for key in ("baseline_shortage_quantity", "changed_shortage_quantity",
                "additional_shortage_quantity", "estimated_quote_cost_krw", "uncovered_quantity"):
        assert result[key] is None
    for key in ("delays", "impacted_orders", "supplier_options", "evidence_document_ids"):
        assert result[key] == []


def test_actual_c001_v4_prediction_replays_without_changes(inputs):
    base, docs = inputs
    before = ACTUAL.read_bytes()
    assert hashlib.sha256(before).hexdigest() == (
        "88387f8d6aee1421c9f628304c6b91811396b32da297d41b40e3d53c3d98dfea")
    original = deepcopy((base, docs))
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["status"] == "OK"
    assert result["execution_status"] == "COMPLETED"
    assert result["needs_review"] is False
    assert (result["baseline_shortage_quantity"], result["changed_shortage_quantity"],
            result["additional_shortage_quantity"]) == (0, 60, 60)
    assert Decimal(result["estimated_quote_cost_krw"]) == Decimal(60500)
    assert sum(line["quantity"] for line in result["supplier_options"]) == 60
    assert all(line["supplier_risk"] == "UNKNOWN" for line in result["supplier_options"])
    assert result["external_action_taken"] is False
    assert result["evidence_verified_against_pdf"] is False
    assert analyze_studio_documents(base, docs, SCHEMA) == result
    assert (base, docs) == original
    assert ACTUAL.read_bytes() == before


@pytest.mark.parametrize("text", [
    '{"documents":[],"documents":[{}]}', '{"x":{"a":1,"a":2}}',
    '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e309}',
    '{"x":01}', '{"x":+1}', '{"x":', '{"x":"\\ud800"}', b'{"x":"\xff"}',
])
def test_strict_json_rejects_unsafe_bytes_and_numbers(text):
    with pytest.raises((ValueError, UnicodeError)):
        loads_strict(text)


@pytest.mark.parametrize("wrapper", ["content", "output_text", "output"])
def test_inner_json_uses_the_same_strict_parser(wrapper):
    text = '{"documents": [], "documents": []}'
    raw = {wrapper: text}
    if wrapper == "content":
        raw["metadata"] = {"job_execution_id": "job_TEST", "step_run_id": "step_TEST"}
    elif wrapper == "output":
        raw.update(id="job_SYNTHETIC", status="completed")
        raw[wrapper] = [{"type": "message", "status": "completed",
                         "content": [{"type": "output_text", "text": text}]}]
    with pytest.raises(ValueError, match="duplicate"):
        documents_from_export(raw)


@pytest.mark.parametrize("raw", [
    {"documents": [], "output_text": "[]"},
    {"output": [], "output_text": "[]"}, {"documents": [], "content": "[]"},
    {"documents": {}, "status": "completed"}, {"documents": [], "human_reviewed": None},
    {"documents": [], "metadata": {}}, {"output": None}, {"output": "text"},
    {"output": [None]}, {"output": [{"type": "message", "status": "completed",
                                     "content": {"text": "[]"}}]},
    {"output": [{"type": "message", "status": "in_progress", "content": []}]},
    {"output": [{"type": "message", "status": "completed", "content": [None]}]},
    {"documents": [], "status": "unexpected"}, {"documents": [], "status": []},
    {"documents": [], "execution_status": "BLOCKED"},
    {"documents": [], "needs_review": "false"},
    {"documents": [], "review_flags": ["PO mismatch"]},
    {"output": [], "status": "completed"},
    {"output": [], "id": "job_T"},
    {"output_text": "[]", "id": "job_T", "status": "queued"},
    {"content": "[]", "metadata": {"job_execution_id": "job_", "step_run_id": "s"}},
    {"content": "[]", "metadata": {"job_execution_id": "job_T", "step_run_id": " "}},
    {"content": "[]", "metadata": {"job_execution_id": "job_T", "step_run_id": "s",
                                     "status": "failed"}},
])
def test_bad_envelope_cannot_fall_through_to_documents(raw):
    with pytest.raises(AdapterError):
        documents_from_export(raw)


def test_native_and_api_job_ids_must_match_run_id():
    raw = loads_strict(ACTUAL.read_bytes())
    with pytest.raises(AdapterError, match="job ID"):
        documents_from_export(raw, expected_job_id="job_DIFFERENT")
    with pytest.raises(AdapterError, match="job ID"):
        documents_from_export({"id": "job_OTHER", "status": "completed", "output_text": "[]"},
                              expected_job_id="job_EXPECTED")


@pytest.mark.parametrize("mutate", [
    lambda d: d[1].update(po_id="PO999"),
    lambda d: d[1]["items"][0].update(product_id="UNKNOWN"),
    lambda d: d[1]["items"][0].update(receipt_id="R999"),
    lambda d: d[1]["items"][0].update(receipt_id=""),
    lambda d: d[1].update(original_delivery=None),
    lambda d: d[1].update(revised_delivery=None),
    lambda d: d[1].update(revised_delivery="2026-02-30"),
    lambda d: d[1].update(revised_delivery="2026년 11월 8일"),
    lambda d: d[1]["items"][0].update(quantity=99),
    lambda d: d[1]["items"][0].update(quantity=-1),
    lambda d: d[1]["items"][0].update(quantity="100"),
    lambda d: d[1]["items"][0].update(quantity=True),
    lambda d: d[1]["items"][0].pop("quantity"),
    lambda d: d[0].update(document_id=" "),
    lambda d: d[0].update(document_type="unexpected"),
    lambda d: d.append(deepcopy(d[1])),
    lambda d: d.append({**deepcopy(d[1]), "document_id": "OTHER", "revised_delivery": "2026-11-09"}),
    lambda d: d[0]["items"].append(deepcopy(d[0]["items"][0])),
    lambda d: d[2]["quote"].update(capacity=59),
    lambda d: d[2]["quote"].update(currency="USD"),
    lambda d: d[2]["quote"].update(unit_price="NaN"),
    lambda d: d[2]["quote"].update(shipping_cost="Infinity"),
    lambda d: d[2]["quote"].update(unit_price=1.5),
    lambda d: d[2].update(warnings=["optional field evidence missing"]),
    lambda d: d[1].update(items=None),
    lambda d: d.__setitem__(0, None),
    lambda d: d[0].update(evidence=[{"confidence": float("nan")}]),
])
def test_synthetic_mutations_block_every_calculation_and_preserve_inputs(inputs, mutate):
    base, docs = inputs
    mutate(docs)
    before = deepcopy(base)
    assert_blocked(analyze_studio_documents(base, docs, SCHEMA))
    assert base == before
    assert base["inbound"][0]["eta"] == "2026-11-03"


@pytest.mark.parametrize("base", [None, [], {"case_id": "BAD"}, {"inbound": None}])
def test_malformed_trusted_input_returns_blocked_instead_of_crashing(base, inputs):
    assert_blocked(analyze_studio_documents(base, inputs[1], SCHEMA))


@pytest.mark.parametrize("key,value", [("unit_price", "999"), ("capacity", 59),
                                        ("currency", "USD"), ("shipping_cost", "501")])
def test_trusted_quote_conflicts_block(inputs, key, value):
    base, docs = inputs
    base["quotes"] = [{**docs[2]["quote"], "supplier_risk": "UNKNOWN", key: value}]
    assert_blocked(analyze_studio_documents(base, docs, SCHEMA))


def test_ambiguous_receipt_never_guesses_a_quantity_split(inputs):
    base, docs = inputs
    base["inbound"].append({**base["inbound"][0], "receipt_id": "R2"})
    docs[1]["items"][0]["receipt_id"] = None
    assert_blocked(analyze_studio_documents(base, docs, SCHEMA))


def test_notice_requires_corresponding_purchase_receipt(inputs):
    base, docs = inputs
    base["inbound"].append({**base["inbound"][0], "receipt_id": "R2"})
    docs[1]["items"][0]["receipt_id"] = "R2"
    assert_blocked(analyze_studio_documents(base, docs, SCHEMA))


def test_direct_mapping_does_not_use_last_conflicting_notice(inputs):
    base, docs = inputs
    docs.append({**deepcopy(docs[1]), "document_id": "COPY", "revised_delivery": "2026-11-09"})
    with pytest.raises(AdapterError, match="duplicate/conflicting"):
        apply_studio_extractions(base, docs)
    assert base["inbound"][0]["eta"] == "2026-11-03"


@pytest.mark.parametrize("number,shortage,gap,cost", [
    (2, 0, 0, "0"), (3, 60, 0, "60500"), (4, 0, 0, "0"), (5, 0, 0, "0"),
    (6, 0, 0, "0"), (7, 20, 0, "20500"), (8, 40, 0, "40500"),
    (9, 80, 20, "60500"), (10, 60, 60, "0"), (11, 60, 40, "20500"),
    (12, 60, 0, "72500"), (17, 60, 0, "60500"), (19, 60, 60, "0"),
])
def test_draft_synthetic_normalized_cases_only(number, shortage, gap, cost):
    folder = ROOT / f"data/cases/SYN-C{number:03}"
    base = loads_strict((folder / "trusted_base_case.json").read_bytes())
    draft = loads_strict((folder / "extraction_gold.DRAFT.json").read_bytes())
    assert draft["human_reviewed"] is False
    with pytest.raises(AdapterError, match="gold/fixture"):
        documents_from_export(draft)
    # Direct fixture access is intentional for synthetic unit tests, never an export ingest.
    result = analyze_studio_documents(base, draft["documents"], SCHEMA)
    assert result["status"] == "OK"
    assert result["changed_shortage_quantity"] == shortage
    assert result["uncovered_quantity"] == gap
    assert Decimal(result["estimated_quote_cost_krw"]) == Decimal(cost)
    assert result["evidence_verified_against_pdf"] is False
    if number == 8:
        updated = apply_studio_extractions(base, draft["documents"])
        assert [r["eta"] for r in updated["inbound"]] == ["2026-11-03", "2026-11-08"]
        assert [o["shortage_quantity"] for o in result["impacted_orders"]] == [0, 40]


@pytest.mark.parametrize("number", [13, 14, 15, 16, 18, 20])
def test_draft_synthetic_conflicts_are_blocked(number):
    folder = ROOT / f"data/cases/SYN-C{number:03}"
    base = loads_strict((folder / "trusted_base_case.json").read_bytes())
    docs = loads_strict((folder / "extraction_gold.DRAFT.json").read_bytes())["documents"]
    before = deepcopy((base, docs))
    assert_blocked(analyze_studio_documents(base, docs, SCHEMA))
    assert (base, docs) == before


def test_provenance_keeps_supplied_metadata_and_empty_evidence_unverified(inputs):
    base, docs = inputs
    raw = loads_strict(ACTUAL.read_bytes())
    sidecar = provenance_sidecar(raw, docs, analyze_studio_documents(base, docs, SCHEMA),
                                 hashlib.sha256(ACTUAL.read_bytes()).hexdigest())
    assert sidecar["studio_metadata_supplied"] == raw["metadata"]
    assert sidecar["evidence_verified_against_pdf"] is False
    assert all(d["evidence_status"] == "ABSENT" for d in sidecar["documents"])
    assert "config_id" not in sidecar  # No observed ID is invented from the config-version label.


@pytest.mark.parametrize("kind", ["bad_encoding", "duplicate", "bad_base", "wrong_job"])
def test_cli_archives_failures_with_complete_blocked_contract(tmp_path, inputs, kind):
    export = tmp_path / "source.json"
    base = tmp_path / "base.json"
    base.write_text(json.dumps(inputs[0]), encoding="utf-8")
    data = ACTUAL.read_bytes()
    if kind == "bad_encoding":
        data = b'{"documents":"\xff"}'
    elif kind == "duplicate":
        data = b'{"documents":[],"documents":[]}'
    elif kind == "bad_base":
        base.write_text('{"inbound":', encoding="utf-8")
    export.write_bytes(data)
    target = tmp_path / "result"
    proc = subprocess.run([
        sys.executable, str(ROOT / "scripts/analyze_studio_export.py"),
        "--export", str(export), "--base", str(base), "--output", str(target),
        "--run-id", "job_WRONG", "--config-version", "test", "--prompt-version", "test",
    ], capture_output=True, check=False)
    assert proc.returncode == 2, proc.stderr
    assert_blocked(loads_strict((target / "analysis.json").read_bytes()))
    assert (target / "studio_original.json").read_bytes() == data == export.read_bytes()
    metadata = loads_strict((target / "run_metadata.json").read_bytes())
    assert metadata["export_sha256"] == hashlib.sha256(data).hexdigest()
    assert (target / "provenance.json").is_file()


def test_engine_rejects_non_krw_quote_in_direct_offline_input():
    case = loads_strict((ROOT / "data/sample/portfolio_case.json").read_bytes())
    case["quotes"][0]["currency"] = "USD"
    assert_blocked(analyze_portfolio(case))


def test_multiple_quotes_share_capacity_and_charge_each_shipping_once(inputs):
    base, docs = inputs
    base["orders"] = [{"order_id": f"O{i}", "product_id": "A", "due_date": "2026-11-05",
                       "quantity": 50} for i in range(1, 4)]
    extra = deepcopy(docs[2])
    extra["document_id"] = "QUOTE-2"
    extra["quote"].update(quote_id="Q2", supplier_id="S2", capacity=30,
                           unit_price="1100.01", shipping_cost="250.25")
    extra["supplier_id"] = "S2"
    extra["items"][0]["quantity"] = 30
    docs.append(extra)
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["status"] == "OK"
    assert result["changed_shortage_quantity"] == 110
    assert result["uncovered_quantity"] == 20
    assert Decimal(result["estimated_quote_cost_krw"]) == Decimal("93750.55")
    assert sum(row["quantity"] for row in result["supplier_options"] if row["quote_id"] == "Q1") == 60
    assert sum(row["quantity"] for row in result["supplier_options"] if row["quote_id"] == "Q2") == 30


def test_supplied_evidence_is_preserved_without_inventing_pdf_verification(inputs):
    base, docs = inputs
    evidence = {"source_page": 1, "source_field": "original_delivery",
                "source_value": "2026년 11월 3일", "confidence": 0.8}
    docs[0]["evidence"] = [evidence]
    original = deepcopy(docs)
    result = analyze_studio_documents(base, docs, SCHEMA)
    assert result["status"] == "OK"
    sidecar = provenance_sidecar({}, docs, result, "synthetic-hash")
    assert sidecar["documents"][0]["evidence_status"] == "SUPPLIED_UNVERIFIED"
    assert sidecar["documents"][0]["evidence_supplied"] == [evidence]
    assert sidecar["evidence_verified_against_pdf"] is False
    assert docs == original
