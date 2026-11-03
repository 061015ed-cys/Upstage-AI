# LeadTime Guardian — 7차 GitHub 통합 개발 및 회귀 결과
Date: 2026-11-01 KST

## 1. Confirmed GitHub baseline and isolation
- Sixth PR #7 HEAD: 8628c96832900e6b8ea913bd072b90e6b9297209 (GitHub Actions #41297086072 SUCCESS, 546 Python/357 QA tests)
- Team2 original Python V6 PR #12 HEAD: e9b9992b593a42d427ff1bbadeb9a9866ca593bd
- Original operations PR #11 HEAD: f196c694917f2d9e5f4ec228c752bd3f2a4eb882
- New isolated seventh Draft PR #8: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/8
- Branch: feat/qa-seventh-raw-stage-e2e-20261101, based directly on sixth PR #7
- Current verified code SHA: 2bb2619ed3c5de4027472bf286c3f13eaea7be9c
- Actual code CI #41298864174: SUCCESS; 380 independent QA pytest PASS, 569 whole Python pytest PASS (QA tests included, not additional), QA Ruff PASS, repository Ruff PASS, C001 archive replay/local integration checks completed with local_checks_passed=true and overall_status=BLOCKED.
- After documentation commits, verify the final HEAD's separate CI and use that result as the final proof.
- No merge, force push, original operations PR #11, Team2 PR #12, QA PR #4/#5/#6/#7, Studio Config, user PDF/XLSX, or Human Gold alteration.

## 2. Audit of existing runnable path
Prior scripts/qa_combined_e2e_check.py already performs strict original operational Native JSON intake, documents_from_export, Python V6 analyze_studio_documents, apply_studio_extractions + validate_documents, independent portfolio QA, optional QA Native+Report cross-agent handoff, and actual source-file-ID/receipt/sidecar PDF hash provenance checks. No new Python calculation engine was written.
Deficiencies confirmed in the seventh inspection:
1. Existing single-file integration could not record original Extract->Merge->Normalize->actual IndependentQA INPUT field evolution in one evidence-bound manifest.
2. Previous scripts/qa_b0_e1_compare_check.py only checked manifest eligibility and never compared supplied raw Normalize field values/type.
3. Raw Normalize Step content and operational Native content could be checked separately, but a same-case semantic content SHA binding was not available as one optional CLI argument.
Corrections are in the next sections.

## 3. Strict Stage intake — source-bytes first
New module src/leadtime_guardian/qa/stage_trace.py; new CLI scripts/qa_stage_intake_check.py.
Expected manifest schema_version: leadtime-stage-intake/v1, case_id C001, operational_job_id job_*, config_id cfg_*, config_version positive integer, stages mapping.
Accepted Stages: Extract, MergeDocuments, NormalizeDocuments, IndependentQA_Input, IndependentQA_Report.
Each provided stage requires SHA-256 of original raw bytes, job_id, step_run_id and case_id. Extract, Merge and Normalize also require the same operational_job_id, config_id and config_version; QA input/report may legitimately use their own QA Sandbox job ID.
Extract can be a single original payload containing a three-document collection, OR a manifest mapping of the three separately saved purchase_order/delivery_notice/quotation original branch JSON files with distinct original SHA and Step ID. Do not synthesize a supposed provider-native combined Extract from three independent Job runs.
The CLI reads only manifest-relative paths and rejects escape outside the manifest directory. JSON parsing rejects duplicate keys and malformed text. A missing stage is NOT_PROVIDED/BLOCKED; raw SHA, Job, Config, Case or Document ID mismatch is FAIL. Each of the three C001 document IDs must be present and distinct. The source is a local raw file, never independently authenticated Upstage Cloud execution.
Command:
    python scripts/qa_stage_intake_check.py --manifest /path/to/local/stage_manifest.json

Example manifest structure (PLACEHOLDERS only; never copy these fake IDs/hashes into real evidence):
    {
      "schema_version":"leadtime-stage-intake/v1",
      "case_id":"C001",
      "operational_job_id":"job_ACTUAL",
      "config_id":"cfg_ACTUAL",
      "config_version":1,
      "stages":{
        "Extract":{"branches":{
          "purchase_order":{"path":"extract_po.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_ACTUAL","step_run_id":"actual_extract_po_id","case_id":"C001","config_id":"cfg_ACTUAL","config_version":1},
          "delivery_notice":{"path":"extract_notice.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_ACTUAL","step_run_id":"actual_extract_notice_id","case_id":"C001","config_id":"cfg_ACTUAL","config_version":1},
          "quotation":{"path":"extract_quote.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_ACTUAL","step_run_id":"actual_extract_quote_id","case_id":"C001","config_id":"cfg_ACTUAL","config_version":1}
        }},
        "MergeDocuments":{"path":"merge.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_ACTUAL","step_run_id":"merge_step","case_id":"C001","config_id":"cfg_ACTUAL","config_version":1},
        "NormalizeDocuments":{"path":"normalize.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_ACTUAL","step_run_id":"normalize_step","case_id":"C001","config_id":"cfg_ACTUAL","config_version":1},
        "IndependentQA_Input":{"path":"qa_input.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_QA","step_run_id":"qa_input_step","case_id":"C001"},
        "IndependentQA_Report":{"path":"qa_report.json","sha256":"<SHA256_OF_ORIGINAL_BYTES>","job_id":"job_QA","step_run_id":"qa_report_step","case_id":"C001"}
      }
    }
The actual Studio Native file format can differ; unsupported wrappers remain blocked until the original format is inspected. An illustrative placeholder is NOT proof of a runtime interface.

## 4. The 22 originally misread XLSX fields
Preserved XLSX source SHA: ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb. All 22 apparent value-49 cells point to zero-based sharedStrings[49], which resolves to EMPTY_STRING, not literal string "49".
Stage trace keeps values and states separately: MISSING, NULL, EMPTY_STRING, STRING_NULL, STRING_ZERO, NUMBER_ZERO, ACTUAL_VALUE, INVALID_TYPE; nested quote arrays are not arbitrarily flattened when multiple elements exist.
It reports each cell/header/document type and observed Extract, Merge, Normalize, QA Input value/type. 'first_observed_conversion' is only an adjacent local evidence difference, not a causal model hallucination claim. Missing intermediary steps remain UNKNOWN.
Current real B0 Native raw Step JSON is still NOT_PROVIDED, so no new actual conversion origin is established.

## 5. Cross-Agent / Python V6 integration
Modified existing scripts/qa_combined_e2e_check.py adds OPTIONAL --stage-intake-manifest, without changing its required operational Native, base case, schema, original job, case, github sha arguments.
It calls the exact same read-only stage intake, records local Stage findings, rejects Stage failed SHA/case/job/step contracts, and calculates a canonical semantic documents SHA for Normalize and the strict parsed operational Native. Differing three-document values fail with NATIVE_AND_NORMALIZE_CONTENT_MISMATCH even if document IDs match.
If original Stage input is missing, the combined status stays BLOCKED and the missing evidence is recorded. This does NOT certify the original Studio transfer, source PDF or Human Gold. A QA Sandbox Job legitimately differs from the operating Job; cross-Job is rejected only when operational Extract/Merge/Normalize identities conflict.
Existing team2 V6 validation, Python safety independent QA, Cross-Agent handoff, and PDF Source File ID/Upload receipt checks are reused. Existing CLI flags remain valid.
Example additional flag:
    python scripts/qa_combined_e2e_check.py --operational-native ORIGINAL_NATIVE.json --trusted-base TRUSTED_C001.json --schema configs/schemas/document_extraction.schema.json --operational-job-id job_ACTUAL --case-id C001 --github-sha ACTUAL_40CHAR_GITHUB_SHA --stage-intake-manifest stage_manifest.json

## 6. B0/E1 comparison now supports optional original Normalize field diff
Modified src/leadtime_guardian/qa/experiment_compare.py and scripts/qa_b0_e1_compare_check.py. Existing --b0 and --e1 manifest-only readiness remains unchanged.
Optional --b0-normalize ORIGINAL_B0_NORMALIZE.json --e1-normalize ORIGINAL_E1_NORMALIZE.json inputs perform strict local type-aware value diffs, only when same Case C001 and manifest-reported three original PDF SHA tuples match, and no read-only manifest ERROR exists. It rejects duplicate document IDs, different document IDs/types and cross-case input. Each changed leaf path records original value and JSON type, including null->empty and integer 0->boolean False.
Even complete self-reported manifests and original local JSON do NOT authenticate provider upload PDF bytes or gold accuracy. A change is CHANGED_UNVERIFIED; no Human Gold means improvement verdict and accuracy NOT_MEASURED, overall eligibility and release BLOCKED. Unchanged values are UNCHANGED locally, not an accuracy PASS.
Example:
    python scripts/qa_b0_e1_compare_check.py --b0 B0_MANIFEST.json --e1 E1_MANIFEST.json --b0-normalize B0_NORMALIZE.json --e1-normalize E1_NORMALIZE.json
As of 2026-11-01, E1 actual Job/Native results are NOT_PROVIDED or NOT_RUN.

## 7. Regression proof and limitations
At code SHA 2bb2619ed3c5de4027472bf286c3f13eaea7be9c: GitHub Actions SUCCESS, QA pytest 380 PASS, full Python pytest 569 PASS, both Ruff PASS; archived C001/local integration evidence PASS_LOCAL, overall gate BLOCKED.
New tests cover missing stages, strict double JSON keys, raw SHA mismatches, different operational Job mixed into Extract/Merge, 3 separate Extract branches and Step IDs, crossed Case, QA input content mismatch, path traversal, null/empty/0/boolean type distinction, B0/E1 field change without accuracy claim, and combined Native-vs-Normalize value mismatch. Fixtures are SYNTHETIC_ONLY and not current Studio Native.
Full-suite pytest includes existing C001/C013/C017/C008 and Python V6/strict JSON/adapter/QA/Cross-Agent/Provenance test groups. CI provided whole-suite proof; no separate per-case count is asserted.
Team2 PR #12 core original source was not modified. Latest actual Studio B0 Job job_NCik8shwrgM93PDnNNYukT remains SINGLE_JOB_REPORTED_FROM_XLSX, Native 3 docs NOT_VERIFIED; raw Extract/Merge/Normalize/QA actual Input+Report, PDF upload receipts, Team2 live sidecar, Team3 Human-reviewed Gold missing.
No new Studio Jobs, paid execution, original XLSX/PDF/Gold upload or release action performed.

## 8. Remaining gates
QA_CODE_GATE PASS_AT_CODE_SHA; TEAM2_ENGINE_GATE PASS_LOCAL; COMBINED_SOURCE_COMPATIBILITY_GATE PASS_LOCAL; COMBINED_CODE_CI_GATE PASS_AT_CODE_SHA; OFFLINE_E2E_GATE PASS_LOCAL.
XLSX_49_ANALYSIS_GATE PASS_LOCAL_OOXML; EXTRACT_SCHEMA_GATE FAIL_STATIC_DRAFT_CONTRACT; B0_SINGLE_JOB_GATE SINGLE_JOB_REPORTED; NORMALIZE_QA_INPUT_GATE NOT_VERIFIED; B0_E1_COMPARISON_GATE BLOCKED.
STUDIO_DOCUMENT_GATE NOT_VERIFIED; STUDIO_PROVENANCE_GATE BLOCKED; PYTHON_SAFETY_GATE PASS_LOCAL; CROSS_AGENT_GATE BLOCKED; HUMAN_GOLD_GATE BLOCKED; ACTUAL_STUDIO_E2E_GATE BLOCKED; OVERALL_RELEASE_GATE BLOCKED.
Do not clear gates solely because tests, model output or a Studio Step show COMPLETED.

See docs/STUDIO_SUPPORT_DELTA_SEVENTH_20261101.txt and docs/SEVENTH_FINAL_CHECKPOINT_20261101.json.
