# LeadTime Guardian — QA copied-sandbox identity & provenance checkpoint (2026-11-01)

## Scope / ownership
QA-only work on an independent branch based on copy PR #2 at `36af77ee83307a2db8371fcd0ee4fe86c65285e9`. No operational Studio, Python engine/Adapter, input PDF, draft Gold, or original PR #11/#12 was modified. No live Studio/API execution occurred here.

## Observed Git baseline (read directly through the GitHub connector)
| PR | At inspection | Status |
|---|---|---|
| original #11 | `f196c694917f2d9e5f4ec228c752bd3f2a4eb882` | open Draft |
| teammate 2 #12 | `e9b9992b593a42d427ff1bbadeb9a9866ca593bd` | open Draft; prior `7897641b` is stale |
| independent QA copy #2 | `36af77ee83307a2db8371fcd0ee4fe86c65285e9` | open Draft |

Past 306 full / 226 QA tests, and teammate 2's 189-test report, are **commit-scoped historical evidence** and are not re-labeled as fresh local runs.

## Identifiers: copy is NOT a live run proof
| Role | Agent | Config | Version |
|---|---|---|---|
| Existing QA sandbox (default) | `agt_GhP9GywhbcDWquFqWTsmtq` | must be separately checked | variable |
| Newly copied QA sandbox (explicit opt-in) | `agt_HdtUJPQPXir9rGKgPWSyZG` | `cfg_X2xXakDtmDTHh2RoqVysvL` | 1 |

The supplied configuration is `kind=studio.workflow-config-draft`; its identifiers are a configured **allow-list pin**, not authenticated Native execution or evidence of an exported run. The existing completed copy Job `job_9DmRWeQsSShHgWUugkELtk` is not eligible to be relabelled as a **new** live Job. The older operational Job `job_gPmEYKzuJdBA6BmKhVnujs` is also in the archived deny-list for that purpose.

## Actual code changes
- `qa/cross_agent.py`: preserve original default Agent ID, introduce narrow copy-Agent/Config/v1 pinning, reject arbitrary expected Agents, quarantine the known completed copy Job as non-new, normalize explicit `EXECUTION_PROVENANCE_MISMATCH` into a warning, set `requires_human_review=true`, block success evidence.
- `scripts/qa_cross_agent_check.py`: explicit `--expected-agent-id` option with the two approved choices.
- `qa/gate.py` and `scripts/qa_gate_check.py`: propagate the identical identity selection to integration gate, which stays non-authorizing.
- `tests/test_qa_cross_agent.py` and `tests/test_qa_cross_agent_cli.py`: default mismatch, approved copy, wrong config/version, arbitrary ID, archived Job spoof, provenance warning, CLI and Release gate fail-closed paths.

### Safe usage
```bash
python scripts/qa_cross_agent_check.py \
  --manifest path/to/reviewed-handoff.json \
  --native path/to/actual-native.json \
  --qa-report path/to/actual-qa-report.json \
  --expected-agent-id agt_HdtUJPQPXir9rGKgPWSyZG \
  --expected-config-id cfg_X2xXakDtmDTHh2RoqVysvL \
  --expected-github-sha ACTUAL_40_CHARACTER_GIT_SHA \
  --require-contract

python scripts/qa_gate_check.py --root . \
  --studio-handoff path/to/reviewed-handoff.json \
  --studio-native path/to/actual-native.json \
  --studio-qa-report path/to/actual-qa-report.json \
  --expected-agent-id agt_HdtUJPQPXir9rGKgPWSyZG \
  --expected-config-id cfg_X2xXakDtmDTHh2RoqVysvL \
  --expected-github-sha ACTUAL_40_CHARACTER_GIT_SHA \
  --require-release
```

Python QA `NOT_VERIFIED` plus document `PASS` => Cross-Agent `BLOCKED`, Release `BLOCKED`. The cross-agent `PASS` is a **local contract-only** result; `release_or_merge_authorized` is always false.

## Existing contract gaps / dependencies
- Team 2 PR #12 now uses separate `studio-provenance/1` sidecar containing supplied `agents_job_id_supplied` and `studio_metadata_supplied`; this is **not** an automatically mapped `leadtime-cross-agent/v1` manifest. Explicit mapping and source-PDF digest validation are still needed.
- The copy workflow draft does not establish actual `IndependentQA` run output schema or Native/QA report bytes.
- C001 historical operational V4 is a reference only. C013 PO mismatch must fail closed. C017 Korean dates require explicit source evidence, and C008 receipt-level allocation requires an unambiguous mapping. They are not new live QA successes here.
- Human-reviewed Gold and PDF-to-actual-job linkage have not been independently verified. The unusual Excel value `49` is an observation to investigate against original Native bytes, not a confirmed model defect.

## What Studio must return before integration can advance
For C001 first, then C013: original unedited `NATIVE_FINAL` file and `IndependentQA` report JSON as **separate files**; saved Config export and `kind`; Agent/Config/version; Job/Step IDs; stage exports for Parse/Classify/Extract/Merge/NormalizeDocuments/IndependentQA; execution type and actual run time; uploaded PDF name, `file_id`, SHA-256 and hash provenance; case_id; node field contract; byte SHA-256 for every raw JSON; any `EXECUTION_PROVENANCE_MISMATCH` with warning/review state. The original existing `job_9Dm...` can be examined as archival evidence without claiming NEW_LIVE_STUDIO.

Cross-Agent contract status: **BLOCKED / pending raw artifacts**.
Release gate status: **BLOCKED** until fresh Team 2 + QA Studio evidence, Python analysis, human Gold, and final integration CI/E2E are provided.
