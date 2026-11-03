# GITHUB_ANALYSIS_RESULT — LeadTime Guardian 5th pass (2026-11-01)

## CURRENT_GITHUB_HEAD / isolation
- Original operating PR#11: f196c694917f2d9e5f4ec228c752bd3f2a4eb882 (no change)
- Team2 V6 original PR#12: e9b9992b593a42d427ff1bbadeb9a9866ca593bd (no change)
- Copy combined PR#4: 9d032d883c49df03657931ea88e97a0bd713043f (no change)
- Copy fourth PR#5: 5ecf6de67e0a5313590e1316ad15700daaacd114 (no change; previous 519 Python/330 QA PASS)
- Three-commit experimental WIP branch feat/qa-studio-github-support-ncik-20261101 compared to PR#5 and preserved as a base for NEW isolated branch feat/qa-fifth-studio-ncik-validation-20261101 / Draft PR#6. WIP had three changed files: input_delivery.py, test_qa_input_delivery.py, qa_excel_49_audit.py; no historical CI success was assumed.
- Exact tested fifth code SHA: a8b2096d665675daa3e63b5c2db7ae7acbdd3fd9. QA 353 passed; full Python 542 passed; Ruff QA and whole repo PASS; C001 archive/replay PASS_LOCAL; conservative Integration Gate overall_status BLOCKED. GitHub Actions https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41295389475 SUCCESS. The final docs-only HEAD requires a separate CI check.
- PR URL: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/6
- The same final Python suite includes the QA subset. Do not add 353 and 542 together.

## NEW_B0_JOB_STATUS
- User/Studio AI reports a new single C001 case Job job_NCik8shwrgM93PDnNNYukT, config cfg_X2xXakDtmDTHh2RoqVysvL v1, source names SYN-C001_purchase_order.pdf, SYN-C001_delivery_notice.pdf, SYN-C001_quotation.pdf.
- This is SINGLE_JOB_REPORTED only, NOT NATIVE_THREE_DOCUMENTS_VERIFIED or ACTUAL_E2E_VERIFIED. Original Native JSON, Normalize raw, IndependentQA input/report, PDF original SHA and upload receipt are not available for the new run in this GitHub Chat. B0 config export described by Studio as available has not been separately provided; a studio.workflow-config-draft is not job-native evidence.
- The three distinct earlier B0 Jobs job_DUdK8NzKasoTvDxGEW9XRY, job_5LX7RWd8SfSUADEfq5MCDL and job_9osC3yrPWtTt2oDjJuSdde remain INVALID_SPLIT_JOBS, NOT a valid comparator.
- New report is preserved in data/observations/B0_C001_NCik_20261101_REPORTED_SINGLE_JOB.json. The three source file IDs are deliberately null to avoid inventing provider file IDs.
- New unit/CLI tests ensure this report is REPORTED_SINGLE_JOB_UNAUTHENTICATED / BLOCKED and must not be mixed with prior archived operational job.

## ISSUE_01_NULL_SCHEMA — CONFIRMED_STATIC_CONFLICT / LIVE_UNVERIFIED
Preserved config configs/studio_native/config_v4.export.json, kind studio.workflow-config-draft; actual saved NCik B0 config was NOT read. Static Extract branches: Extract_purchase_order, Extract_delivery_notice, Extract_quotation, Extract_other. Their common schema describes missing values as null, but po_id, supplier_id, original_delivery and revised_delivery are type string; items.receipt_id has type string with parent description indicating null unless printed; quote is Extract array with description null for non-quotes; nested quote.capacity has type integer while its description says null if absent; quote.unit_price, quote.shipping_cost are strings with similar instructions. Also review receipt_id quantity, quote.date and other fields against source data. The final Python normalization schema has nullable string fields and quote object|null — this is a separate output stage, not proof that Extract quote should be object.

New QA module src/leadtime_guardian/qa/extract_null_contract.py and CLI scripts/qa_extract_null_contract_check.py enumerate all four branches and explicit/generic conflicts, original descriptions, required flags, normalized expected types and risk. To run:
python scripts/qa_extract_null_contract_check.py --config configs/studio_native/config_v4.export.json
No saved Studio config was modified. A normal value 0 must remain 0; missing, null, empty string, quoted "null", numeric string "0", invalid negative values and date errors must not be silently conflated. The Upstage Chat API reference documents using null in strict structured output types, but this does NOT establish the same Studio Extract editor/runtime capability. Official reference: https://console.upstage.ai/api/chat. Ask Studio AI to confirm supported schema syntax inside the actual Studio Extract UI/Config first, record before/after Config and compare test inputs; do not apply unsupported nullable schema syntax.

## ISSUE_02_EXCEL_49 — UNKNOWN_CAUSAL_ORIGIN
The reported 22 problem cells include PO R2/T2/Y2, notice R3/Y3, quotation S4/T4/V4. The actual original affected XLSX and complete 22-cell listing were NOT supplied in this turn or exposed in this QA code branch; cannot independently confirm count/values/type. Existing scripts/qa_excel_49_audit.py classifies NUMBER_49 vs STRING_49 vs FORMULA_CACHED_49, preserves original XLSX SHA and inspects optional Extract/Merge/Normalize raw JSON. WIP additions expose column_header_row1_candidate only, json_field_mapping_verified=false. Fifth additions expose bounded same-row context and closest up-to-three candidate cells ABOVE; no authoritative header row or JSON key mapping is invented. Added synthetic OOXML tests.
Use original export:
python scripts/qa_excel_49_audit.py --xlsx ACTUAL_ORIGINAL.xlsx --extract-json ACTUAL_EXTRACT.json --merge-json ACTUAL_MERGE.json --normalize-json ACTUAL_NORMALIZE.json
Omit unavailable optional stage inputs. CAUSAL_ORIGIN must remain UNKNOWN until actual stage values establish the first appearance, not merely because 49 repeats in multiple cells.

## ISSUE_03_QA_INPUT_DELIVERY — WIP_REVIEWED_AND_HARDENED
Initial WIP supports strict, single/double serialized JSON payload decoding from observed structures under Normalize output/content/documents and QA input/content/normalized_documents. Duplicate keys/malformed JSON are not auto-repaired. Local equality => LOCAL_CONTENT_MATCH but never Studio input authenticated. Missing QA input => UNKNOWN/BLOCKED; model issue NORMALIZED_OUTPUT_NOT_PROVIDED alone is NOT evidence of failed node-to-node transmission.
Fifth additions require nonempty unique document_id and object rows to avoid false match on arbitrary lists; optional expected_case_id rejects explicit mismatched Normalize/QA/QA Report case ID. New scripts/qa_input_delivery_check.py CLI:
python scripts/qa_input_delivery_check.py --normalize ACTUAL_NORMALIZE_STEP.json --qa-input ACTUAL_QA_STEP_INPUT.json --qa-report ACTUAL_QA_REPORT.json --case-id C001
The last two files are optional for diagnosis; if absent, no delivery claim is possible. These are paths to original received outputs, NOT manufactured dummy JSON. The exact current Studio input field path remains UNOBSERVED and no runtime binding failure root cause was confirmed. Existing "selectedSplitResultMatched:false" retrieval failure is not proof that the internal QA input was empty.

## ISSUE_04_B0_E1_COMPARISON — READINESS_GATE_IMPLEMENTED
New src/leadtime_guardian/qa/experiment_compare.py and scripts/qa_b0_e1_compare_check.py reject mismatched Case IDs, split/missing Job, missing saved Config refs, unavailable original 3-PDF name+type+SHA+file-ID set, missing Extract/MergeDocuments/NormalizeDocuments/IndependentQA Step raw SHA/ID, and duplicate B0/E1 Job ID. They report UNKNOWN/NOT_MEASURED, never synthetic accuracy/quality improvement. The manifest-only interface remains BLOCKED even for complete self-reported metadata, because original PDF bytes and live provider authenticity are not independently verified. To check once manifests are actually prepared:
python scripts/qa_b0_e1_compare_check.py --b0 ACTUAL_B0_EVIDENCE_MANIFEST.json --e1 ACTUAL_E1_EVIDENCE_MANIFEST.json
E1 original result is currently NOT_PROVIDED/NOT_RUN. Human-reviewed Gold required for per-field accuracy; compare only after actual original SHA and same case are established.

## CONFIRMED_ROOT_CAUSES
1. Earlier B0: three independent Jobs, invalid group structure, supported by supplied run report; new C001 single Job is a distinct reported execution.
2. Saved v4 DRAFT Extract: textual null instruction vs restrictive type in multiple branches (static JSON analysis).
3. Original archived QA regression: local delivery assumptions need strict wrapping/case checks; does not confirm current Studio internal failure.

## UNCONFIRMED_CAUSES
1. First place 49 appears: Extract / Merge / Normalize / Excel; actual original bytes missing.
2. Whether NCik single Job has 3 normalized documents, correct values, warnings and QA actual status.
3. Whether actual QA Step received Normalize values; internal Step input not retrieved.
4. Whether nullable JSON Schema union/anyOf is accepted in the actual Studio Extract editor.
5. Whether E1 improves any metric, and actual Python/Studio/Human Gold accuracy.

## ACTUAL_CODE_CHANGES
- Preserve WIP: src/leadtime_guardian/qa/input_delivery.py and tests/test_qa_input_delivery.py; scripts/qa_excel_49_audit.py.
- QA changed: src/leadtime_guardian/qa/studio_batch.py (reported NCik job without file_id => BLOCKED not invented mismatch), src/leadtime_guardian/qa/input_delivery.py (fail-closed document shape and case), scripts/qa_excel_49_audit.py (nearby context).
- New: src/leadtime_guardian/qa/extract_null_contract.py, src/leadtime_guardian/qa/experiment_compare.py, scripts/qa_extract_null_contract_check.py, scripts/qa_input_delivery_check.py, scripts/qa_b0_e1_compare_check.py.
- New tests: test_qa_extract_null_contract.py, test_qa_b0_e1_comparison.py, test_qa_input_delivery_strict_case.py, test_qa_fifth_single_job_report.py; expanded test_qa_excel_49_audit.py; new user-reported observation JSON.
- No original operational Python/Studio config/PDF/Gold modification; no new paid Studio Job; no merge/force push.

## TEST_RESULTS / CI_RESULT
At fifth **code** SHA a8b2096d665675daa3e63b5c2db7ae7acbdd3fd9: GitHub Actions SUCCESS (#41295389475), QA pytest 353 PASS; full Python pytest 542 PASS; Ruff QA + repo PASS; archived replay and conservative local gate successful; overall release BLOCKED. Code tests include synthetic fixtures and archived C001; DO NOT re-label as NCik live E2E.

## REMAINING_BLOCKERS
- Actual Native + 3 PDF upload receipts/SHA/Step outputs for Job NCik.
- IndependentQA input and report raw bytes, updated saved Config version and actual Job metadata.
- Current operating Python Job/result and studio-provenance/1 sidecar from Team2.
- Human-reviewed field-level Gold PDF/page evidence from Team3.
- E1 actual comparable single case Job and originals.
- Release sign-off. New GitHub CI success cannot clear these.

See companion docs/STUDIO_FIX_REQUEST_FIFTH_20261101.txt for the minimal Studio AI handoff.
