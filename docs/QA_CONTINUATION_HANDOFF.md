# LeadTime Guardian — QA continuation handoff (2026-10-31 KST)

## Canonical locations

- **Writable copy:** `dohun3540-crypto/leadtime-guardian-agent.copy`
- **Continue branch:** `feat/qa-source-restore-20261031`
- **Draft PR #2:** https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/2
- **Original read-only PR #11:** https://github.com/dohun3540-crypto/leadtime-guardian-agent/pull/11
- **Source snapshot:** `f196c694917f2d9e5f4ec228c752bd3f2a4eb882`
- **Last code SHA with independently observed CI success before doc updates:** `2b926733ac4dba90454ae2f7a6254eef11cfed1b`
- **Full CI:** https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856300
- **Independent QA CI:** https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856310

**Important:** The branch HEAD moves when docs are updated. Always retrieve latest PR head and confirm success of CI at that **exact** SHA. Prior CI is not proof of a new commit.

## Latest measured test results

| Run | Verified |
| --- | --- |
| Python CI (full repository) | **306 passed in 9.64s**, whole-repo Ruff PASS |
| Independent QA CI | **226 passed in 1.35s**, QA Ruff PASS |
| C001 archive | 3/3 original PDF hashes, metadata consistency PASS |
| C001 replay | PASS, no new Studio calls |
| Native C001 contract | PASS against archived expected run IDs |
| Local integration gate | Local PASS, **overall BLOCKED** for external dependencies |
| Original Git tree | 156/156 original file SHA matches QA copy |

## New/modified work in this continuation

- `src/leadtime_guardian/qa/portfolio.py`: independent source preflight of quantity/date/money fields; C001/other native successful document IDs must match actual source document list; wrong success review flags rejected. Previously optional synthetic compact fixtures remain supported without falsely claiming provenance.
- `tests/test_qa_source_integrity.py`: invalid/unused quote amounts, malformed source row arithmetic, document ID tampering, positive boundary/date cases.
- `src/leadtime_guardian/qa/studio_contract.py`: strict native `content + metadata` contract, job/step cross-run check, duplicate nested JSON keys, Gold-wrapper rejection, source file IDs/names and merge document type alignment.
- `tests/test_qa_studio_contract.py`: adversarial Native envelope and run-mixing tests, including the unknown file ID + absent file-name regression, based on the unchanged historical C001 archive.
- `src/leadtime_guardian/qa/gate.py`: read-only local gate that differentiates actual C001 checks from unavailable external/live/human evidence.
- `scripts/qa_gate_check.py`: machine-readable gate and CLI return codes: 0 local pass, 1 local failure, 2 unmet release prerequisites under `--require-release`.
- `tests/test_qa_gate.py`: ensures local QA success can never silently grant merge/release permission.
- `.github/workflows/qa.yml`: executes local integration gate in CI after the regular independent QA tests.

Commit messages are split across feature, test and CI updates in PR #2. The original 156 file paths are unchanged, as are team 2's and team 3's owned materials.

## Not done (do not claim otherwise)

1. Fresh real Studio runs for C013/C017 or C002–C020: **NOT_RUN**.
2. Human source review of draft Gold: **BLOCKED** until team 3 provides it.
3. QA check against team 2's final unpublished Adapter/engine changes: **BLOCKED** until artifacts are available.
4. Actual PDF extraction accuracy/precision, end-to-end latency and live API costs: **NOT_VERIFIED**.
5. Final LMS submission, production release, main merge, email/procurement action: **NOT_RUN**.

## Immediate next steps for the next developer

1. Read the latest remote HEAD/PR #2 and CI conclusions for that same SHA.
2. Re-run full `pytest`, Ruff, `tests/test_qa_*.py`, C001 archive and `qa_gate_check.py` after any integration.
3. On actual new Studio runs, compare returned Job/Step IDs against externally observed execution metadata before accepting a prediction.
4. Receive team 2's revised Adapter interface and team 3's separately verified Gold; test on a *separate integration branch* if original component changes are needed.
5. Update `docs/QA_SCORECARD.md` and `docs/INTEGRATION_GATE.md` with only actually witnessed results, keep Draft PR #2 unmerged until external requirements are met.

## Safety and provenance

A GitHub CLI/Actions success is software contract verification. A recorded `REAL_STUDIO_RUN` from October 30 is historical evidence; an `ARCHIVED_REPLAY` is a local re-execution of stored predictions; neither creates new PDF-extraction accuracy results. Never promote DRAFT Gold automatically or mistake source-file hashes for correctness of extracted text.

## Further cross-agent continuation — 2026-10-31

New code: `qa/cross_agent.py`, `scripts/qa_cross_agent_check.py`, optional `qa_gate_check.py` handoff inputs, `qa/gate.py` guarded integration, tests `test_qa_cross_agent*.py`, QA workflow linting of all `qa_*.py` scripts. New docs: `QA_STUDIO_INTEGRATION_CONTRACT.md` and `QA_CROSS_AGENT_HANDOFF.md`.

The QA Sandbox Agent ID `agt_GhP9GywhbcDWquFqWTsmtq` came from the task handoff. Its latest real Config ID, Node output schema, Native Config Export and C001/C013 QA job files have **not** been read in this GitHub-only session. Do not substitute operational v4 `cfg_SZi6qfyZ6XFoNszpXQK5xQ`. Real cross-agent validation needs actual Studio exports plus matching raw byte hashes and real external approval before production readiness.

Cross-agent code CI checkpoint: 306 whole-repo tests and 226 independent QA tests, Ruff PASS at `2b926733ac4dba90454ae2f7a6254eef11cfed1b`. Re-fetch latest HEAD and rerun CI before claiming a newer commit is verified.
