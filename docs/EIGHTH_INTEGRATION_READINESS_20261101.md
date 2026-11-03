# LeadTime Guardian — 8차 실제 Studio 원본 수신 및 통합 검증 준비도
## A. 원본 수집 체크
| Input | Required Evidence | 2026-11-01 Status | Owner |
|---|---|---|---|
| C001 Existing B0 | Job job_NCik8shwrgM93PDnNNYukT, saved Config cfg_X2xXakDtmDTHh2RoqVysvL v1 | XLSX SINGLE_JOB_REPORTED; no native 3-document proof | Studio |
| Extract original | Three separately saved purchase_order/delivery_notice/quotation raw JSON with SHA256 + Job/Step/Case/Config; or one native 3-doc container with source binding | NOT_PROVIDED | Studio |
| MergeDocuments original | Raw Step JSON bytes plus SHA and run IDs | NOT_PROVIDED | Studio |
| NormalizeDocuments original | Actual raw Step JSON with 3 document IDs/types and source-file metadata | NOT_PROVIDED | Studio |
| IndependentQA actual input | Raw Step Input JSON, exact QA Sandbox Job & Step, bytes SHA | NOT_PROVIDED | Studio |
| IndependentQA report | Actual raw QA report JSON, run provenance, document IDs and qa_status | NOT_PROVIDED | Studio |
| PDF | Three untouched original PDF bytes SHA256 + operational/QA upload receipts and file IDs | NOT_VERIFIED | Studio/Team2 |
| Team2 live provenance | Python execution output + exact original Native SHA sidecar | NOT_PROVIDED | Team2 |
| Human reviewed Gold | PDF page-grounded annotated extraction facts, reviewer and approval, source PDF SHA | NOT_PROVIDED | Team3 |
| E1 | Distinct confirmed Job, saved Config and exact B0 original PDF byte equality, all stages | NOT_RUN/NOT_PROVIDED | Studio |

## B. Executable QA CLI order
1. Never modify original Stage raw JSON. Copy to a local secured evidence folder and calculate actual SHA256 per file from original bytes.
2. Create stage manifest version leadtime-stage-intake/v1 referencing only relative raw paths. Existing seventh contract expects case_id=C001, operational_job_id, config_id, config_version and individual Stage SHA/job/step/case metadata. Extract may be a 3-branch object with independent branch Step IDs.
3. Stage preflight: python scripts/qa_stage_intake_check.py --manifest /evidence/stage_manifest.json
4. Then run the existing combined Python V6/QA/Provenance CLI with optional Stage binding:
   python scripts/qa_combined_e2e_check.py --operational-native /evidence/operational_native.json --trusted-base data/cases/SYN-C001/trusted_base_case.json --schema configs/schemas/document_extraction.schema.json --operational-job-id job_NCik8shwrgM93PDnNNYukT --case-id C001 --github-sha <ACTUAL_GIT_SHA> --stage-intake-manifest /evidence/stage_manifest.json
5. To validate actual cross-agent QA, add original --qa-native, --qa-report, --qa-agent-id, --qa-config-id, --qa-config-version; do not synthesize unsupported native. To prove original PDFs, add --team2-provenance, --qa-pdf-receipt, --operational-pdf-receipt and --pdf-root with genuine bytes.
6. When E1 exists, run manifest readiness plus exact raw Normalize binding:
   python scripts/qa_b0_e1_compare_check.py --b0 /evidence/B0_manifest.json --e1 /evidence/E1_manifest.json --b0-normalize /evidence/B0_normalize_original.json --e1-normalize /evidence/E1_normalize_original.json
7. Do not call a comparison IMPROVED if only type/field change is found. Human reviewed Gold is required to assess accuracy. Compare Config Diff and original PDF SHA and provenance independently.
8. Preserve JSON stdout and original-file SHA manifest, Markdown report and final Gate verdict. A Python or QA process exit code 2 may indicate BLOCKED/NOT_VERIFIED, not success of Studio live execution.

## C. Eight-pass operational safeguards
- Reject malformed Stage original bytes, incorrect SHA, conflicting Job/Config/Case/Step and mixed QA Input+Report Jobs.
- Check each unexpected Stage and Extract branch instead of silently ignoring it.
- Both stage_trace and the older input_delivery Normalize-to-IndependentQA checker now distinguish integer 0/1 from Boolean false/true using strict typed JSON equality. Neither result alone authenticates cloud transfer.
- Compare normalized documents by stable typed JSON serialization: false is not 0, arrays can legitimately be reorder-equivalent by document ID.
- If the optional Stage original fails: Python V6 is NOT_RUN by the combined CLI and no safety execution result is claimed.
- Missing original Normalize leaves uncertainty as BLOCKED and does not imply the cloud transmission failed.
- B0/E1 comparison requires matching local Normalize byte SHA against the side's manifest original_sha256, but even matching self-declared hashes DO NOT independently authenticate Studio provider uploads.
- Manifest input metadata bounded to 1 MiB, per original JSON Stage to 32 MiB, path traversal and out-of-folder symlinks fail. PDF original files are handled by the existing receipt/provenance path, not the JSON size cap.

## D. Current Release status
Stage Intake: SYNTHETIC_TEST_PASS / LOCAL_CONTRACT_PASS; ORIGINAL_RAW_VERIFIED=NO (new NCik); PROVIDER_EXECUTION_AUTHENTICATED=NO.
Python V6: LOCAL_ARCHIVED_PASS; current C001 new Job actual run NOT_VERIFIED.
IndependentQA/Cross-Agent: existing local contracts/pass regressions; actual input+report missing.
B0/E1: manifest/read-only diff verified synthetically, E1 real job NOT_PROVIDED, experimental result NOT_MEASURED.
Human Gold: BLOCKED. Actual Studio E2E: BLOCKED. Overall Release: BLOCKED.
