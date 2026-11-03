"""A raw shared-string reference <v>49</v> does NOT mean literal '49'.

Synthetic OOXML reproduces the 22 coordinate pattern, NOT the user's XLSX.
The original XLSX is never committed to GitHub.
"""
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from leadtime_guardian.qa.audit import load_json_strict

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/qa_excel_49_audit.py"
COORDINATES = (
    "R2", "T2", "Y2", "Z2", "AA2", "AB2", "AC2", "AD2", "AE2", "AF2",
    "R3", "Y3", "Z3", "AA3", "AB3", "AC3", "AD3", "AE3", "AF3",
    "S4", "T4", "V4",
)
HEADERS = {
    "R": "supplier_id", "S": "original_delivery",
    "T": "revised_delivery", "V": "items.receipt_id",
    "Y": "quote.quote_id", "Z": "quote.supplier_id",
    "AA": "quote.product_id", "AB": "quote.capacity",
    "AC": "quote.arrival_date", "AD": "quote.unit_price",
    "AE": "quote.shipping_cost", "AF": "quote.currency",
}


def make_fixture(path, *, at49=""):
    # Exactly fifty sharedString entries. Ref 49 points to blank, NOT "49".
    shared = [
        f"<si><t>unused_{n}</t></si>" for n in range(49)
    ] + [f"<si><t>{escape(at49)}</t></si>"]
    names = [
        f'<c r="{col}1" t="inlineStr"><is><t>{escape(name)}</t></is></c>'
        for col, name in HEADERS.items()
    ]
    cells = [
        f'<c r="{coord}" t="s"><v>49</v></c>' for coord in COORDINATES
    ]
    numeric = [
        '<c r="W2" t="n"><v>100</v></c>',
        '<c r="AB4" t="n"><v>60</v></c>',
    ]
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    worksheet = (
        f'<worksheet xmlns="{ns}"><sheetData>'
        + "".join(f'<row r="{row}">'
                  + "".join(x for x in (names + cells + numeric)
                            if any(f'r="{col}{row}"' in x for col in (
                                "R", "S", "T", "V", "W", "Y", "Z",
                                "AA", "AB", "AC", "AD", "AE", "AF",
                            )))
                  + "</row>" for row in (1, 2, 3, 4))
        + "</sheetData></worksheet>"
    )
    with zipfile.ZipFile(path, "w") as output:
        output.writestr(
            "xl/sharedStrings.xml",
            f'<sst xmlns="{ns}">' + "".join(shared) + "</sst>",
        )
        output.writestr("xl/worksheets/sheet1.xml", worksheet)


def run(path):
    proc = subprocess.run(
        [sys.executable, str(CLI), "--xlsx", str(path)],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=30,
    )
    return proc, load_json_strict(proc.stdout)


def test_all_22_pointer_49_cells_are_resolved_blank_not_string_49(tmp_path):
    workbook = tmp_path / "synthetic_22_blank_shared_indexes.xlsx"
    make_fixture(workbook)
    proc, result = run(workbook)
    assert proc.returncode == 2, proc.stderr
    assert result["xlsx_49_count"] == 0
    assert result["shared_index_49_reference_count"] == 22
    assert result["shared_index_49_resolved_blank_count"] == 22
    assert result["shared_index_49_resolved_string_49_count"] == 0
    assert {x["cell"] for x in result["shared_index_49_references"]} == set(
        COORDINATES
    )
    row_counts = {
        n: sum(x["cell"].endswith(str(n))
               for x in result["shared_index_49_references"])
        for n in (2, 3, 4)
    }
    assert row_counts == {2: 10, 3: 9, 4: 3}
    assert next(x for x in result["shared_index_49_references"]
                if x["cell"] == "AB2")["header_row1"] == "quote.capacity"
    assert result["causal_origin"] == "UNKNOWN"
    assert result["source_pdf_verified"] is False
    assert result["original_files_modified"] is False


def test_real_shared_string_at_index49_is_identified_as_string49(tmp_path):
    file = tmp_path / "synthetic_literal_49.xlsx"
    make_fixture(file, at49="49")
    proc, output = run(file)
    assert proc.returncode == 2, proc.stderr
    assert output["xlsx_49_count"] == 22
    assert output["shared_index_49_resolved_string_49_count"] == 22
    assert output["shared_index_49_resolved_blank_count"] == 0
    assert {x["match_type"] for x in output["xlsx_matches"]} == {"STRING_49"}


def test_duplicate_shared_string_index_does_not_change_numeric_quantities(tmp_path):
    file = tmp_path / "synthetic_quantities.xlsx"
    make_fixture(file)
    proc, output = run(file)
    assert proc.returncode == 2
    assert output["shared_index_49_reference_count"] == 22
    assert output["xlsx_49_count"] == 0
    assert output["xlsx_cell_interpretation_status"] == "VERIFIED_OOXML_SHARED_STRINGS"


def test_malformed_shared_index_49_fails_closed(tmp_path):
    file = tmp_path / "synthetic_missing_shared_entry.xlsx"
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    with zipfile.ZipFile(file, "w") as z:
        z.writestr("xl/sharedStrings.xml",
                   f'<sst xmlns="{ns}"><si><t>only one</t></si></sst>')
        z.writestr("xl/worksheets/sheet1.xml",
                   f'<worksheet xmlns="{ns}"><sheetData><row r="2">'
                   '<c r="R2" t="s"><v>49</v></c>'
                   '</row></sheetData></worksheet>')
    proc, out = run(file)
    assert proc.returncode == 1
    assert out["qa_status"] == "FAIL"
