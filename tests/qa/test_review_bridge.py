"""Synthetic review workbook tests; none are a human approval."""
import csv
import io

import pytest

from qa.review_bridge import inspect_xlsx_review, parse_candidate


@pytest.fixture
def book():
    pytest.importorskip("defusedxml")
    lib = pytest.importorskip("openpyxl")
    result = lib.Workbook()
    yield result
    result.close()


def sample(book, value=0, edits=None):
    row = {
        "document_id": "D", "source_filename": "doc.pdf", "page": "1",
        "field_path": "items[0].quantity", "normalized_candidate": "0",
        "value_type": "integer", "source_text": "0", "location": "table",
        "evidence_kind": "cell", "draft_match": "AI_COMPARE_MATCH",
        "review_reason": "", "reviewer": "", "reviewed_at": "",
        "decision": "", "approval_state": "PENDING"}
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(row), lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    row["page"] = 1
    row["normalized_candidate"] = value
    row.update(edits or {})
    sheet = book.active
    sheet.append(list(row))
    sheet.append(list(row.values()))
    xlsx = io.BytesIO()
    book.save(xlsx)
    return out.getvalue().encode(), xlsx.getvalue()


def test_explicit_typed_parse():
    assert parse_candidate("0", "integer") == 0
    assert parse_candidate("001", "string") == "001"
    assert parse_candidate("null", "null") is None
    with pytest.raises(ValueError):
        parse_candidate("001", "integer")
    with pytest.raises(ValueError):
        parse_candidate("0", "null")


def test_xlsx_match_never_human_promotes(book):
    csv_bytes, xlsx = sample(book)
    report = inspect_xlsx_review(xlsx, csv_bytes)
    assert report["status"] == "PASS"
    assert report["expected_rows"] == 1
    assert report["gold_promoted"] is False
    assert report["official_metrics_eligible"] is False


def test_xlsx_string_zero_type_mismatch(book):
    csv_bytes, xlsx = sample(book, value="000")
    report = inspect_xlsx_review(xlsx, csv_bytes)
    assert report["status"] == "BLOCKED"
    assert "BASELINE_TYPE_OR_VALUE_MISMATCH" in {i["code"] for i in report["issues"]}


def test_claimed_team_approval_not_verified(book):
    csv_bytes, xlsx = sample(book, edits={
        "reviewer": "SYNTHETIC", "reviewed_at": "2026-11-02T11:00:00+09:00",
        "decision": "ACCEPT", "approval_state": "TEAM_APPROVED"})
    report = inspect_xlsx_review(xlsx, csv_bytes)
    assert report["claimed_accept_rows"] == 1
    assert report["team_approval_verified"] is False
    assert report["gold_promoted"] is False


def test_duplicate_header_rejected(book):
    csv_bytes, _ = sample(book)
    book.active["B1"] = "document_id"
    data = io.BytesIO()
    book.save(data)
    with pytest.raises(ValueError, match="duplicate"):
        inspect_xlsx_review(data.getvalue(), csv_bytes)


def test_formula_rejected(book):
    csv_bytes, _ = sample(book)
    book.active["E2"] = "=1+1"
    data = io.BytesIO()
    book.save(data)
    assert inspect_xlsx_review(data.getvalue(), csv_bytes)["status"] == "BLOCKED"



def test_explicit_null_token_not_excel_blank(book):
    import csv
    csv_bytes, _ = sample(book)
    parsed = list(csv.DictReader(io.StringIO(csv_bytes.decode())))
    parsed[0]["normalized_candidate"] = "null"
    parsed[0]["value_type"] = "null"
    parsed[0]["source_text"] = ""
    text = io.StringIO()
    writer = csv.DictWriter(text, fieldnames=list(parsed[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(parsed)
    book.active["E2"] = "null"
    book.active["F2"] = "null"
    book.active["G2"] = None
    payload = io.BytesIO()
    book.save(payload)
    report = inspect_xlsx_review(payload.getvalue(), text.getvalue().encode())
    assert report["status"] == "BLOCKED"
    assert "ABSENCE_EVIDENCE_REQUIRES_HUMAN_REVIEW" in {
        i["code"] for i in report["issues"]}
    # Removing the explicit null token must also be detected.
    book.active["E2"] = None
    payload2 = io.BytesIO()
    book.save(payload2)
    bad = inspect_xlsx_review(payload2.getvalue(), text.getvalue().encode())
    assert "BASELINE_TYPE_OR_VALUE_MISMATCH" in {
        i["code"] for i in bad["issues"]}


def test_team_approved_without_accept_is_inconsistent(book):
    csv_bytes, xlsx = sample(book, edits={"approval_state": "TEAM_APPROVED"})
    report = inspect_xlsx_review(xlsx, csv_bytes)
    assert report["status"] == "BLOCKED"
    assert "APPROVAL_WITHOUT_ACCEPT" in {x["code"] for x in report["issues"]}
