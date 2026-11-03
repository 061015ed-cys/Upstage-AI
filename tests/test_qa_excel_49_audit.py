"""Minimal in-memory XLSX fixtures; no claim about user's unavailable Excel."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from leadtime_guardian.qa.audit import load_json_strict

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_excel_49_audit.py"


def test_excel_49_numeric_string_and_other_values_stay_distinct(tmp_path):
    workbook = tmp_path / "test.xlsx"
    content = """<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="n"><v>49</v></c>
<c r="B1" t="s"><v>0</v></c>
<c r="C1" t="n"><v>48</v></c>
<c r="D1" t="inlineStr"><is><t>49</t></is></c>
<c r="E1" t="b"><v>1</v></c></row>
</sheetData></worksheet>"""
    ss = """<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<si><t>49</t></si></sst>"""
    with zipfile.ZipFile(workbook, "w") as bundle:
        bundle.writestr("xl/worksheets/sheet1.xml", content)
        bundle.writestr("xl/sharedStrings.xml", ss)
    extract = tmp_path / "extract.json"
    extract.write_text(json.dumps({"n": 49, "s": "49", "other": None}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(CLI), "--xlsx", str(workbook),
         "--extract-json", str(extract)],
        capture_output=True, text=True, cwd=ROOT, check=False, timeout=30,
    )
    assert proc.returncode == 2, proc.stderr
    out = load_json_strict(proc.stdout)
    assert out["xlsx_49_count"] == 3
    assert {item["match_type"] for item in out["xlsx_matches"]} == {
        "NUMBER_49", "STRING_49",
    }
    assert out["causal_origin"] == "UNKNOWN"
    assert len(out["stage_evidence"]["Extract"]["matches"]) == 2
    assert out["stage_evidence"]["Merge"]["status"] == "NOT_PROVIDED"


def test_invalid_xlsx_fails_closed(tmp_path):
    workbook = tmp_path / "bad.xlsx"
    workbook.write_bytes(b"not an XLSX")
    proc = subprocess.run(
        [sys.executable, str(CLI), "--xlsx", str(workbook)],
        capture_output=True, text=True, cwd=ROOT, check=False, timeout=30,
    )
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["qa_status"] == "FAIL"


def test_formula_cached_49_is_not_a_literal_number(tmp_path):
    workbook = tmp_path / "formula.xlsx"
    with zipfile.ZipFile(workbook, "w") as bundle:
        bundle.writestr("xl/worksheets/sheet1.xml",
                        '<?xml version="1.0"?><worksheet '
                        'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                        '<sheetData><row r="1"><c r="A1" t="n">'
                        '<f>7*7</f><v>49</v></c></row></sheetData></worksheet>')
    result = subprocess.run([sys.executable, str(CLI), "--xlsx", str(workbook)],
                            capture_output=True, text=True, check=False,
                            cwd=ROOT, timeout=30)
    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["xlsx_49_count"] == 1
    match = data["xlsx_matches"][0]
    assert match["match_type"] == "FORMULA_CACHED_49"
    assert match["formula_expression"] == "7*7"
    assert match["has_formula"] is True
    assert data["causal_origin"] == "UNKNOWN"



def test_excel_49_row_context_does_not_invent_json_mapping(tmp_path):
    workbook = tmp_path / "synthetic_context.xlsx"
    xml = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main"><sheetData>'
        '<row r="1"><c r="C1" t="inlineStr"><is><t>Quantity'
        '</t></is></c></row>'
        '<row r="2"><c r="B2" t="inlineStr"><is><t>PO1</t></is></c>'
        '<c r="C2" t="n"><v>49</v></c>'
        '<c r="D2" t="n"><v>100</v></c></row>'
        '</sheetData></worksheet>'
    )
    with zipfile.ZipFile(workbook, "w") as bundle:
        bundle.writestr("xl/worksheets/sheet1.xml", xml)
    proc = subprocess.run(
        [sys.executable, str(CLI), "--xlsx", str(workbook)],
        capture_output=True, text=True, check=False, cwd=ROOT, timeout=30,
    )
    result = json.loads(proc.stdout)
    assert proc.returncode == 2, proc.stderr
    match = result["xlsx_matches"][0]
    assert match["cell"] == "C2"
    assert match["column_header_row1_candidate"] == "Quantity"
    assert match["potential_header_cells_above"] == [
        {"cell": "C1", "value": "Quantity"},
    ]
    assert match["same_row_context_unverified"] == {
        "B2": "PO1", "D2": "100",
    }
    assert match["json_field_mapping_verified"] is False
    assert result["causal_origin"] == "UNKNOWN"
