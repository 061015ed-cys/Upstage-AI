# Team2 V6 + QA Combined Candidate — Release Gates (2026-11-01)

**All statuses attached to exact staged code HEAD `bdcdac48a39a73ee72f19936818648eae1813c90`**; GitHub Actions run #41291094905 (SUCCESS). Later documentation commits do not change that test claim until independently checked.

| Gate | Status | Verified evidence | Remaining blocker / owner |
| --- | --- | --- | --- |
| QA_CODE_GATE | PASS | QA 315 pytest + QA Ruff | code evidence only / Team1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | exact six source blobs from PR#12, 504 whole Python pytest | actual operating V5 live Job / Team2 |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS | six core source Blob SHAs identical to PR#12; old QA preserved; exact combined HEAD | official original-repo integration not executed / Team1+Team2 |
| COMBINED_CODE_CI_GATE | PASS | GitHub Actions 41291094905 at combined HEAD | original-repo release branch CI still NOT_RUN |
| OFFLINE_E2E_GATE | PASS_LOCAL | C001 archived, C013/C017/C008 DRAFT, combined CLI + QA reference | no new Studio measured accuracy |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | QA copy reported NOT_VERIFIED/PARTIAL on prior historical C001 | actual raw QA native+report+Step/Config / Studio AI |
| STUDIO_PROVENANCE_GATE | BLOCKED | local SHA/ID binding logic implemented | original PDF byte SHA + job-specific upload receipts / Studio+Team2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL | independent local numeric audit and blocked path, V6 tests | actual current Python Job + source evidence / Team2 |
| CROSS_AGENT_GATE | BLOCKED | raw mapping and strict manifest tests | actual QA raw pair, same source PDF provenance, Python independent evidence / Team1 |
| HUMAN_GOLD_GATE | BLOCKED | only DRAFT case labels | human reviewed source-page field Gold / Team3 |
| OVERALL_RELEASE_GATE | BLOCKED | local Gate outputs BLOCKED, no approval | all above + G9 human sign-off |

`PASS_LOCAL` is a scope qualifier, **never Actual Studio PASS**.
No automatic merge, release, email, purchase or Studio paid run is authorized.


## 4차 Studio-B0 실제 관측 및 QA PR#5 통합 Gate (2026-11-01)

**코드 검증 SHA:** e5d07bb9e86ef98e20821dcbd10abf57273af7eb  
**실측 근거:** 사용자가 전달한 Studio AI B0-C001 완료 Job 3개(서로 다른 PDF/Job). Original Native bytes, actual QA report, original PDF upload receipts **미확보**. 이는 3차 보관 C001 Job이 아님.  
**CI:** QA copy PR#5 commit e5d07bb; GitHub Actions #41292849737 SUCCESS; QA pytest 330 PASS, full Python pytest 519 PASS (includes QA tests); QA Ruff and repository Ruff PASS; archived C001 replay PASS; existing conservative local gate overall_status=BLOCKED.

| Gate | State | Scope / owner |
|---|---|---|
| QA_CODE_GATE | PASS | new grouping/provenance QA and 330 tests at e5d07bb, Team1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | source Team2 PR#12 unchanged, 519 whole-tree tests, Team2 live result NOT_VERIFIED |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS | original six Team2 PR#12 source files remain identical; no new Team2 SHA, Team1 |
| COMBINED_CODE_CI_GATE | PASS_AT_e5d07bb | GitHub #41292849737; latest docs-only HEAD needs its own CI |
| OFFLINE_E2E_GATE | PASS_LOCAL | archived C001 and synthetic C013/C017/C008; split B0 report blocked |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | actual new B0 QA step completed, qa_status UNKNOWN / Studio AI |
| STUDIO_PROVENANCE_GATE | BLOCKED | original Native, original PDF bytes/SHA/2 upload receipts unavailable / Studio + Team2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL | Python V6 + independent portfolio reference, not actual current Python Job |
| CROSS_AGENT_GATE | BLOCKED | actual QA Normalize raw + IndependentQA report unavailable / Team1 |
| HUMAN_GOLD_GATE | BLOCKED | human-reviewed, SHA-grounded field Gold absent / Team3 |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | B0-C001 batchRunCount=3 separate Jobs; E1 NOT_RUN / Studio AI |
| OVERALL_RELEASE_GATE | BLOCKED | actual same-case Studio source proofs, Human Gold and human release approval absent |

This current gating cannot be promoted by any older successful offline CI, identical file names, or by copying prior NOT_VERIFIED/PARTIAL verdicts. A new single-Job B0 and comparable E1 must be measured only when the correct case grouping is proven and source PDF SHA equality is grounded.
