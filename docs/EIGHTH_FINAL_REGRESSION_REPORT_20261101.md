# LeadTime Guardian — 8차 전체 회귀 검증 및 CI 보고

## Executed code checkpoint
- GitHub code HEAD before documentation: 72408d9afb3c3cbe755c5d181da0b016594e6df7.
- Code CI: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41302028422
- GitHub Actions conclusion: SUCCESS, all jobs/steps SUCCESS.
- QA-only: PYTHONPATH=src python -m pytest -q tests/test_qa_*.py => **392 passed**.
- Full: python -m pytest -q => **581 passed**, includes the 392 QA tests.
- QA Ruff and repository-wide Ruff => **All checks passed**.
- Archived C001 Replay => successful local CI step; actual new C001 NCik not executed.
- Local integration checks => local_checks_passed:true; overall_status:BLOCKED as expected because Live provenance/Gold missing.
- Final docs/checkpoint GitHub SHA will change; final user-visible report MUST reference the workflow run for final HEAD, never only this intermediate code run.

## Systems covered by the existing full suite
| Subsystem / case | Coverage | Scope |
|---|---|---|
| Strict JSON | Existing unit tests + new raw manifest SHA and metadata isolation | CI LOCAL |
| Studio Adapter / Python V6 | Existing V6 + Studio integration tests; unchanged Team2 engine | CI LOCAL |
| Independent QA | 392 QA tests, including existing QA and new 8th tests | CI LOCAL |
| Stage Intake | Existing 7th raw Step handling, 8th unknown/duplicate/sandbox/typed fixes | SYNTHETIC CI |
| Normalize/QA Input | New false vs 0 regression fails closed, Stage pair checked | SYNTHETIC CI |
| Operational Native/Normalize | Stage preflight before V6; wrong SHA/job/semantic content blocked | SYNTHETIC + ARCHIVED CI |
| Cross-Agent / Provenance | Existing handoff+source PDF receipt contract tests retained | CI LOCAL; Live NOT_VERIFIED |
| B0/E1 Normalize comparison | Exact local raw file SHA match, manifest Step identity, null/string and boolean changes checked | SYNTHETIC CI |
| XLSX sharedStrings index 49 | Previous 6th tests preserved, 22 index49 empty refs vs literal 49 | SYNTHETIC CI + previous actual source forensic |
| Extract null draft contract | Prior 5th audit retained, no speculative Studio schema write | STATIC CI |
| C001 normal/changed delivery | Archived replay and original regression tests | ARCHIVED LOCAL |
| C013 PO1/PO999 | Existing safety regression suite retained | LOCAL CI |
| C017 Korean date | Existing regression suite retained | LOCAL CI |
| C008 partial receipt/double allocation | Existing regression suite retained | LOCAL CI |
| Offline E2E / Local Release | Combined Python/QA/Provenance local checker | BLOCKED for Live |

## Reproduced and corrected failures
1. Previous Python dict equality could silently equate JSON false with numeric 0 and return LOCAL_CONTENT_MATCH. Eighth test asserts FAIL and QA_NORMALIZED_CONTENT_MISMATCH.
1b. The separate existing Normalize->IndependentQA input_delivery validator (not just stage_trace) also compared lists with unsafe Python primitive equality. It now rejects false vs 0 and true vs 1, with two additional regression tests; final test counts must be read from the newest HEAD CI.
2. Previously invalid Stage SHA/Job/Normalize content reached Python V6 and failed only after local business calculations; new preflight returns FAIL with python_safety_status NOT_RUN and no python_summary.
3. Previously B0/E1 comparator accepted replacement JSON if manifests otherwise self-asserted PDFs; eighth original Normalize file SHA matching fails closed and a wrong embedded Job ID is blocked.
4. Missing QA Input+Report provenance link, identical Job-Step IDs, unexpected Extract branch/Stage entries and out-of-evidence-folder paths now fail closed in local Stage validation.
5. A harmless reordering of the 3 intact documents does not change the semantic content hash, but altered quantities or removed evidence do.
6. Manifest oversized beyond 1MiB, original raw Stage beyond 32MiB, malformed JSON and symlink escape are rejected by CLI instead of loading uncontrolled content.

## Explicitly unverified
GitHub cannot authenticate Upstage cloud run using only self-reported JSON or a filename. The real 2026-11-01 B0 NCik job original Normalize/QA Step bytes, 3 PDF upload receipts, Team2 live sidecar, Team3 Human-reviewed Gold and E1 actual run remain absent. QA Step COMPLETED never proves QA PASS. Final Release BLOCKED.

## Final code and docs verification
Check GitHub PR #9 latest HEAD and the GitHub Actions run bound to that exact SHA after EIGHTH_FINAL_CHECKPOINT_20261101.json and this Markdown are committed. The final response should report the final HEAD result and tests from that exact run.
