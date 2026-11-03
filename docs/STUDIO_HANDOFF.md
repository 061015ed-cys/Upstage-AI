# Studio ↔ Python ↔ LMS integration handoff

1. Studio Large: verify account access and create the real document workflow (Parse → Classify → type-specific Extract → Merge/Match → Validate/Instruct). The Studio UI and exact native node links must be tested by a teammate.
2. Output normalized JSON using configs/schemas/document_extraction.schema.json. For delivery notices include po_id, revised_delivery, items with product_id and receipt_id when multiple receipts match.
3. Human team members verify PDF originals vs gold labels separately. Run C001 normal, C013 wrong PO (must block), C017 Korean date. Then expand to 20 cases / 60 PDFs. Record predictions, errors, run_id, versions and metrics. Never supply gold labels as Studio predictions.
4. To handoff a predicted case to code: apply_studio_extractions(base_case, predictions), then analyze_portfolio(case). Base case contains trusted inventory/orders/inbound/quotes. Source evidence in this version is identifier-level, not original PDF page text verification.
5. Console: verify actual Agents API endpoint, response JSON, workspace permissions and quota. Do not expose API keys. Native Studio workflow export is not the same as any GitHub JSON Schema.
6. LMS: read course and submission specifications, submit individual/team missions and final artifacts. 10/30 team schedule: final upload before 2026-11-10 17:00 KST. Team should aim earlier.
7. Required for real demo: one actual normal flow and one actual conflicting PO blocked flow; screenshot/export native Studio config; Studio prediction JSON; human checked labels; source PDF; video; one-page design; slides.

Deferred: full cost optimization, multi-agent autonomy, live procurement, ERP and production deployment.
