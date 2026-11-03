# LeadTime Guardian — 7th QA Release Gate Matrix
Date: 2026-11-01 KST. Base PR #7 commit 8628c96832900e6b8ea913bd072b90e6b9297209.
Seven-pass code tested SHA 2bb2619ed3c5de4027472bf286c3f13eaea7be9c. Actual GitHub CI https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41298864174 SUCCESS; full Python 569 PASS (including 380 independent QA PASS), QA and repo Ruff PASS, archived local checks successful. GitHub docs-only final commit requires its own final HEAD CI check.

| Gate | Latest Status | Evidence / source | Scope | Blocker; owner / next file |
|---|---|---|---|---|
| QA_CODE_GATE | PASS_AT_TESTED_SHA | 380 QA PASS and Ruff SUCCESS | local CI | final docs SHA CI; Team1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | preexisting original Team2 V6 integrated six modules, Team2 PR#12 unchanged | repository-local | Team2 live Python execution / provenance sidecar |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS_LOCAL | QA combined code with original Team2 V6; new Stage intake calls original Python path | local code | production original repo integration approval |
| COMBINED_CODE_CI_GATE | PASS_AT_TESTED_SHA | 569 full Python PASS incl QA, Ruff PASS, actions #41298864174 | code CI | final docs HEAD CI separately |
| OFFLINE_E2E_GATE | PASS_LOCAL | archived C001 replay, synthetic negative evidence and source checks | offline | Not NCik live Studio |
| XLSX_49_ANALYSIS_GATE | PASS_LOCAL_OOXML | actual XLSX SHA ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb; 22 pointer49->empty, 0 literal49 | original XLSX bytes | Stage origin of empty strings UNKNOWN; Studio |
| EXTRACT_SCHEMA_GATE | FAIL_STATIC_DRAFT_CONTRACT | preserved v4 DRAFT descriptions contradictory with nonnullable types | static, not current run | saved NCik B0 v1 and Studio UI nullable support; Studio |
| B0_SINGLE_JOB_GATE | SINGLE_JOB_REPORTED_XLSX | NCik Job ID with three PDF rows in XLSX | observed export structure | original Native 3-doc grouping, provider file IDs; Studio |
| NORMALIZE_QA_INPUT_GATE | NOT_VERIFIED | new local Stage trace & existing input_delivery contracts | synthetic CI | original Normalize/QA actual INPUT bytes/Step IDs; Studio |
| B0_E1_COMPARISON_GATE | BLOCKED | readiness + local optional Normalize field diff tested | synthetic CI | E1 real Job and same exact original PDF SHA, config/step raw, Gold; Studio/Team3 |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | Studio reported C001 only, raw Native not provided | external run | Native Normalize 3 docs exact original bytes; Studio |
| STUDIO_PROVENANCE_GATE | BLOCKED | local source IDs/PDF sidecar checks preserved | local contract | actual PDF originals, receipt file IDs + Team2 Sidecar; Studio/Team2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL | Team2 V6 analyze/validate + portfolio QA, archived C001 | offline V6 | NCik actual Python run and underlying document evidence; Team2 |
| CROSS_AGENT_GATE | BLOCKED | cross_agent validators, QA manifest, new optional stage-binding | synthetic CI | actual independent QA native Input+Report + source provenance; Studio/Team1 |
| HUMAN_GOLD_GATE | BLOCKED | no reviewed truth in current task | human | Human-reviewed Gold, pages, PDF digest, reviewer/date; Team3 |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | no real current NCik raw/QA Step+Provenance | live unknown | exact original B0 stage exports and verified PDF upload chain |
| OVERALL_RELEASE_GATE | BLOCKED | code CI success is not release authorization | release | external live proof, human Gold, sign-off; Team1 |

Additional policy: The original operational and QA Sandbox Job IDs can differ without an automatic provenance error. Same-case metadata, per-Stage SHA and source-file content must bind correctly; arbitrary old Studio replay files must not be described as a new NCik run. QA Step COMPLETED != document QA PASS. LOCAL_CONTENT_MATCH != provider-authenticated delivery. A comparison change != Gold accuracy improvement. No Studio runs, archive modifications, main merges or release submissions were performed.

## Recommended next responsible actions
Studio: preserve B0 Config v1 and existing NCik Job. Export original Extract branch3/Merge/Normalize/IndependentQA Input+Report, with each source SHA and Step ID. Report any unexportable artifacts as NOT_PROVIDED, not fabricated success.
Team2: original operating Studio Native + Python execution output + provenance sidecar and PDF identities; do not change frozen engine to satisfy the tests.
Team3: source-PDF page-grounded Human-reviewed Gold + reviewer/time/version and original PDF SHA.
Team1: run qa_stage_intake_check.py, then qa_combined_e2e_check.py with --stage-intake-manifest, and compare B0/E1 only after actual E1 data exists and original PDF byte digests are grounded. Keep release BLOCKED until full evidence chain and explicit sign-off.
