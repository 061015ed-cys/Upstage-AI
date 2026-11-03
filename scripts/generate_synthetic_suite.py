"""Create C002-C020 synthetic DRAFT cases; never regenerate the existing C001 PDFs."""
import argparse
import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
TYPES = ["baseline", "minor delay", "late delivery", "enough stock", "equal ETA", "early ETA",
         "two orders", "partial arrival", "two products", "late quote", "limited quote",
         "premium quote", "mismatched PO", "missing ETA", "missing quantity", "unknown product",
         "Korean date", "duplicate PO reference", "supplier unavailable", "contradictory wording"]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def case_spec(number):
    case = json.loads((ROOT / "data/cases/SYN-C001/trusted_base_case.json").read_text())
    case["case_id"] = f"SYN-C{number:03}"
    revised, price, capacity, arrival = "2026-11-08", "1000.00", 60, "2026-11-04"
    if number == 2:
        revised = "2026-11-04"
    elif number == 3:
        revised = "2026-11-12"
    elif number == 4:
        case["inventory"][0]["available_stock"] = 120
    elif number == 5:
        revised = "2026-11-05"
    elif number == 6:
        revised = "2026-11-02"
    elif number == 7:
        case["orders"] = [{"order_id": "O1", "product_id": "A", "due_date": "2026-11-05",
                           "quantity": 60}, {"order_id": "O2", "product_id": "A",
                           "due_date": "2026-11-09", "quantity": 70}]
    elif number == 8:
        case["inventory"][0]["available_stock"] = 20
        case["inbound"][0]["quantity"] = 40
        case["inbound"].append({**case["inbound"][0], "receipt_id": "R2", "quantity": 60})
        case["orders"] = [{"order_id": "O1", "product_id": "A", "due_date": "2026-11-05",
                           "quantity": 50}, {"order_id": "O2", "product_id": "A",
                           "due_date": "2026-11-06", "quantity": 50}]
    elif number == 9:
        case["inventory"].append({"product_id": "B", "available_stock": 10})
        case["orders"].append({"order_id": "OB", "product_id": "B",
                               "due_date": "2026-11-05", "quantity": 30})
        case["inbound"].append({**case["inbound"][0], "receipt_id": "RB",
                                "product_id": "B", "quantity": 30})
    elif number == 10:
        arrival = "2026-11-07"
    elif number == 11:
        capacity = 20
    elif number == 12:
        price = "1200.00"
    elif number == 18:
        case["inbound"][0]["quantity"] = 50
        case["inbound"].append({**case["inbound"][0], "receipt_id": "R2"})
    elif number == 19:
        capacity = 0
    base_item = lambda r: {"product_id": r["product_id"], "receipt_id": r["receipt_id"],
                           "quantity": r["quantity"], "unit": "EA"}
    shared = {"po_id": "PO1", "supplier_id": None, "original_delivery": "2026-11-03",
              "revised_delivery": None, "quote": None, "warnings": [], "evidence": []}
    po = {**deepcopy(shared), "document_id": f"C{number:03}-PO", "document_type": "purchase_order",
          "items": [base_item(r) for r in case["inbound"]]}
    affected = case["inbound"][1:] if number == 8 else case["inbound"]
    notice = {**deepcopy(shared), "document_id": f"C{number:03}-NOTICE",
              "document_type": "delivery_notice", "revised_delivery": revised,
              "items": [base_item(r) for r in affected]}
    if number == 13:
        notice["po_id"] = "PO999"
    elif number == 14:
        notice["revised_delivery"] = None
    elif number == 15:
        notice["items"][0]["quantity"] = None
    elif number == 16:
        notice["items"][0]["product_id"] = "UNKNOWN-X"
    elif number == 18:
        notice["items"] = [{"product_id": "A", "receipt_id": None, "quantity": 50, "unit": "EA"}]
    elif number == 20:
        notice["warnings"] = ["Revised delivery table says 2026-11-08; note says 2026-11-09."]
    quote = {"document_id": f"C{number:03}-QUOTE", "document_type": "quotation", "po_id": "PO1",
             "supplier_id": "S1", "original_delivery": None, "revised_delivery": None,
             "items": [{"product_id": "A", "receipt_id": None, "quantity": capacity, "unit": "EA"}],
             "quote": {"quote_id": f"Q{number:03}", "supplier_id": "S1", "product_id": "A",
                       "capacity": capacity, "arrival_date": arrival, "unit_price": price,
                       "shipping_cost": "500", "currency": "KRW"}, "warnings": [], "evidence": []}
    return case, [po, notice, quote]


def render(path, case, doc, *, korean_date=False, contradictory=False):
    title = ParagraphStyle("title", fontName="Suite", fontSize=22, leading=28,
                           textColor=colors.HexColor("#17324d"))
    body = ParagraphStyle("body", fontName="Suite", fontSize=10, leading=16)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=12)
    names = {"purchase_order": "PURCHASE ORDER / 발주서",
             "delivery_notice": "DELIVERY NOTICE / 납기 변경 통보서",
             "quotation": "SUPPLIER QUOTE / 대체 공급업체 견적서"}
    def display_date(value):
        if not value:
            return "NOT PROVIDED / 미기재"
        if korean_date:
            year, month, day = value.split("-")
            return f"{year}년 {int(month)}월 {int(day)}일"
        return value
    details = [["Case ID", case["case_id"]], ["Document ID", doc["document_id"]],
               ["Related PO" if doc["quote"] else "PO ID", doc["po_id"]]]
    if doc["quote"]:
        q = doc["quote"]
        details += [["Quote ID", q["quote_id"]], ["Supplier ID", q["supplier_id"]],
                    ["Arrival date", display_date(q["arrival_date"])],
                    ["Unit price", q["unit_price"] + " KRW / EA"],
                    ["Shipping cost", q["shipping_cost"] + " KRW (once per quote)"],
                    ["Currency", "KRW"]]
        header = ["Product", "Capacity", "Unit"]
        lines = [[item["product_id"], str(item["quantity"]), item["unit"]]
                 for item in doc["items"]]
        note = "Replacement offer only. No purchase has been placed."
    else:
        details += [["Original delivery", display_date(doc["original_delivery"])]]
        if doc["document_type"] == "delivery_notice":
            details += [["Revised delivery", display_date(doc["revised_delivery"])]]
        header = ["Product", "Receipt", "Quantity", "Unit"]
        lines = [[item["product_id"], item["receipt_id"] or "NOT PROVIDED",
                  str(item["quantity"]) if item["quantity"] is not None else "NOT PROVIDED",
                  item["unit"]] for item in doc["items"]]
        note = ("Only the listed receipts are affected; all other receipts retain their original dates."
                if doc["document_type"] == "delivery_notice" else "Original inbound schedule.")
    if contradictory and doc["document_type"] == "delivery_notice":
        note += " Written confirmation: revised delivery is 2026-11-09."
    style = TableStyle([("FONTNAME", (0, 0), (-1, -1), "Suite"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c8d3dd")),
                        ("TOPPADDING", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 9)])
    table = Table(details, colWidths=[190, 305]); table.setStyle(style)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf3f8"))]))
    items = Table([header] + lines, colWidths=[495 / len(header)] * len(header)); items.setStyle(style)
    items.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]))
    story = [Paragraph("LEADTIME GUARDIAN | SYNTHETIC TEST DOCUMENT | DRAFT", small),
             Spacer(1, 18), Paragraph(names[doc["document_type"]], title), Spacer(1, 18),
             table, Spacer(1, 20), items, Spacer(1, 18), Paragraph(note, body), Spacer(1, 22),
             Paragraph("SYNTHETIC / 합성 자료. Fictional procurement test data. "
                       "Inventory and customer orders are separate trusted JSON inputs. "
                       "Human label review pending.", small)]
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=50, rightMargin=50,
                      topMargin=40, bottomMargin=40, title=names[doc["document_type"]]).build(story)


def generate(root, font):
    pdfmetrics.registerFont(TTFont("Suite", str(font)))
    records = []
    for number in range(2, 21):
        case, docs = case_spec(number)
        target = root / case["case_id"]
        target.mkdir(parents=True, exist_ok=False)
        manifest = {"case_id": case["case_id"], "synthetic": True, "label_status": "DRAFT",
                    "studio_executed": False, "human_gold_reviewed": False, "documents": []}
        for doc in docs:
            path = target / f"{case['case_id']}_{doc['document_type']}.pdf"
            render(path, case, doc, korean_date=number == 17, contradictory=number == 20)
            manifest["documents"].append({"document_id": doc["document_id"],
                "document_type": doc["document_type"], "filename": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        write_json(target / "trusted_base_case.json", case)
        write_json(target / "manifest.json", manifest)
        write_json(target / "extraction_gold.DRAFT.json", {"provenance": "generator source; NOT Studio predictions",
                   "human_reviewed": False, "documents": docs})
        records.append({"case_id": case["case_id"], "failure_class": TYPES[number - 1],
                        "synthetic": True, "studio_tested": False, "human_label_reviewed": False})
    with (root / "case_types.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0])); writer.writeheader()
        writer.writerow({**records[0], "case_id": "SYN-C001", "failure_class": TYPES[0]})
        writer.writerows(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/cases")
    parser.add_argument("--font", type=Path, required=True)
    args = parser.parse_args()
    generate(args.output, args.font)
