# QA raw Studio adapter and team 2 provenance checkpoint — 2026-11-01

## Scope and factual limits

Owner: Team 1, QA-only branch `feat/qa-sandbox-copy-validation-20261101`, Draft PR #3 against QA PR #2. Never merge without approval.

- QA Sandbox original: `agt_GhP9GywhbcDWquFqWTsmtq`.
- Sandbox copy: `agt_HdtUJPQPXir9rGKgPWSyZG`, `cfg_X2xXakDtmDTHh2RoqVysvL`, v1. This narrow allow-list is NOT authentication of any Studio export.
- Existing completed QA Job `job_9DmRWeQsSShHgWUugkELtk` is **historical**, not eligible for NEW_LIVE_STUDIO.
- The supplied config export is `kind=studio.workflow-config-draft`; it is not a native Job export.
- C001 existing QA findings described by Studio handoff: `qa_status=NOT_VERIFIED`, `evidence_status=PARTIAL`, 20 field checks (17 VERIFIED, 3 SOURCE_NOT_VERIFIED), with null workflow/config/job/source provenance. No actual raw Native/report bytes independently verified here.
- Cross-Agent status BLOCKED; release gate BLOCKED. No extraction accuracy or Python independent QA success can be claimed from those reports.

## Actual additions

1. `qa/studio_qa_adapter.py` maps explicitly supplied Studio `qa_status`, checked document IDs, issues, evidence status, field checks and provenance to document-only QA status, with Python always NOT_VERIFIED. Missing fields and mismatched case/doc identities are errors. A raw PASS with incomplete field/source evidence is downgraded, never promoted.
2. `qa/cross_agent.py` accepts explicit `studio.qa_report_format=STUDIO_INDEPENDENT_QA_V1`; the original report bytes still determine `studio.qa_report_sha256`. The adapted verdict lives in `verdict` and is compared to independently parsed raw report. The legacy `HANDOFF_VERDICT_V1` path remains the default for compatibility. Original Native bytes, Job/Step, source file IDs, native document IDs and original report bytes are checked separately.
3. `qa/handoff_builder.py` and `scripts/qa_prepare_studio_raw_handoff.py` derive a manifest from **real supplied raw bytes**, without rewriting them. The CLI exits 2 for a structurally BLOCKED/NOT_VERIFIED handoff; 1 for failure. No newly LIVE cloud authentication is inferred.
4. `qa/provenance_link.py` and `scripts/qa_provenance_link_check.py` compare team 2's `studio-provenance/1` sidecar with the QA manifest and separate PDF receipts, verifying local SHA-256 against supplied PDF bytes when available. The two distinct Studio Job IDs need not match. Matching PDFs proves local byte equality only, never actual Studio upload.
5. `qa/input_delivery.py` distinguishes completed Normalize, unknown QA input, local document-content match and mismatch. `NORMALIZED_OUTPUT_NOT_PROVIDED` is a model report assertion, not direct proof of a missing transmission. Null provenance is incomplete, not necessarily a contradiction.
6. `scripts/qa_excel_49_audit.py` reads OOXML cell values without mutation: numeric 49 vs string "49", also optional Extract/Merge/Normalize raw JSON occurrences. The source of 49 remains UNKNOWN without stage bytes.
7. Tests: `test_qa_studio_adapter.py`, `test_qa_handoff_builder.py`, `test_qa_provenance_link.py`, `test_qa_input_delivery.py`, `test_qa_excel_49_audit.py` cover synthetic positive/negative cases. Do not call them new Studio executions.

## Exact CLI examples

```bash
python scripts/qa_prepare_studio_raw_handoff.py \
  --native actual-normalize-native.json \
  --qa-report actual-independentqa-report.json \
  --case-id C001 \
  --agent-id agt_HdtUJPQPXir9rGKgPWSyZG \
  --config-id cfg_X2xXakDtmDTHh2RoqVysvL \
  --config-version 1 \
  --github-sha ACTUAL_40_CHARACTER_QA_SHA \
  --execution-kind ARCHIVED_STUDIO \
  --manifest-output derived-handoff.json

python scripts/qa_cross_agent_check.py \
  --manifest derived-handoff.json \
  --native actual-normalize-native.json \
  --qa-report actual-independentqa-report.json \
  --expected-agent-id agt_HdtUJPQPXir9rGKgPWSyZG \
  --expected-config-id cfg_X2xXakDtmDTHh2RoqVysvL \
  --expected-github-sha ACTUAL_40_CHARACTER_QA_SHA \
  --require-contract

python scripts/qa_provenance_link_check.py \
  --qa-handoff derived-handoff.json \
  --team2-provenance team2-studio-provenance.json \
  --qa-pdf-receipt qa-input-receipt.json \
  --operational-pdf-receipt operation-input-receipt.json \
  --pdf-root ./actual-original-pdfs

python scripts/qa_excel_49_audit.py \
  --xlsx job-list-agt_HdtU-2026-11-01T06-53-15.xlsx \
  --extract-json actual-extract.json \
  --merge-json actual-merge.json \
  --normalize-json actual-normalize.json
```

PDF receipt required shape:
```json
{
  "case_id": "C001",
  "files": [
    {"filename": "SYN-C001_purchase_order.pdf",
     "file_id": "file_actual_id", "sha256": "actual_lowercase_sha256"}
  ]
}
```
Provide full case-specific sets, including three PDFs for C001, not only the example. Use actual file IDs from the respective operating or QA Job; they are not required to match across Studio Jobs. Incomplete or missing inputs fail closed.

## EVIDENCE REQUIRED from Studio (current blocker)

- Actual QA copy saved Config, Config version and `kind` of export. If v2+ was saved, provide the exact saved ID, backup and changed-node diff; current v1 allow-list must not automatically approve v2.
- For existing C001 Job: original unmodified NormalizeDocuments native final and IndependentQA report bytes, downloaded separately; SHA-256 computed from each file; actual Job/Step IDs and statuses. Additionally the direct IndependentQA input payload if accessible, not merely the prior Normalize status.
- Actual field/issue key spelling, field_checks entries, explicit checked_document_ids, origin of null execution_provenance values, and whether an observed `NORMALIZED_OUTPUT_NOT_PROVIDED` is a report assertion or an independently observed input omission.
- Raw extract/merge/normalize to locate Excel `49` or report UNKNOWN; case PDF source file IDs and original SHA hashes; avoid asserting 49 is a model defect without raw comparison.
- If a previous UI/API path produces 404/permission denied, record exact error and use only an alternate **verified** export route; do not repeatedly report success or fabricate files.
- All original C001 and C013 outputs must be distinctly identified by case, saved Config, Job/Step and run kind. No payment, new paid execution, deletion, modifications of original workflow or forced PR merge.

## TEAM2_INTERFACE_REQUEST

From PR #12 owner request actual current operational Job/Step/Agent/Config identifiers and saved config version, original exported Native bytes and checksum, `studio-provenance/1` sidecar, Python analysis/status and its Git SHA, three original source PDFs with SHA-256 and an operational-job upload receipt `{case_id,files:[{filename,file_id,sha256}]}`. `evidence_verified_against_pdf=false` is a normal unverified sidecar property, not Python PASS. Keep historical prediction Job ID separate from the QA Job. Do not modify Python Adapter/engine to satisfy this bridge.

## Risk status and follow-up

- Code/test CI passing at a given SHA is not independent Studio, human Gold, current team2+QA integrated E2E or submission PASS.
- C013 PO1/PO999 is a fail-closed mismatch; C017 date cannot be invented; C008 receipt-level allocations cannot be aggregated across ambiguous receipts.
- Final QA-only code ready for review. Keep Release Gate BLOCKED until raw Studio bytes, team2 operational evidence, case/PDF binding and human Gold are all independently available.
