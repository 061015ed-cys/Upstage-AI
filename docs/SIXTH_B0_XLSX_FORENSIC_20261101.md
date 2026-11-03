# LeadTime Guardian — 6차 B0 원본 XLSX 포렌식 (2026-11-01)

## ACTUAL_SOURCE_FILE
- User upload: job-list-agt_HdtU-2026-11-01T09-21-32 (1)(1).xlsx
- Original XLSX size: 8016 bytes
- SHA-256: ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb (matches reported original)
- Sheet: Job List, raw OOXML dimension A1:AF4.
- XLSX A2 reports a single Job job_NCik8shwrgM93PDnNNYukT, config version 1, three PDFs; rows 2/3/4 are purchase_order/delivery_notice/quotation Extract splits, not three separate Job IDs.
- This proves an XLSX display structure, **NOT** the three-document Normalize Native JSON, QA report or PDF SHA.

## CORRECTED_FINDING — 22 SHARED STRING POINTERS, NOT 22 LITERAL VALUES
The 22 allegedly literal string 49 cells are OOXML shared-string references: cell type t=s and raw v=49. The value 49 denotes ZERO-BASED sharedStrings index 49, not the cell's text. In this original XLSX file, the entry at index 49 of xl/sharedStrings.xml contains an empty string (XML t node with empty text). Correct decoded cell contents are empty strings.

- Literal STRING_49 count: **0**
- Literal NUMBER_49 count: **0**
- Formula cached 49 count: **0**
- Raw sharedStrings index49 reference count: **22**
- Index49 references resolved to empty string: **22**
- No original workbook bytes were edited or uploaded to GitHub. An importer also returned the raw string "49", contradicting standard OOXML shared-string interpretation. This is a parsing/representation boundary discrepancy, not demonstrated LLM "49 hallucination".

## COMPLETE COORDINATE AND VERIFIED HEADER MAPPING
| Document branch | Cells with raw shared string index 49 (all resolved empty) |
|---|---|
| Purchase order — 10 | R2=supplier_id, T2=revised_delivery, Y2=quote.quote_id, Z2=quote.supplier_id, AA2=quote.product_id, AB2=quote.capacity, AC2=quote.arrival_date, AD2=quote.unit_price, AE2=quote.shipping_cost, AF2=quote.currency |
| Delivery notice — 9 | R3=supplier_id, Y3=quote.quote_id, Z3=quote.supplier_id, AA3=quote.product_id, AB3=quote.capacity, AC3=quote.arrival_date, AD3=quote.unit_price, AE3=quote.shipping_cost, AF3=quote.currency |
| Quotation — 3 | S4=original_delivery, T4=revised_delivery, V4=items.receipt_id |

XLSX column headers from original row1 are VERIFIED. Corresponding exact Extract/Merge/Normalize JSON paths and raw values are NOT_VERIFIED because original Step output files were not provided.

## NORMAL NONEMPTY XLSX VALUES (NOT PDF-GROUNDED GOLD)
- Purchase order: PO-DOC / purchase_order, po_id PO1, original_delivery 2026-11-03, product A, receipt R1, numeric item quantity 100, unit EA.
- Delivery notice: NOTICE-DOC / delivery_notice, PO1, original_delivery 2026-11-03, revised_delivery 2026-11-08, product A, receipt R1, numeric quantity 100, unit EA.
- Quotation: QUOTE-DOC / quotation, PO1, supplier S1, product A, numeric item quantity 60, quote Q1/S1/A, numeric capacity 60, arrival 2026-11-04, unit_price "1000.00" stored as text, shipping_cost "500" stored as text, KRW.

## CAUSAL_ORIGIN / EXTRACT_NULL_SCHEMA / PYTHON_SAFETY
- CONFIRMED root of apparent "49": raw shared-string index 49 was misread as a literal value in at least one import/display method.
- UNKNOWN: Which Studio Stage first wrote the empty string as its missing-value representation, whether that representation matches the actual saved B0 Config, and its correctness against PDFs.
- Prior preserved v4 DRAFT declares string/integer/array fields while asking for null in descriptions. This is a separate STATIC contract issue, not proof of the runtime cause or a required Studio syntax edit. Extract quote array and normalized quote object|null are intentionally separate contracts.
- Python V6 validates normalized document JSON schema, quote/receipt consistency, date, quantity. The raw XLSX is NOT a substituted Native input for Python execution. Do not convert empty strings or index 49 automatically to 0, null, "null", or guessed receipt IDs.
- Valid Excel output quantity 100/100/60 and capacity 60 is preserved. Their PDF truth is still unverified.
- Original XLSX is read-only. The revised GitHub CLI exposes shared_index_49_reference_count and resolved values separately from actual xlsx_49_count. Its tests use synthetic fixtures, NOT the user's XLSX in CI.

## GATES AND NEXT ACTION
- XLSX_49_ANALYSIS_GATE: PASS_LOCAL_OOXML; literal 49 anomaly NOT_REPRODUCED.
- EXTRACT_SCHEMA_GATE: FAIL_STATIC_DRAFT_CONTRACT; live B0 saved Config not verified.
- B0_SINGLE_JOB_GATE: SINGLE_JOB_REPORTED (one Job in XLSX, Native 3-doc still NOT_VERIFIED).
- NORMALIZE_QA_INPUT_GATE: NOT_VERIFIED; STUDIO_DOCUMENT_GATE: NOT_VERIFIED.
- B0_E1_COMPARISON_GATE: BLOCKED (E1 not provided); STUDIO_PROVENANCE/CROSS_AGENT/HUMAN_GOLD: BLOCKED.
- ACTUAL_STUDIO_E2E/OVERALL_RELEASE: BLOCKED.

Studio AI: First retrieve actual NCik Job Extract/Merge/Normalize/QA Input+Report raw JSON, original PDF SHA and upload receipts. Compare missing/null/"" per stage. Do NOT rerun B0/E1 or mutate saved B0 Config v1 just to "remove 49".
