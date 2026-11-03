"""Generate three synthetic PDFs from the pinned portfolio sample, never predictions."""
import argparse
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


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate(destination, font_path):
    destination.mkdir(parents=True, exist_ok=True)
    case = json.loads((ROOT / "data/sample/portfolio_case.json").read_text(encoding="utf-8"))
    receipt, quote = case["inbound"][0], case["quotes"][0]
    pdfmetrics.registerFont(TTFont("C001", str(font_path)))
    title = ParagraphStyle("Title", fontName="C001", fontSize=23, leading=32,
                           textColor=colors.HexColor("#17324d"))
    normal = ParagraphStyle("Body", fontName="C001", fontSize=10, leading=17)
    small = ParagraphStyle("Small", parent=normal, fontSize=8, leading=13)
    specs = [
        ("purchase_order", "PO-DOC", "PURCHASE ORDER / 발주서", [
            ["PO ID / 발주번호", receipt["po_id"]],
            ["Original delivery / 기존 입고일", receipt["original_eta"]],
        ], [["Product / 품목", "Receipt / 입고 건", "Quantity / 수량", "Unit / 단위"],
            [receipt["product_id"], receipt["receipt_id"], str(receipt["quantity"]), "EA"]],
         "This purchase order records the original inbound schedule. / 기존 입고 일정입니다."),
        ("delivery_notice", "NOTICE-DOC", "DELIVERY NOTICE / 납기 변경 통보서", [
            ["PO ID / 발주번호", receipt["po_id"]],
            ["Original delivery / 기존 입고일", receipt["original_eta"]],
            ["Revised delivery / 변경 입고일", receipt["eta"]],
        ], [["Product / 품목", "Receipt / 입고 건", "Affected quantity / 수량", "Unit / 단위"],
            [receipt["product_id"], receipt["receipt_id"], str(receipt["quantity"]), "EA"]],
         "Only the delivery date changes; the quantity remains unchanged. / 수량 변경 없이 납기만 변경합니다."),
        ("quotation", "QUOTE-DOC", "SUPPLIER QUOTE / 대체 공급업체 견적서", [
            ["Quote ID / 견적번호", quote["quote_id"]],
            ["Supplier ID / 대체 공급업체", quote["supplier_id"]],
            ["Related PO / 참조 발주번호", receipt["po_id"]],
            ["Arrival date / 대체 입고일", quote["arrival_date"]],
            ["Unit price / 단가", f"{quote['unit_price']} KRW / EA"],
            ["Shipping cost / 운송비", f"{quote['shipping_cost']} KRW (once per quote)"],
            ["Currency / 통화", "KRW"],
        ], [["Product / 품목", "Capacity / 공급 가능 수량", "Unit / 단위"],
            [quote["product_id"], str(quote["capacity"]), "EA"]],
         "Replacement offer only. No purchase has been placed. / 대체 구매 검토용 견적이며 발주가 아닙니다."),
    ]
    manifest = {"case_id": case["case_id"], "synthetic": True,
                "source": "data/sample/portfolio_case.json", "studio_executed": False,
                "human_gold_reviewed": False, "documents": []}
    labels = []
    for kind, did, heading, details, lines, note in specs:
        path = destination / f"SYN-C001_{kind}.pdf"
        story = [Paragraph("LEADTIME GUARDIAN | SYNTHETIC TEST DOCUMENT", small),
                 Spacer(1, 20), Paragraph(heading, title), Spacer(1, 18)]
        meta = [["Case ID / 케이스", case["case_id"]], ["Document ID / 문서 ID", did]] + details
        table = Table(meta, colWidths=[235, 260], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "C001"), ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf3f8")),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c8d3dd")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        item_table = Table(lines, colWidths=[495 / len(lines[0])] * len(lines[0]), hAlign="LEFT")
        item_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "C001"), ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c8d3dd")),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.extend([table, Spacer(1, 24), item_table, Spacer(1, 22), Paragraph(note, normal),
                      Spacer(1, 30), Paragraph(
                          "SYNTHETIC / 합성 자료: fictional procurement test data. "
                          "Inventory and customer orders are separate trusted JSON inputs.", small)])
        SimpleDocTemplate(str(path), pagesize=A4, rightMargin=50, leftMargin=50,
                          topMargin=48, bottomMargin=48, title=heading).build(story)
        manifest["documents"].append({"document_id": did, "document_type": kind,
                                      "filename": path.name, "pages": 1,
                                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        label = {"document_id": did, "document_type": kind, "po_id": receipt["po_id"],
                 "supplier_id": None, "original_delivery": None, "revised_delivery": None,
                 "items": [], "quote": None, "warnings": [], "evidence": []}
        if kind in {"purchase_order", "delivery_notice"}:
            label["original_delivery"] = receipt["original_eta"]
            label["revised_delivery"] = receipt["eta"] if kind == "delivery_notice" else None
            label["items"] = [{"product_id": receipt["product_id"],
                               "receipt_id": receipt["receipt_id"],
                               "quantity": receipt["quantity"], "unit": "EA"}]
        else:
            label["supplier_id"] = quote["supplier_id"]
            label["items"] = [{"product_id": quote["product_id"], "receipt_id": None,
                               "quantity": quote["capacity"], "unit": "EA"}]
            label["quote"] = {key: quote[key] for key in (
                "quote_id", "supplier_id", "product_id", "capacity", "arrival_date",
                "unit_price", "shipping_cost")}
            label["quote"]["currency"] = "KRW"
        labels.append(label)
    base = deepcopy(case)
    base["documents"] = []
    base["quotes"] = []
    for row in base["inbound"]:
        row["eta"] = row["original_eta"]
    write_json(destination / "trusted_base_case.json", base)
    write_json(destination / "manifest.json", manifest)
    write_json(destination / "extraction_gold.DRAFT.json", {
        "provenance": "generator source; NOT Studio predictions", "human_reviewed": False,
        "documents": labels})
    write_json(destination / "expected_calculation.json", {
        "provenance": "expected fixture; NOT Studio predictions", "case_id": case["case_id"],
        "baseline_shortage_quantity": 0, "changed_shortage_quantity": 60,
        "additional_shortage_quantity": 60, "estimated_quote_cost_krw": "60500.00"})
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/cases/SYN-C001")
    parser.add_argument("--font", type=Path, default=Path("C:/Windows/Fonts/malgun.ttf"))
    args = parser.parse_args()
    print(json.dumps(generate(args.output, args.font), ensure_ascii=False, indent=2))
