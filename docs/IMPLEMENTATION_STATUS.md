# B+C3 implementation status (2026-10-30 KST)

## Source code delivered in PR #11 (unmerged)
- B: deterministic lead-time calculations, multi-order deadline allocation, quote draft with capacity and shipping charged once.
- C1: baseline vs revised ETA, per-order and case-level additional shortage.
- C2: normalized documents checked for PO/SKU/ETA conflicts and ambiguous receipts; unsafe cases are blocked.
- C3: multiple partial inbound receipts per PO/SKU; quantities never reused.
- Studio extraction adapter and local regression tests; run CI and review before merge.

## Not yet done
- 20-case/60-PDF package described in earlier local work is **not in this Git branch**; do not confuse local files with committed files.
- Upstage Studio real agent runs, actual agent config export, Studio predictions and field-level PDF source verification.
- Authentication, persistent database, production UI, ERP sync and email/purchase actions.
- Studio API transport requires real API request/response and account permission; credentials must stay outside Git.

**Safety:** evidence_document_ids tracks document references only. evidence_verified_against_pdf=false until human verification. Cost output is a greedy quote estimate, not globally optimal.

**Deadline:** final submission 2026-11-10 17:00 KST per the 10/30 team timetable; confirm LMS details.
