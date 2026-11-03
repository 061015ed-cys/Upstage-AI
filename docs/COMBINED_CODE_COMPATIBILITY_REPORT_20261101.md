# Combined Code Compatibility — actual same-tree QA/Team2 integration

## What was assembled

A new isolated QA-copy branch `feat/qa-team2-v6-combined-20261101` was created from QA PR#3 `f2aeb848eed0d72893073896898fcaa7154b52a1`. Team2 PR#12's exact six Python source modules, operational offline CLI, and three test files were staged. QA-owned modules, tests, local gate, provenance checking and QA CI are retained. Draft PR #4 has base `feat/qa-sandbox-copy-validation-20261101`; original PR#11/#12 and QA PR#3 were NOT modified.

## Observed compatibility

- **API:** `documents_from_export(raw, expected_job_id=...)` accepts the previously used `documents_from_export(raw)` invocation. Team2 `validate_documents`, Adapter, engine, QA archived replay and independent QA checkers were run together in full CI.
- **Negative contracts:** duplicate JSON keys; unsafe quote currency; duplicate/ambiguous receipt; conflicting PO and revised date; missing source proof; Python blocked numeric outputs; fake Agent Job change.
- **Independence:** `qa.portfolio.audit_portfolio` checks Team2's allocation/cost output independently using the trusted normalized case. QA report status and Python local safety status remain independent; no auto-promotion of Studio PASS.
- **New read-only intake:** `scripts/qa_combined_e2e_check.py` checks exact operational Native bytes, trusted base case ID, expected operational Job ID, strict Studio parsing, deterministic Engine, independent local portfolio validation, optional QA Native+QA Report pair, SHA and Cross-Agent. Returns structured statuses and always keeps release=false, cloud input authentication=false.
- **Cases:** archived C001 (0→60 EA / KRW 60,500); C013 synthetic PO1/PO999 rejection; C017 synthetic ISO dates versus unsupported Korean date string; C008 synthetic receipt R1=40/R2=60, revised shortage 40 / KRW 40,500.
- **Simulation limit:** case DRAFT Gold is explicitly marked not human-reviewed; no new PDF OCR or live Studio Job is executed in these tests.

## Exact measured CI

At code SHA `bdcdac48a39a73ee72f19936818648eae1813c90`: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41291094905
- QA: 315 passed, 0 failed.
- Whole Python: 504 passed, 0 failed (includes QA subset).
- QA Ruff and whole repository Ruff: PASS.
- C001 archived integrity / local offline replay / integration gate checks: executed successfully.
- Integration gate output `local_checks_passed=true`, `overall_status=BLOCKED`.

This is a real single-code-tree CI result, **NOT** an official original-repository merge, actual live Studio test, or approval to release.

## Current blockers

Actual operating V5 Studio Native, actual copied QA Sandbox independent report/Native, saved Configs and original source PDF hashes; Team2 operating Python job evidence; human-reviewed Gold; final production branch and authorized G9 release.
