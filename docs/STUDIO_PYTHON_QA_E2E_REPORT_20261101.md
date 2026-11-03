# Studio → Python → IndependentQA → Cross-Agent: E2E evidence report

**Measured code commit:** see `docs/REGRESSION_AND_CI_REPORT_20261101.md` once final CI completes. No new remote Studio calls were performed here.

## E2E coverage ladder

| Level | Evidence | Status | What it proves |
| --- | --- | --- | --- |
| I1 local units | QA `tests/test_qa_*.py`, Python engine unit tests | PASS at cited CI SHA | Local code functions/contracts |
| I2 offline E2E | archived operational V4 Native + Python replay + explicitly synthetic IndependentQA JSON + new raw adapter + Cross-Agent + integration Gate | PASS_LOCAL_CODE_WITH_RELEASE_BLOCKED | Cross-module mechanics and conservative blocking; no live claims |
| I3 actual Studio E2E | QA copied C001 Job original Native/IndependentQA + fresh operating Job + PDFs/steps | NOT_VERIFIED/BLOCKED | Unavailable original bytes and execution source binding |
| I4 release | live source-authenticated C001/C013/C017/C008 + Python + Human Gold + E2E CI | BLOCKED | No external authorization |

### I2 actual test behavior

`tests/test_qa_full_offline_e2e.py` invokes:
1. `qa.replay.verify_c001_replay(repo_root)` on archived operational C001 v4.
2. `qa.handoff_builder.build_studio_raw_handoff(..., execution_kind=ARCHIVED_REPLAY)` on archived Native with a synthetic QA report openly created by the test.
3. `qa.cross_agent.audit_cross_agent_handoff`, whose status stays `BLOCKED` because Python QA is `NOT_VERIFIED` and report provenance is incomplete.
4. `qa.gate.build_integration_gate`, which reports `local_checks_passed=true` while `overall_status=BLOCKED` and `release_or_merge_authorized=false`.

The synthetic QA document is NOT a Studio IndependentQA execution. The archived operational Job ID does not identify the QA Sandbox copy. PR #12 changed engine/Adapter files independently and is not merged into this QA copy; I2 is NOT a combined PR#12+QA integration test.

## Case comparison (source manifests inspected at QA PR)

| Case | Source evidence | Code/local expectation | Actual QA copy+Python live |
| --- | --- | --- | --- |
| C001 | `SYN-C001/manifest.json`, three synthetic PDFs in GitHub; archived V4 run | baseline shortage 0, revised 60, substitute 60, KRW 60,500 | QA copy report user-observed NOT_VERIFIED/PARTIAL; raw QA report unverified |
| C013 | DRAFT synthetic document JSON with PO1 purchase and PO999 notice | `validate_documents` must reject unmatched PO; no fabricated numbers | NOT_RUN/NOT_VERIFIED |
| C017 | DRAFT synthetic extraction JSON; generator-origin and no human Gold | Korean source date normalization only with unambiguous original context; strict Python ISO date otherwise blocks | NOT_RUN/NOT_VERIFIED |
| C008 | DRAFT synthetic rows: R1=40 EA, R2=60 EA; notice changes R2 only | receipt-level uniqueness, no double allocation | NOT_RUN/NOT_VERIFIED |
| C002-C020 | QA repo contains 20 case directories; DRAFT or synthetic gold | local fixture coverage subject to source checks | NOT_VERIFIED, not new Studio runs |

Note: `SYN-C017/extraction_gold.DRAFT.json` already contains normalized ISO dates, so it cannot itself prove accurate recognition of raw Korean date strings in actual PDF.

## B0 / E1 / E2 / E3 / E4 comparison

These labels denote **proposed experiment variants, not Config IDs**.
- B0: baseline config ID / original Job/Step / exact PDF inputs / Gold metrics NOT_VERIFIED.
- E1: Extract null schema experiment version and actual new run NOT_VERIFIED.
- E2: Match/Validate (could be Python-level) experimental ID and actual run NOT_VERIFIED.
- E3: IndependentQA input-path repair, actual input Step and report NOT_VERIFIED.
- E4: integrated candidate, same-case source PDFs and actual operating/QA Jobs NOT_VERIFIED.

No defensible classification accuracy, field accuracy, false-positive rate or improvement delta can be computed yet. Metrics require numerator/denominator, exact ground-truth version, source/job/Config/Git SHA.

## Required to promote I3

Per case and per operating/QA workflow: original unedited Native and IndependentQA JSON bytes, raw Step-level input/output, Agent/Config/version/Job/Step, timestamps, actual uploaded PDF names/file IDs and PDF SHA with hash origin. For operating side also provide actual Python run output, business validation status, `studio-provenance/1` sidecar, Git SHA and independent Python QA evidence. For Human Gold provide reviewer, PDF page/field coordinates, version/SHA and reviewed/excluded fields.

**Status:** LOCAL_CODE_PASS / CROSS_AGENT_LIVE_BLOCKED / RELEASE_BLOCKED.
