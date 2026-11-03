# LeadTime Guardian — Independent QA Integration Gate

**Last measured code snapshot:** `2b926733ac4dba90454ae2f7a6254eef11cfed1b` (2026-10-31 KST)  
**Work branch:** `feat/qa-source-restore-20261031` (Draft PR #2)  
**Source checkpoint:** original PR #11 `f196c694917f2d9e5f4ec228c752bd3f2a4eb882`.

## 1. Ownership and non-negotiable protections

Team 2 owns the calculation engine and Studio Adapter. Team 3 owns source PDFs, dataset and Gold review. This QA contribution owns `src/leadtime_guardian/qa/`, `tests/test_qa_*.py`, QA scripts, CI QA workflow and QA documents only.

No original source changes, force pushes, main merges, Studio configuration writes, external procurement, emails or draft-to-approved Gold promotion.

## 2. Verified state vs prerequisites

| Gate | Status | Evidence or dependency |
| --- | --- | --- |
| Original Git source file restoration | **PASS** | 156/156 original Git SHA matches |
| Full Python regression | **PASS** | 306 passed, Ruff PASS, [Actions #41181856300](https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856300) |
| Independent QA regression | **PASS** | 226 passed, QA Ruff PASS, [Actions #41181856310](https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41181856310) |
| Archived C001 PDF hash / internal metadata | **PASS** | 3/3 source-PDF file hash checks |
| Archived C001 replay / Adapter output contract | **PASS** | `tests/test_qa_replay.py`; replay does not mean new Studio inference |
| Archived C001 Native envelope consistency | **PASS** | Job, Step, document/source metadata expected IDs checked |
| Local gate executable | **PASS** | `python scripts/qa_gate_check.py --root .` |
| Overall integration/release gate | **BLOCKED** | Live/human/team handoff requirements missing |
| Team 2 latest Adapter integration | **BLOCKED** | Await collaborator branch/artifact |
| Team 3 source-reviewed Gold | **BLOCKED** | Await independent human ground truth |
| New Studio run for C013/C017 | **NOT_RUN** | No authenticated Studio execution in this QA task |
| Production PDF extraction accuracy | **NOT_VERIFIED** | No approved independent Gold sample set |
| External purchase/send or final delivery | **NOT_RUN** | Explicitly outside automated QA scope |

**PASS is scoped to the check actually executed.** The local gate deliberately cannot infer GitHub CI status, real Studio availability or human validation from archived results.

## 3. Repeatable checks

Use the repository declared Python environment and `requirements-agents.txt`.

```bash
python -m pip install -r requirements-agents.txt
python -m pytest -q
python -m ruff check .
PYTHONPATH=src python -m pytest -q tests/test_qa_*.py
python scripts/qa_archive_check.py --root .
python scripts/qa_gate_check.py --root .
```

The last command returns 0 when **local** checks pass while reporting `overall_status=BLOCKED`. To demand actual merge readiness (not merely local check success):

```bash
python scripts/qa_gate_check.py --root . --require-release
```

Expected exit is **2** until required external evidence is verified. Local failed checks return **1**, even without `--require-release`.

The C001 `trusted_base_case.json` is **pre-Studio**; do not pair it directly with completed Studio analysis. The replay module reconstructs integrated data from archived native predictions.

## 4. Merge gate decision

Do not merge based only on the 306 test passes.

1. Verify PR HEAD and every Actions conclusion refer to the same SHA.
2. Compare team 2's final Adapter interface and team 3's PDF/Gold evidence without overwriting their branches.
3. Re-run full tests plus independent QA on the new combined tree, including C013/C017 contract and adversarial boundary cases.
4. Execute new Studio jobs only with valid permission; save real Agent, Config, Job IDs, input hashes and raw responses.
5. Keep DRAFT Gold distinct from raw predictions and human-verified Gold. Only calculate extraction metrics with independently reviewed labels.
6. Require separate authorized review before changing Draft PR status or merging main.

Historical `scripts/qa_restore_source.sh` is not to be rerun on this already restored branch. The original 156 files remain byte-for-byte unchanged.

## Optional Studio QA Sandbox handoff gate

The latest QA Sandbox remains unobserved, so no real Studio QA artifact is claimed. Provide reviewed `leadtime-cross-agent/v1` manifest and unmodified Native/QA report bytes to `qa_cross_agent_check.py`, then the optional `--studio-handoff`, `--studio-native`, `--studio-qa-report` inputs to `qa_gate_check.py`. An invalid supplied handoff produces local FAIL. A valid but unverified handoff preserves overall BLOCKED. A single Studio document PASS never implies Python PASS or main merge authorization. See `docs/QA_STUDIO_INTEGRATION_CONTRACT.md` and `docs/QA_CROSS_AGENT_HANDOFF.md`.
