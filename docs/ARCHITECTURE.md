# System Architecture — LeadTime Guardian V1

```mermaid
flowchart LR
  PDF[PO / Delay Notice / Supplier Quote PDF] --> ST[Upstage Studio: Parse/Classify/Extract/Instruct]
  ST --> AD[Validate and normalize JSON]
  CSV[Inventory / Inbound / Customer Orders / Quote CSV] --> AD
  AD --> PY[Python: allocate stock by customer deadline]
  PY --> Q[Feasible supplier quote comparison]
  Q --> R[Risk / shortage JSON + approval-only email draft]
  R --> H[Human review; no automatic purchase or send]
```

## Roles and contracts
AI handles unstructured documents and explanations only. Python owns dates, quantities, capacity, monetary amounts. Target normalized extraction JSON includes `document_id,document_type,po_id,supplier_id,original_delivery,revised_delivery,items[],quote,warnings`. Engine input is a single `case_id`, `snapshot_date`, `inventory[]`, `inbound[]`, `orders[]`, `quotes[]`. Engine output is `schema_version,case_id,status,delays[],impacted_orders[],supplier_options[],uncovered_quantity,needs_review,review_flags,execution_status,external_action_taken`. All input dates ISO YYYY-MM-DD, quantities nonnegative integer EA, prices KRW decimal strings.

## Algorithm
For each SKU sort customer orders by due date then order ID. Add inbound batches with ETA <= customer's deadline. Allocate min(request, currently available) and never reuse allocated stock. Compute `delay_days=max(0,eta-original_eta)`. Each eligible quote must arrive by deadline; consume its total capacity across orders and recommend priced quantities. Quote estimates are **per-order**; shipping may repeat on a quote allocated across multiple orders and must not be treated as approved global total. No business-calendar, BOM, quality losses, reserved-stock sync, ERP API, or global optimization.
Invalid PO/product/unit joins, duplicate IDs, missing dates, or bad amounts are not inferred: block and flag for review. Final purchase/email needs human approval (the MVP has no send action).

## Integration
Current runnable interface: `leadtime_guardian.engine.analyze_portfolio(payload)->dict`, `scripts/run_portfolio_demo.py`. A proposed `POST /v1/analyze` is **not implemented**. Studio Export Agent Config JSON is an external artifact, never synthesized. API key in local environment only. C modules for scenarios/evidence/optimizer can be added without changing the V1 calculation contract. Official: https://console.upstage.ai/docs/agents ; https://console.upstage.ai/ko/docs/studio/key-features
