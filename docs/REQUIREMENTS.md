# Software Requirements Specification V1
| ID | P | Input → output / DoD | Estimate |
|---|---|---|---|
| FR-001 | P0 | PDF → parsed text, manual source check | M/3h |
| FR-002 | P0 | Text → PO/DELAY_NOTICE/SUPPLIER_QUOTE/OTHERS; >=20-case actual run | M/2h |
| FR-003 | P0 | Text → fields/items/date/quote JSON; null for missing | H/6h |
| FR-004 | P0 | PO and SKU matching; conflicts blocked | M/3h |
| FR-005 | P0 | Date change → max(0,revised-original) | L/1h |
| FR-006 | P0 | Inventory, inbound and orders → customer shortages with no reuse | H/6h |
| FR-007 | P0 | Shortage → impacted order IDs | L/1h |
| FR-008 | P0 | Supplier quotes → feasible quantity, cost, ETA | M/4h |
| FR-009 | P0 | Decision → approval-only email/report draft, never sends | M/3h |
| FR-010 | P0 | Schema keys + gold labels exactly comparable | M/4h |
| FR-011 | P0 | Missing, duplicate, conflicting documents → review | M/3h |
| FR-012 | P0 | >=20 cases with PDFs and human-reviewed truth | M/5h |
| FR-013 | P1 | Separate classification/extraction/numerical metrics | M/3h |
| FR-014 | P1 | 2-3 cost/deadline/risk scenario comparisons | M/4h |
| FR-015 | P2 | Approval state and optional UI | H/6h |

NFR-001 deterministic reproducibility (pytest). NFR-002 no keys, PII or actual orders in repository. NFR-003 source document traceability. NFR-004 failures and costs logged by stage. NFR-005 stable versioned V1 contract. NFR-006 zero external sends. Tests T-001..T-012 map to respective FR requirements, including multi-item, partial inbound, duplicate receipt, unknown product, wrong PO, missing date, quote arriving too late, quote capacity. Done = working code + sample input/output + test evidence + documentation; local success never counts as Upstage success.
Estimates are person-hours for initial development; API cost needs real measured pages/tokens.