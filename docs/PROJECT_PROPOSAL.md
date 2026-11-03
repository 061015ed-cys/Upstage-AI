# LeadTime Guardian — Project Proposal
2026-10-29 / Synthetic-data prototype / KST

## Problem
When a supplier changes a PO delivery date, purchasing teams manually reconcile PO, delay notice, stock, customer commitments, and substitute quotes. The goal is document-to-decision: identify affected orders, calculate shortage, and generate review-only purchasing responses.

## User and workflow
Purchaser uploads purchase order, supplier delay notice and alternate supplier quotation. Upstage Studio performs Parse → Classify → Extract → Instruct with optional Validate/Match after testing. Python validates document IDs, PO/product consistency, and performs deterministic order allocation, ETA/shortage computation and supplier quote comparison. Purchasing manager reviews the recommendation; **no auto-purchase or outgoing email**.

## Priorities
P0 B: parse/classify/extract, match PO/product, calculate delay, allocate stock among customer orders, compare available quotes, structured JSON, approval-only draft, >=20 document test cases with evaluation.
P1 C: evidence attribution, contradiction review, multiple quote scenarios.
P2 / excluded: global mixed-integer optimization, real ERP integrations, multi-agent delegation, UI polish. No model training or GPU.
Success criteria: successful schema validation, reproducible Python results, actual Studio output recorded separately, 20-case evaluation, complete submission package. These are internal targets, not official judging weights.

## Assumptions and risks
EA per product, KRW Decimal, available stock unreserved on snapshot, inbound each receipt as independent lot, earliest customer deadline first, no BOM/calendar constraints. No historical accuracy claims from synthetic data. Missing or conflicting values must block unreviewed automation. Main technical risk: Studio workflow capabilities and models vary by account; verify after 10/30 access.

## B→C strategy
Fixed V1 normalized input/output contracts. Add optional scenario/audit modules after B is stable, preserving deterministic engine and fallback. Show quantities, quoted capacity, dates, cost and document IDs separately from LLM explanation.