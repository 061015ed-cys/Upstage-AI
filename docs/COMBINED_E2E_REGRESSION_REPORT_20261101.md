# Combined Team2 V6 + QA Offline E2E / Raw Studio Intake

Tested code HEAD: `bdcdac48a39a73ee72f19936818648eae1813c90`, CI https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41291094905 — 315 QA + 504 total Python PASS; Ruff PASS.

## Tests that execute both code families

- `tests/test_qa_combined_v6_contract.py`: exact Team2 PR#12 engine/Adapter/strict JSON → independent QA allocation reference `audit_portfolio`. Archived operational C001 + synthetic DRAFT C013/C017/C008. C001 0→60 EA and KRW 60,500; C013 PO1/PO999 blocked without cost; C017 ISO DRAFT passes, raw non-ISO Korean date is blocked without evidence; C008 R1=40/R2=60 yields revised shortage 40, KRW 40,500; null, "", "null", 0, negative and wrong quantity block.
- `tests/test_qa_combined_e2e_cli.py`: original archived C001 V4 Native + trusted base → Team2 `documents_from_export` / `analyze_studio_documents` + QA independent numeric audit, SHA; optional synthetic QA raw report/Native → QA manifest + Cross-Agent; wrong Job, wrong case, missing one half of QA raw pair, malformed JSON must not pass.
- `tests/test_qa_full_offline_e2e.py` retained: archived operational V4 + deliberately synthetic QA report → Cross-Agent gate BLOCKED.
- Team2 `tests/test_python_safety_v6.py` staged without changing the authoritative tests, including source metadata preservation and fail-closed case suite.

## New CLI: same-code-tree combined E2E

When original downloaded artifacts are available, from the integrated copy branch run:

```bash
python scripts/qa_combined_e2e_check.py \
  --operational-native <ACTUAL_OPERATION_NATIVE_JSON> \
  --trusted-base <CASE_TRUSTED_BASE_JSON> \
  --operational-job-id <ACTUAL_OPERATION_JOB_ID> \
  --case-id C001 \
  --github-sha <CURRENT_40_CHAR_QA_INTEGRATION_SHA> \
  --qa-native <ACTUAL_QA_NORMALIZE_NATIVE_JSON> \
  --qa-report <ACTUAL_INDEPENDENT_QA_REPORT_JSON> \
  --qa-agent-id agt_HdtUJPQPXir9rGKgPWSyZG \
  --qa-config-id cfg_X2xXakDtmDTHh2RoqVysvL \
  --qa-config-version 1 \
  --execution-kind ARCHIVED_STUDIO
```

The placeholders are deliberate: no current real QA raw files or current operating Job are in this branch. `--qa-native` and `--qa-report` are optional as a **pair**, but absent pair causes `QA_STUDIO_RAW_ARTIFACTS_NOT_PROVIDED` and BLOCKED. If the QA Config changes to v2+, stop and require explicit reviewed allow-list update; do not pretend v1 matches.

Result fields are independent: `python_business_status`, `python_safety_status` (`PASS_LOCAL`, `SAFELY_BLOCKED_LOCAL`, `FAIL` or `NOT_VERIFIED`), `studio_document_status`, `cross_agent_status`, raw SHA-256 digests, `actual_studio_e2e_status=NOT_VERIFIED`, `same_original_pdf_bytes_verified=false`, `release_or_merge_authorized=false`.

This CLI neither authenticates a Studio cloud execution nor compares the original source PDFs. To verify matching PDFs separately, use `scripts/qa_provenance_link_check.py` on complete per-Job PDF receipts with original bytes and SHA; independent proof of Studio upload remains required. A runnable local contract never authorizes release.

## Test-level statuses

| Scenario | Evidence | Outcome |
| --- | --- | --- |
| C001 | Archived authentic operating V4 native, Team2 V6 Python and QA local reference | PASS_LOCAL; no new Studio |
| C013 | DRAFT fixture PO1/PO999, Team2 and independent QA | SAFELY_BLOCKED_LOCAL |
| C017 | DRAFT ISO + wrong Korean-date synthetic mutation | Correct strict ISO boundary; PDF OCR NOT_VERIFIED |
| C008 | DRAFT R1 40/R2 60, Team2 and QA independent reference | PASS_LOCAL receipt allocation |
| Raw QA report | Synthetic test only | Cross-Agent BLOCKED |
| Actual Studio Jobs + same PDFs | Original source evidence unavailable | NOT_VERIFIED/BLOCKED |
| Human Gold | DRAFT, not reviewed | BLOCKED |

Original operating repository files, PDF/Gold, paid Studio jobs and main were not changed.
