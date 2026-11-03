# Security and safety review — 2026-11-01

## Reviewed boundaries

| Boundary | Source paths | Outcome |
| --- | --- | --- |
| Strict JSON and duplicate keys | PR#12 `strict_json.py`, QA `audit.load_json_strict` | Implemented and locally tested; no evidence of cloud authenticity |
| PDF → extracted fields | Studio configs and `studio_integration.validate_documents` | Static null schema conflicts, actual source/page match NOT_VERIFIED |
| PO/SKU/receipt | `validate_documents`, `apply_studio_extractions`, `engine.evidence_flags` | Ambiguous matching and conflicts blocked on full validation path; actual Studio C013 NOT_VERIFIED |
| Numeric/date/currency | `engine.prepare/quantity/money/date_value` | Strict finite nonnegative amounts and ISO dates; partial receipts support in engine |
| Counterfactual | `engine.allocate` two baseline/revised passes | Deterministic local calculation; quote selection is draft, not globally optimal |
| Unverified source IDs | `qa/cross_agent.py` | **Fixed** reject missing/empty Native metadata.source_files |
| Source-PDF path escape | `qa/provenance_link.py` | **Fixed** reject symlink escaping trusted root |
| Workbook value provenance | `scripts/qa_excel_49_audit.py` | **Fixed** distinguish formula cached 49 vs literal string/numeric 49 |
| Old Job spoofing | `qa/cross_agent.py` | Existing explicit completed IDs blocked from being called new |
| Current Job identity | QA sidecar/manifest metadata | Local contract only. No cloud signature, saved Config/Job authentication |
| External business action | Engine `blocked_result/analyze_portfolio` | `external_action_taken=false`; no purchase or mail initiated in this audit |
| Human Gold and approval | Team3 human review and G9 | BLOCKED |

## Residual P0/P1 issues

**P1** operational Extract nullability schema and implementation instructions do not fully align in user-supplied v5 draft. Team 2 / Studio AI must own any changes; capture saved config diff and real stage output.

**P1** local and archived replay are not a signed/verifiable Studio source. Distinct QA and operational Job IDs should be retained, not silently joined. Independent PDF receipts and uploaded source_file IDs must bind each Job to original PDF SHA, with explicit evidence source.

**P1** same-run provenance conflict: compare only non-null actual same execution IDs. Null means NOT_VERIFIED; historic operational prediction Job is separate. Warning plus requires_human_review; never new-live success evidence.

**P1** raw QA Input Step not independently captured for C001; Normalize COMPLETED does not prove transmission to IndependentQA.

**P1** integration of team2 PR #12 Python source with QA PR #3 has NOT_RUN; final combined SHA/CI missing.

**P2** Excel 49 origin remains UNKNOWN despite utility capable of parsing cell types and comparing optional Extract/Merge/Normalize JSON.

**P1 (interface review)** `engine.analyze_portfolio` takes case documents, while the stricter `studio_integration.validate_documents` is a separate wrapper. Team 2 must confirm no external entrypoint bypasses the stricter document-to-receipt validation.

**P2** B0/E1/E2/E3/E4 differences cannot be measured without matching saved configurations, case-PDF hashes and human-reviewed Gold.

All code-level QA regressions should be read with their exact CI HEAD. Actual cloud execution and a final release decision remain BLOCKED; no authorization to merge/submit follows from this report.
