# Team 2 PR#12 vs QA PR#3 — source-level diff and integration decision

**Frozen refs:**
- Team2 original: `dohun3540-crypto/leadtime-guardian-agent` PR#12 `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`.
- QA copy: PR#3 `f2aeb848eed0d72893073896898fcaa7154b52a1`.
- Staged candidate: QA copy `feat/qa-team2-v6-combined-20261101`, Draft PR#4. The 6 core files below were re-fetched in both repos; **all six contents and Blob SHA equal Team2 PR#12**. No changes were written to the original repo.

## Files and real semantic differences before staging

| File | QA PR#3 before | Team2 PR#12 authoritative implementation | Classification |
| --- | --- | --- | --- |
| `engine.py` | Prior business data flow without V6 `blocked_result` helper and revised direct-quote currency check | Adds `blocked_result`, explicit non-KRW rejection, standardized unsafe numeric `None` outputs; `analyze_portfolio` remains deterministic | BEHAVIORAL_DIFFERENCE / SAFETY_REGRESSION_RISK when older QA copied upstream |
| `studio_adapter.py` | Lower-level receipt ETA mapping; less complete duplicate/warning/quantity safeguards | Adds source document warnings check, nonempty receipt IDs, duplicate/conflicting notice prevention and stronger original-date/quantity invariants | SAFETY_REGRESSION_RISK (resolved by staging Team2) |
| `studio_integration.py` | Older `documents_from_export(raw)`, accepts narrower envelope and less strict input boundary | `documents_from_export(raw, *, expected_job_id=None)` with strict JSON, Node/Agent job/status envelope checks; `validate_documents` checks PO/SKU/receipt, quantity, quote uniqueness and fields; `analyze_studio_documents` returns blocked results safely | API_CONTRACT_MISMATCH / BEHAVIORAL_DIFFERENCE (new optional kwarg retains old direct invocation) |
| `strict_json.py` | ABSENT | Team2 new `loads_strict`, `validate_json_value`; rejects duplicate keys/nonfinite JSON, invalid UTF-8 | INTEGRATION_BLOCKER fixed by adding exact Team2 file |
| `provenance.py` | ABSENT | Team2 `provenance_sidecar` contract `studio-provenance/1`, source metadata supplied but no PDF verification claim | INTEGRATION_BLOCKER fixed by adding exact Team2 file |
| `agents_api.py` | Older Agent transport status and retrieval loop | Team2 rejects changed/missing Job ID during polling, preserves native Step content for inspection | SAFETY_REGRESSION_RISK resolved in staged code |

Other intentionally staged authoritative Team2 PR#12 files:
- `scripts/analyze_studio_export.py` — strict input and provenance sidecar output, preserves raw export; only offline file-ingestion in CI.
- `tests/test_agents_api.py`, `tests/test_studio_integration.py` — current Team2 regression definitions.
- `tests/test_python_safety_v6.py` — Team2 V6 negative/synthetic/C001 archived tests previously absent from QA copy.

The staged files are an **isolated compatibility experiment**. DO NOT backport QA-copy's obsolete core into Team2 PR#12 or merge this candidate into the operating repository. QA PR#3 remains unchanged.

## Exact Git Blob SHA after staging

| Source | Blob SHA (Team2 PR#12 = candidate PR#4) |
| --- | --- |
| engine.py | `bc0ecdc3df55c0ad95dc8195f1631579aa95d866` |
| studio_adapter.py | `cd24c70f06869a8646e3e56c3ec2e0461727feef` |
| studio_integration.py | `e4c3b81187e31822838eea53ea20f1e1bed7c1ea` |
| strict_json.py | `342357bb271f0e96900effb6401b73a19c4a41fc` |
| provenance.py | `65a4d2a2b27bacf5d0acc359322b528f1b6d7814` |
| agents_api.py | `926070e3bc11a1775170496e26b432089e8b22a3` |

## Interfaces validated together

`documents_from_export(raw, expected_job_id)` → `validate_documents(base,documents,schema)` → `apply_studio_extractions` → `analyze_portfolio` → independent `qa.portfolio.audit_portfolio`. Separately, `qa.studio_qa_adapter` → `qa.handoff_builder` → `qa.cross_agent` → `qa.gate`. The new `scripts/qa_combined_e2e_check.py` provides a read-only single entrypoint for both tracks, but does NOT authenticate Studio uploads or identical PDFs.

Combined CI verified at SHA `bdcdac48a39a73ee72f19936818648eae1813c90`: 315 QA tests and 504 whole Python tests passed; Ruff PASS; local gate BLOCKED. Later commits must be retested at their own SHA.

## Remaining interface gaps

- Actual Studio V5 Native and QA copy Native/IndependentQA report require separate original bytes, Agent/Config/Job/Step and per-upload original PDF hashes. No cloud authenticity was proven by code tests.
- Python local result = `PASS_LOCAL` only if business completed and independent numeric audit PASS; this is NOT Python cloud-independent verification.
- Direct untrusted calls to `engine.analyze_portfolio` skip the high-level extraction validator. The safe Studio path uses `analyze_studio_documents`; Team2 owner should audit public entrypoints, not change the engine arbitrarily in QA.
- V5 Extract null-schema mismatch is owned by operating Studio/Team2, not to be silently fixed by this combined copy.
- Human Gold and final release are BLOCKED.
