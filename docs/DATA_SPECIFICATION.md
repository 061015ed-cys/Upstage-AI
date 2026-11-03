# Data Specification V1
Source: **synthetic-only**. Planned 20 cases × 3 PDFs = 60 documents. `data/cases/case_types.csv`: case ID, failure class, file IDs, synthetic flag, Studio-tested flag, human-label-reviewed flag. Gold document labels are drafts until manually verified against generated PDF, never copied from Studio prediction. Actual Studio runs require separate `data/results/studio_runs/`.

CSV contracts:
- `inventory(case_id,product_id,available_stock)` EA int>=0
- `orders(case_id,order_id,product_id,due_date,quantity)`
- `inbound(case_id,receipt_id,po_id,product_id,original_eta,eta,quantity)`
- `quotes(case_id,quote_id,supplier_id,product_id,arrival_date,capacity,unit_price,shipping_cost,supplier_risk)`
`document-extraction.schema.json` document-level normalized keys: `document_id, document_type, po_id, supplier_id, original_delivery, revised_delivery, items[{product_id,quantity,unit}],quote,warnings`. Null means absent, not a guessed value.
Portfolio input/output schemas version 1.0.0. ISO YYYY-MM-DD dates, price as Decimal string, KRW, EA. Reject unexpected product refs, negative or duplicate IDs, NaN/inf and unit mismatch.
Case types C001..020: baseline, minor delay, late delivery, enough stock, equal ETA, early ETA, two orders, partial arrival, two products, late quote, insufficient quote capacity, premium quote, mismatched PO, missing ETA, missing quantity, unknown product, Korean-formatted date, duplicate PO reference, supplier unavailable, contradictory wording.
Evaluate: classification accuracy per document; extract field exact match and null recall; multi-item recall; reviewer flags separately; numerical shortage/order match with independent manually checked truth. Do not call local schema checks Studio extraction accuracy.
Public DataCo shipping data can provide domain context but does **not** substitute for purchase-order change notices; do not upload public files until license/redistribution/privacy checked. All generated companies/orders are fictional.