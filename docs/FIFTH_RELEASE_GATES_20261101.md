# LeadTime Guardian — 5th QA Gate Matrix (2026-11-01)

Source baseline Team2 PR#12 e9b9992b593a42d427ff1bbadeb9a9866ca593bd, previous combined QA PR#5 5ecf6de67e0a5313590e1316ad15700daaacd114. No modifications to these refs.
Fifth actual code tested SHA a8b2096d665675daa3e63b5c2db7ae7acbdd3fd9, GitHub Actions #41295389475 SUCCESS, 353 independent QA / 542 full Python pytest PASS, QA and repo Ruff PASS, Archived C001 Offline Replay and local gate checks PASS_LOCAL. All reports after this code SHA require exact latest final SHA CI recheck.

| Gate | Status | Scope / evidence | Unresolved / owner |
|---|---|---|---|
| QA_CODE_GATE | PASS_AT_CODE_SHA | 353 pytest, Ruff PASS | New docs HEAD requires its own CI, Team1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | six original Team2 V6 source Blob match previously confirmed; original PR#12 unchanged | Current actual Python Job, Team2 |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS_PRIOR_BASELINE | Fourth merged code on PR#5 and fifth QA extensions | Release candidate original-repo CI not executed, Team1/Team2 |
| COMBINED_CODE_CI_GATE | PASS_AT_CODE_SHA | 542 whole suite, GitHub run #41295389475 | New docs-only SHA requires recheck |
| OFFLINE_E2E_GATE | PASS_LOCAL | C001 archived replay, synthetic negative cases and receipt checks | Not NCik live E2E |
| B0_SINGLE_JOB_GATE | SINGLE_JOB_REPORTED | New job_NCik8shwrgM93PDnNNYukT per Studio AI report, three input PDF names | Native 3-document original bytes / Studio |
| EXTRACT_SCHEMA_GATE | FAIL_STATIC_CONTRACT | Four v4 DRAFT Extract branch descriptions vs JSON type conflicts | Actual B0 Saved Config + Studio nullable support / Studio |
| NORMALIZE_QA_INPUT_GATE | NOT_VERIFIED | WIP + hardened local payload contracts/test | Actual two Step raw inputs/QA Report / Studio |
| B0_E1_COMPARISON_GATE | BLOCKED | Comparison manifest gate implemented; E1 not run | Native/Step/PDF SHA and E1 / Studio |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | No actual NCik normalized document array | Exact Native/Extract/Merge/Normalize raw / Studio |
| STUDIO_PROVENANCE_GATE | BLOCKED | Code rejects case/job/PDF receipt mismatch | Actual original PDF SHA + two Job receipts / Studio/Team2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL | Team2 V6 plus independent numeric QA on archived/synthetic | Actual current operating Job/Python sidecar / Team2 |
| CROSS_AGENT_GATE | BLOCKED | QA adapters local contract; no actual NCik report | Raw IndependentQA Input+Report / Team1/Studio |
| HUMAN_GOLD_GATE | BLOCKED | DRAFT only | Human-reviewed PDF-page/source-SHA Gold / Team3 |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | Single B0 Job reported but no Native/PDF/QA raw | Current raw Job original evidence |
| OVERALL_RELEASE_GATE | BLOCKED | Local success does not authorize release | All above + explicit release sign-off |

Specific stale assumptions disallowed: old B0 three split Jobs cannot be combined; archived 2026-10-30 C001 V4 is not NCik; draft Config is not a provider-run record; user-reported Job and reported PDF filenames alone do not authenticate original PDF bytes. XLSX 49 causal origin UNKNOWN, original workbook and Step outputs not provided. No new Studio credit, workflow mutation, main merge, force push, source PDF/Gold edits, or external submission.
