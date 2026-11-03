# LeadTime Guardian — GitHub integration plan (no merge performed)

## Actual branch topology

- Original repository PR #11: `feat/specs-data-engine-20261029`, HEAD `f196c694917f2d9e5f4ec228c752bd3f2a4eb882`, base original `main`.
- Original repository PR #12: `codex/teammate-python-safety-v6`, HEAD `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`, **base PR #11 head**.
- Copy QA repository PR #2: `feat/qa-source-restore-20261031`, HEAD `36af77ee83307a2db8371fcd0ee4fe86c65285e9`, base copy `main`.
- Copy QA repository PR #3: `feat/qa-sandbox-copy-validation-20261101`, based on QA PR #2. The copy repository is separate: no cross-repository automatic merge into the original is assumed.

## Real source conflicts and dependencies

QA copy's core `src/leadtime_guardian/engine.py` blob SHA differs from PR #12's engine blob `bc0ecdc3df55c0ad95dc8195f1631579aa95d866`. The copy's `studio_integration.py` also differs from PR #12's `e4c3b81187e31822838eea53ea20f1e1bed7c1ea`. This is a **known integration divergence**, not proof of a merge conflict: it requires a real three-way diff on the proposed final branch. QA code must not overwrite team 2's engine/Adapter, strict_json or provenance.

QA-owned portable paths:
- `src/leadtime_guardian/qa/**`
- `scripts/qa_*.py`
- `tests/test_qa_*.py`
- `.github/workflows/qa.yml`
- QA-only docs/checkpoints.

Review independently any root `pyproject.toml`, requirements, `README`, main CI workflow and release docs changed on team2 branch. Do not copy QA repository's whole tree into the original.

## Proposed integration sequence (not executed)

1. Pin precise SHA of original PR #11, PR #12, QA PR #3 and their baseline merge-base.
2. Create a fresh protected integration candidate branch in **original repository** from a reviewed team 2 PR #12 tip (requires explicit owner authorization before performing this operation in original repository).
3. Port only QA-owned files from QA PR #3. Preserve original team2-modified engine/Adapter/provenance and gold/PDF files. Resolve import/API differences explicitly.
4. Run `python -m pytest -q`, `python -m ruff check .` and QA targeted tests at the **same final integrated SHA**. Add/execute operational Studio V5 → Python → independent QA local E2E fixtures; run actual Studio only with independently approved costs/permissions.
5. Recheck C001/C013/C017/C008 with case & original PDF digests, human Gold, current saved config/Job/Step and provenance. Mark failed/unknown paths BLOCKED.
6. Review safety, security, upload evidence and presentation. Require human G9 release approval; no automatic merge.

## Request for team2

See `docs/TEAM2_INTERFACE_REQUEST_20261101.md`. Do not silently modify the engine's input contract. The direct `engine.analyze_portfolio` path is a lower-level API; `studio_integration.validate_documents` performs several critical document checks. Verify that all published/external callers actually use the full boundary instead of direct engine calls on untrusted documents.

## CI reality

Independent QA CI validates the QA copy **own tree** (historical PR #11-like core), not PR #12 + QA merged. Team2 PR #12 CI validates the original branch without QA PR #3. Independent PASS + team2 PASS is not combined E2E PASS.

## Third-pass actual isolated combined candidate (2026-11-01)

**Implemented, not merely proposed:** QA copy `feat/qa-team2-v6-combined-20261101` / Draft PR #4, based on unchanged QA PR#3 `f2aeb848eed0d72893073896898fcaa7154b52a1`. All six primary Python source Blob SHA **equal** original Team2 PR#12 `e9b9992b593a42d427ff1bbadeb9a9866ca593bd` after explicit staging. No production or original GitHub repository modification was needed. Exact combined tree CI `bdcdac48`: 315 QA / 504 total Python pytest, two Ruff suites, offline replay and local Integration Gate; GitHub Actions #41291094905 SUCCESS, Release BLOCKED.

The next move is not to merge QA PR #4 into original main. A future authorized release candidate should start from currently approved original PR#12 (or a new owner-updated SHA), then **selectively port QA-only modules/tests/scripts/QA CI/docs**. Run a fresh whole-tree test and official integrated CI; retest raw actual Jobs, source PDF hashes and human Gold. PR#4's historical overlay is for compatibility verification only; if Team2 updates PR#12, the six Blob SHAs must be re-fetched and compatibility rerun. Do not merge PR#4's entire tree back onto Team2 code.
