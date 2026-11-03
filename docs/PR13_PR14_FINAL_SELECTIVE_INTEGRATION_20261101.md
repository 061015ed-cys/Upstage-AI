# LeadTime Guardian — PR #13·#14 최종 선택적 통합 검토

**Date:** 2026-11-01 KST. **Repo:** `dohun3540-crypto/leadtime-guardian-agent.copy`.
**Result:** PR #13 기준을 유지하고 PR #14의 Studio QA Adapter 변경만 선별 반영. **No merge, no force-push, no original PR mutation.**

## 1. 실제 PR 근거

| Source | HEAD | Base | GitHub CI |
| --- | --- | --- | --- |
| Freeze PR #11 | `585142e718b444cbbd3e43d3c2b5e42d68637450` | `feat/qa-ninth-release-readiness-20261101` | #41307188645 SUCCESS, Python 600 / QA 411 |
| Selective PR #13 | `d07771ebb28aaf34026fc6a28322e424b110ea18` | `feat/qa-tenth-final-code-freeze-20261101` | #41308800589 SUCCESS, Python 617 / QA 428 |
| Parallel PR #14 | `62c68e1a6d9630d027e7acc64989b27972ab5cbe` | `feat/qa-tenth-final-code-freeze-20261101` | #41309031347 SUCCESS, Python 627 / QA 438 |
| Consolidated Draft PR #15 | See latest PR #15 head | `feat/qa-cross-review-pr12-integration-20261101` | Code run #41310125056 SUCCESS, Python 630 / QA 441 |

PR #13 vs PR #14 compare: Git reports `diverged`, ahead 6 / behind 6 (from PR #13 to #14). Both descend from the same PR #11 snapshot but their later commits are not linearly compatible. Test totals are not evidence that one branch is inherently superior.

## 2. PR13_TO_PR14_COMPATIBILITY_MATRIX

| Contract | PR #13 | PR #14 | Final resolution |
| --- | --- | --- | --- |
| tuple ≠ list | `_is_strict_json_tree` | `_strict_json_value` equivalent | **ALREADY_IMPLEMENTED**: retain PR #13 |
| integer dict key vs string key | Strict built-in string key | Same safety check | **ALREADY_IMPLEMENTED**: retain PR #13 |
| 0/false, 1/true | Canonical JSON typed compare | Canonical JSON typed compare | **ALREADY_IMPLEMENTED** |
| 100 vs 100.0 | Different representation in local input | Same | **ALREADY_IMPLEMENTED** |
| null/empty string | Strict comparison | Same | **ALREADY_IMPLEMENTED** |
| array order/object key order | Array order preserved, object order canonicalized | Same | **ALREADY_IMPLEMENTED** |
| Wrapper, `expected_case_id`, duplicate document IDs | Preserved | Same common base | Retain PR #13 (unchanged) |
| Raw QA Report Provenance and Cross-Agent | Existing source check | Existing source check | Retain PR #13 (unchanged) |
| Lowercase issue severity | Strict uppercase only, structural FAIL | Map only known lowercase `info/warning/error` to uppercase with explicit WARNING and review | **SELECTIVE_FIX** in `studio_qa_adapter.py` |
| Explicit `workflow_version:null` | Structural FAIL | Accept for triage but preserve null, warn, human review; no QA PASS promotion | **SELECTIVE_FIX** in `studio_qa_adapter.py` |
| Missing workflow_version key | FAIL | FAIL | Preserve fail-closed |
| Unknown severity `Info/WARN/debug` | FAIL | FAIL | Preserve fail-closed |
| Source report mutation | None | None | Preserve raw object unchanged |
| `qa_status=NOT_VERIFIED` | Never promote to verified QA PASS | Same | Preserve no-promotion |
| `qa_status=PASS` with null workflow version | Previously structural FAIL | Structural adapter PASS, document QA downgraded from PASS for review | **SELECTIVE_FIX**, not provider-certified |
| PR #14 raw E1 observation | Not provided | Reported by Studio agent/user, not authenticated raw provider bytes | **NEEDS_STUDIO_EVIDENCE**; no Live claims |

## 3. Red-before / green-after tests

**Red first:** synthetic Studio QA Adapter regressions added to a new branch based on PR #13 HEAD. Pre-patch SHA `8dd0e02568f70f4ca11384c590a87d1fc4fd920c`, GitHub Actions #41310013297: **5 new tests failed** because lower-case known severities and explicit null workflow version caused adapter FAIL. This verifies the compatibility difference in the existing Python code; it does **not** authenticate actual Studio reports.

**Selective patch:** SHA `23a08d119185d4f2cff73c8d32169526b22bc932`, only `src/leadtime_guardian/qa/studio_qa_adapter.py`:
- Recognize only literal `info`, `warning`, `error` in the issue severity field; convert solely in adapter output to `INFO`, `WARNING`, `ERROR`; add `STUDIO_ISSUE_SEVERITY_CASE_NORMALIZED` warning and `requires_human_review=true`.
- When required key `workflow_version` is **present** and `null`, preserve null, add `STUDIO_WORKFLOW_VERSION_NOT_VERIFIED`, request human review; unknown version is not authenticated. If the key is omitted, preserve `STUDIO_REQUIRED_FIELD_MISSING`/structural FAIL.
- Optimistic reported PASS with null version cannot be accepted as verified document PASS. Existing Cross-Agent compares adapter's mapped document verdict to the handed-off verdict and separately checks raw SHA, Case/Doc IDs, provenance.
- No modifications to Python V6 Team2 engine, `input_delivery.py`, `cross_agent.py`, Studio Adapter/Stage Intake, B0/E1 or PDF.
- Original report is not mutated, source bytes never claimed authenticated, `python_run_verified=false`, `pdf_grounding_verified=false`.

**Green code CI:** Run #41310125056, **630 full Python PASS (including 441 QA)**, QA and full Ruff PASS, Archived C001 and Local Integration PASS_LOCAL, `overall_status=BLOCKED`. Existing C001/C013/C017/C008, Stage Intake, Typed JSON, Normalize→QA Input, Cross-Agent, Provenance and B0/E1 local regression remain within the whole test suite. It is not new Studio Live execution.

## 4. Code freeze decision

Draft PR #15 is the **preferred consolidated GitHub code-freeze candidate**, conditional on GitHub Actions SUCCESS at the last HEAD including all documentation and cross-checking immutable Team2 operational module Blob SHAs. PRs #11, #13, #14 are retained; do not auto-merge PR #14 or double-implement strict JSON. PR #14 does not require cherry-picking; its severity/null adapter hunks were selectively reconstructed at the latest PR #13 HEAD.

## 5. Open provider evidence and release gates

Observed C001 B0 Job reported in XLSX: `job_NCik8shwrgM93PDnNNYukT`, Config `cfg_X2xXakDtmDTHh2RoqVysvL` v1. XLSX `sharedStrings[49]` in 22 cells refers to EMPTY_STRING, not literal 49. That XLSX alone does not authenticate a three-document Native report.

Missing: Actual B0 Extract 3 / Merge / Normalize Native, IndependentQA actual INPUT and REPORT, PDF 3 bytes + operational/QA Upload Receipts, Team2 Live Sidecar, Team3 Human-reviewed Gold, and an actual comparable E1 run/config/PDF origin. The PR #14 E1 report shape is user-reported, not verified raw JSON. Therefore:
- `GITHUB_CODE_FREEZE_GATE=PASS_LOCAL_CANDIDATE` after final CI.
- `STUDIO_E1_ADAPTER_CONTRACT=SYNTHETIC_PASS_LOCAL`.
- `ACTUAL_STUDIO_E2E_GATE=BLOCKED`.
- `HUMAN_GOLD_GATE=BLOCKED`.
- `B0_E1_IMPROVEMENT=NOT_MEASURED`.
- `OVERALL_RELEASE_GATE=BLOCKED`.

The source-code frozen candidate can be stable while live release approval remains blocked.
