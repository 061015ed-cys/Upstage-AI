# LeadTime Guardian — 8차 제출 전 Release Gate Matrix
Date: 2026-11-01 KST. 8차 Draft PR #9, based on QA PR #8 HEAD 4528a75141320ba9f4d3980c0ea4ca3127703852.
Last tested code SHA 72408d9afb3c3cbe755c5d181da0b016594e6df7, CI https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41302028422 SUCCESS, 581 all Python + 392 included QA tests PASS and QA/all Ruff PASS.
Recheck final documentation HEAD and its own CI separately. Local source checks and CI do not authenticate Upstage Live.

| Gate | State | Evidence/Scope | Blocker / owner / next artifact |
|---|---|---|---|
| QA_CODE_GATE | PASS_AT_CODE_SHA | QA 392 PASS, QA Ruff PASS | Final docs SHA CI, Team1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | Team2 original V6 source unchanged, archived engine tests | Actual NCik Python analysis and V6 provenance sidecar, Team2 |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS_LOCAL | Existing Team2 engine combined with independent QA code; before-execution Stage preflight | Production integration sign-off, Team1/Team2 |
| COMBINED_CODE_CI_GATE | PASS_AT_CODE_SHA | GitHub Actions full Python 581 PASS and Ruff PASS | Final documentation HEAD own CI, Team1 |
| OFFLINE_E2E_GATE | PASS_LOCAL | Archive C001 replay + synthetic Stage/QA/Type/SHA negative cases | Do not confuse with new Native Studio |
| XLSX_49_ANALYSIS_GATE | PASS_LOCAL_OOXML | Real XLSX original SHA ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb; 22 shared index49 EMPTY_STRING | Stage causal origin UNKNOWN, Studio |
| EXTRACT_SCHEMA_GATE | FAIL_STATIC_DRAFT_CONTRACT | Preserved v4 Draft null-descriptions conflict with declared string/integer/array schema types | Verify real saved B0 v1 and nullable Studio UI, Studio |
| B0_SINGLE_JOB_GATE | SINGLE_JOB_REPORTED_XLSX | Job NCik single row, three Extract branch rows in source XLSX | Three-doc Native + source file IDs from one Job, Studio |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | No current raw Normalize Native three documents | Original saved Step original JSON bytes and SHA, Studio |
| NORMALIZE_QA_INPUT_GATE | NOT_VERIFIED | Local typed-content and QA Job-binding regressions pass | Actual IndependentQA input bytes and QA report, Studio |
| B0_E1_COMPARISON_GATE | BLOCKED | Same-PDF manifest, exact Normalize raw SHA and type diff implemented locally | E1 real Job + original PDF byte SHA and Config Diff, Studio / Team3 |
| STUDIO_PROVENANCE_GATE | BLOCKED | Original PDF SHA/upload receipt and sidecar validators run locally | Actual 3 PDFs/receipts/Team2 source sidecar, Studio / Team2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL | Existing V6/QA and Stage preflight tests, archived C001 | New NCik execution + verified provenance, Team2 |
| CROSS_AGENT_GATE | BLOCKED | Existing Cross-Agent handoff and QA identity tests locally pass | QA Sandbox original Native+Report+execution link, Studio / Team1 |
| HUMAN_GOLD_GATE | BLOCKED | No PDF-grounded reviewer-approved Gold for live NCik/E1 | Team3 original PDF SHA+page citations+reviewer |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | Studio raw and QA execution not yet provided | Complete Step+Native+receipt+Sidecar and Human Gold, Studio/Team2/Team3 |
| OVERALL_RELEASE_GATE | BLOCKED | Code CI PASS not Studio real data PASS | User/team human signoff after all required real evidence |

## Single-Job and source-integrity facts
- Case C001. Job job_NCik8shwrgM93PDnNNYukT, Config cfg_X2xXakDtmDTHh2RoqVysvL v1 are reported with XLSX structure, not authenticated from original Upstage 3-doc Native.
- 22 raw XML <v>49</v> references are not literal numeric/text 49. All resolve to empty sharedStrings[49]; do not reintroduce a hallucination root-cause claim.
- Real Extract/Merge/Normalize/IndependentQA raw and E1 comparison fields currently NOT_PROVIDED/NOT_MEASURED; 8th validation harness is ready to inspect them, not evidence that they have been provided.
- QA Step COMPLETED is not PASS; normalized local content match is not provider delivery authentication.
- A locally consistent pair of B0/E1 original file SHA and manifest IDs does not prove actual PDF byte identity or improved extraction accuracy without source review.
- No paid Studio run, original XLSX/PDF modifications, force push, GitHub merge, Human Gold fabrication or original Team2 PR modification.

## Next gated action
Studio owner: export exact original existing NCik Job Stages and PDF source receipt bytes, without rerunning B0.
Team2 owner: provide operational Native->Python V6 result with original-byte SHA sidecar and unchanged authoritative engine.
Team3 owner: produce reviewed PDF-page-grounded Gold (SHA/reviewer/version).
Team1: run qa_stage_intake_check.py and qa_combined_e2e_check.py with --stage-intake-manifest before any B0/E1 quality claim; check final HEAD GitHub Actions, then keep Release BLOCKED until actual proofs are received.
