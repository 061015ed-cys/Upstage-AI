# LeadTime Guardian — 8차 GitHub 집중 통합 안정화 개발 결과
Date: 2026-11-01 KST. Scope: isolated QA GitHub code only, NOT a new Studio execution.

## Repository and evidence
- QA copy: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy
- Baseline: Draft PR #8, commit 4528a75141320ba9f4d3980c0ea4ca3127703852, original CI https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41299178119 (569 full Python / 380 QA PASS).
- Eighth isolated branch: feat/qa-eighth-release-hardening-20261101.
- Eighth Draft PR #9: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/9
- Source code tested SHA: 72408d9afb3c3cbe755c5d181da0b016594e6df7.
- Tested run: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41302028422, CI SUCCESS; 392 QA pytest PASS, 581 full Python pytest PASS (QA included), QA Ruff PASS, entire repo Ruff PASS, C001 archived replay and local integration checks succeed; overall integration gate BLOCKED.
- Final documentation commits change HEAD. For true final CI cite the latest PR #9 HEAD and GitHub Actions run for that exact SHA; do not represent this code-only run as a later docs-commit run.

## Findings: actual defects and bounded fixes
1. **False equality of false and 0**. In seventh src/leadtime_guardian/qa/stage_trace.py, Normalize vs QA Input documents were compared with native Python dict equality. In Python, False == 0 (and True == 1), meaning a changed quantity type could erroneously report LOCAL_CONTENT_MATCH. Replaced with canonical type-aware SHA256 over JSON-serialized normalized documents, sorted by document type and ID. A change from numeric 0 to JSON false now FAILS. Legitimate document array reorder still matches locally. These hashes are semantic content hashes, NOT SHA256 of original file bytes.
Additional last-path finding: the pre-existing src/leadtime_guardian/qa/input_delivery.py audit_normalize_qa_input also used Python list equality (where False == 0 and True == 1) independently of stage_trace. Eighth fixed this separate active checker with type-aware canonical JSON comparison while preserving the previous wrapper/Case/duplicate-ID contract. Added two regression cases in tests/test_qa_input_delivery_strict_case.py.
2. **Python invoked before evidence preflight**. In seventh scripts/qa_combined_e2e_check.py, --stage-intake-manifest was validated only AFTER audit_combined_bytes had already run operational Python V6. Moved into preflight_stage_before_python: missing stages remain BLOCKED and may allow safe local archived replay; SHA, Job, C001 Case, or Normalized content mismatch now aborts before V6 execution and reports python_safety_status NOT_RUN. Existing CLI without optional manifest remains backward-compatible.
3. **B0/E1 Normalize raw not SHA-bound**. In seventh comparison, user-supplied B0/E1 raw JSON could be replaced without matching per-side NormalizeDocuments original_sha256 in the evidence manifest. Existing original manifest checks were self-reported, but no local raw bytes were bound. Updated scripts/qa_b0_e1_compare_check.py to hash exact original Normalize files and compare with Step SHA, and validate any present Job/Step/Config metadata against manifest. New audit fields normalized_original_sha256_by_side and normalized_job_metadata_by_side. A mutated raw or wrong Job blocks local diff; a successfully bound local diff is still CHANGED_UNVERIFIED, not improved extraction.
4. **Cross-Job contamination and silent duplicate Step IDs**. Stage trace now rejects identical (Job, StepRunID) across different Stage evidence, QA Input vs QA Report job inconsistency, unexpected Stage keys and unlisted Extract document branches. Operational Job and QA Sandbox Job are legitimately distinct; the restriction is on contradiction within an execution pair.
5. **Unbounded raw file intake**. scripts/qa_stage_intake_check.py now bounds manifest metadata to 1 MiB and each original JSON Stage to 32 MiB, protects manifest-relative paths against symlink escapes, and fails closed on malformed deeply nested JSON/RecursionError. Size limits apply to JSON evidence, not PDF files, and can be reviewed for exceptionally large real data.

## Existing systems deliberately reused unchanged
- src/leadtime_guardian/studio_integration.py + studio_adapter.py + engine.py: original Team2 Python V6 calculation, document schema, dates, PO/receipt and quote validation.
- leadtime_guardian/strict_json.py: strict parser reused rather than replaced.
- src/leadtime_guardian/qa/input_delivery.py: existing QA step input adapter and wrappers.
- src/leadtime_guardian/qa/cross_agent.py, studio_batch.py and provenance_link.py: existing Cross-Agent, batch and original PDF upload receipt / SHA constraints.
- qa_combined_e2e_check.py remains the combined Python safety, independent portfolio QA and Cross-Agent offline CLI; new preflight does not replace its safety gates.
- qa_b0_e1_compare_check.py maintains optional Normalize diff and no Human-reviewed Gold quality claim.

## Changed implementation and regression files
- src/leadtime_guardian/qa/stage_trace.py
- scripts/qa_stage_intake_check.py
- scripts/qa_combined_e2e_check.py
- src/leadtime_guardian/qa/experiment_compare.py
- scripts/qa_b0_e1_compare_check.py
- tests/test_qa_stage_trace.py
- tests/test_qa_seventh_combined_stage_cli.py
- tests/test_qa_seventh_experiment_diff.py
- docs/EIGHTH_GITHUB_DEVELOPMENT_REPORT_20261101.md
- docs/EIGHTH_INTEGRATION_READINESS_20261101.md
- docs/EIGHTH_FINAL_REGRESSION_REPORT_20261101.md
- docs/STUDIO_SUPPORT_DELTA_EIGHTH_20261101.txt
- docs/EIGHTH_RELEASE_GATE_MATRIX_20261101.md
- docs/EIGHTH_FINAL_CHECKPOINT_20261101.json

## Critical limits preserved
- Live B0 Job is job_NCik8shwrgM93PDnNNYukT, Config cfg_X2xXakDtmDTHh2RoqVysvL v1, one Job with three PDF names in an XLSX export, but no original current NormalizeDocuments Native or QA actual raw.
- Original B0 XLSX SHA ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb. Its 22 apparent 49 cells contain sharedStrings index 49 resolving to EMPTY STRING; literal STRING_49=0, NUMBER_49=0. No incorrect old 'LLM 49 hallucination' narrative.
- The local code's 581/392 PASS does not establish native cloud Job authenticity, PDF page Gold accuracy, correct Studio source file receipts, a true B0/E1 experimental improvement, or production release authorization.
- Original user XLSX/PDF/Native/Human Gold never modified or uploaded; no Studio paid execution, PR merge, force push, Team2 original repository writes or branch overwrite.

## Continuation
See EIGHTH_INTEGRATION_READINESS and STUDIO_SUPPORT_DELTA_EIGHTH for Stage evidence collection, and EIGHTH_RELEASE_GATE_MATRIX for actual incomplete gates.
