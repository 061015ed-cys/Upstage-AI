# LeadTime Guardian — Independent QA Scorecard

**Verified:** 2026-10-31 KST  
**Working copy:** `dohun3540-crypto/leadtime-guardian-agent.copy`  
**Branch:** `feat/qa-source-restore-20261031`  
**Draft PR:** https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/2

## Observed checks — code checkpoint `2b926733ac4dba90454ae2f7a6254eef11cfed1b`

| Validation | Result | Verified action |
| --- | --- | --- |
| Full repo Python tests | **306 passed in 9.64s** | https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856300 |
| Independent QA tests | **226 passed in 1.35s** | https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856310 |
| Whole-repo Ruff / QA Ruff | **PASS / PASS** | Same completed CI runs |
| Original PR #11 file integrity | **156/156 source Git blob SHA identical** | Compared original checkpoint `f196c694917f2d9e5f4ec228c752bd3f2a4eb882` to QA copy HEAD |
| Archived C001 PDF hash check | **PASS: 3/3 source PDFs** | Independent QA archive check |
| C001 archived Adapter replay | **PASS** | QA replay tests |
| C001 Native envelope contract | **PASS for archived JSON and expected IDs** | New independent Native contract tests |
| Conservative local integration gate | **LOCAL PASS / OVERALL BLOCKED** | QA Actions `qa_gate_check.py` step |
| New real Upstage Studio runs (C013 / C017) | **NOT_RUN** | No new cloud execution in this QA session |
| Manually verified Gold | **NOT_VERIFIED** | Requires team 3 source-PDF review |
| Real extraction accuracy / latency / API cost | **N/A** | No new live measured sample set |

**Interpretation:** The 306 tests are 80 restored project tests plus 226 independent QA tests, **not** 306 separate Studio jobs and **not** an extraction accuracy figure. These measurements are for the specified code SHA; the final documentation commits may have newer SHAs and must be checked separately.

## This QA continuation's improvements

- Source preflight now rejects invalid/negative/unhashable quantities, malformed dates, non-finite or malformed prices even for supplier quotes that are not selected in the final solution. This prevents a false PASS and avoids arithmetic type exceptions.
- Successful analyses with actual `documents` must preserve the exact `evidence_document_ids` list. Duplicated/missing document IDs, missing documents and review flags in a success result are flagged. Compact standalone synthetic QA examples without a `documents` field remain supported for backward compatibility; this does not establish Studio provenance.
- New `studio_contract.py` independently checks archived **native** `content + metadata` envelopes: strict nested JSON, execution Job/Step IDs, occurrence ID, document types/IDs, source manifests, merge document types, file references, ambiguous content and Gold-wrapper contamination.
- Malformed or unbound native data is FAIL/NOT_VERIFIED. A structural PASS verifies internal consistency against expected IDs, **not** authenticity, PDF grounding or a new live run.
- New `gate.py` and `qa_gate_check.py` aggregate actual C001 local checks while explicitly keeping external CI, C013/C017 Studio, human Gold and team 2/3 integration dependent gates unresolved. No automatic main merge or release approval.
- New adversarial QA tests include integer/Decimal and invalid sources, document-ID tampering, cross-job and cross-step mixing, duplicate JSON keys, stale source mappings and fail-closed gate behavior.
- CI now executes the local conservative gate in addition to archive checks.

## Provenance and pending integration

- Existing 2026-10-30 C001 Web Studio record: historical **REAL_STUDIO_RUN** evidence only. QA replays and envelope audits **did not initiate** a fresh Studio run.
- Team 2 calculation engine / Studio Adapter and team 3 source PDFs / draft Gold remained unmodified in this QA work.
- Additional actual C013/C017 cloud executions: **NOT_RUN**.
- Latest team 2 Adapter result vs current QA contract: **BLOCKED** until handoff.
- Team 3 PDF-grounded human Gold: **BLOCKED** until reviewed.
- Deployment, actual procurement, email sending and main merge are **not authorized or performed**.

Follow `docs/INTEGRATION_GATE.md` and `docs/QA_CONTINUATION_HANDOFF.md`. Keep Draft PR #2 open for review.

## Cross-agent Studio / Python verification (2026-10-31)

- New `qa/cross_agent.py` versioned handoff manifest validator verifies distinct document/Python status domains; strict expected Sandbox Agent ID; optional expected actual Config ID / GitHub SHA; historical C001 Job replay protection; unmodified Native and QA report SHA-256; actual Job/Step/file-ID cross-checks.
- New `tests/test_qa_cross_agent.py` and `tests/test_qa_cross_agent_cli.py` cover synthetic handoffs, stale Config, mixed Job, false PASS/FAIL, malformed reports and reordered file manifests. Their synthetic manifests **are not authentic Studio Sandbox exports**.
- New QA scripts and optional gate arguments let reviewers test a future authentic Studio Sandbox artifact without changing Studio or team 2's Adapter.
- Real latest Studio QA Sandbox Config ID, QA Node output schema, actual C001/C013 new Job IDs and Native Config Export: **NOT_VERIFIED**, no authenticated Studio access. A current Studio release decision is **BLOCKED**.
- GitHub cross-agent code CI: [306 full tests](https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856300), [226 QA tests](https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856310), Ruff PASS. Tests were run at SHA `2b926733ac4dba90454ae2f7a6254eef11cfed1b` before documentation-only updates.
