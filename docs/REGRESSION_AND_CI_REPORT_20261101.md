# LeadTime Guardian — QA regression, CI, E2E and provenance

## Last fully measured code checkpoint (before audit documentation commits)

- QA code SHA: `d9af009c6d41eca9252384883a656d856ed0c951`.
- GitHub Actions: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41287538498
- Conclusion: **completed / SUCCESS** at that SHA, not a claim about any future SHA.
- `PYTHONPATH=src python -m pytest -q tests/test_qa_*.py`: **304 passed**, 0 failed.
- `PYTHONPATH=src python -m pytest -q`: **384 passed**, 0 failed.
- `python -m ruff check src/leadtime_guardian/qa scripts/qa_*.py tests/test_qa_*.py`: PASS.
- `python -m ruff check .`: PASS.
- Archived C001 record integrity, Native envelope and offline replay QA check workflow steps: SUCCESS.
- Local integration gate: `local_checks_passed=true`; **`overall_status=BLOCKED`**, `release_or_merge_authorized=false`.

The 384/304 counts are measured GitHub Actions outputs for this exact SHA. QA suite is included in full Python suite (not additive independent counts). A future doc-only commit must be separately checked before reporting its own latest CI status.

## Relevant new QA source and tests

| Modified or introduced QA area | Regression |
| --- | --- |
| `qa/pipeline_config_audit.py`, `scripts/qa_pipeline_config_check.py` | `test_qa_pipeline_config_audit.py` |
| `qa/cross_agent.py` fail closed missing Native source-files | `test_qa_cross_agent.py` |
| `qa/provenance_link.py` reject PDF symlink escapes | `test_qa_provenance_link.py` |
| `scripts/qa_excel_49_audit.py` distinguish formula-cached value 49 | `test_qa_excel_49_audit.py` |
| Archived Native → Python replay → synthetic QA raw adapter/handoff → gate | `test_qa_full_offline_e2e.py` |

Existing raw Studio QA Adapter, handoff builder and integration gate tests remain included. CI and tests are independent of the actual Studio cloud. The archived operating Job must not be treated as a current QA Sandbox execution.

## Independent operational CI

- Original PR#11 at `f196c694917f2d9e5f4ec228c752bd3f2a4eb882`: Python CI SUCCESS at https://github.com/dohun3540-crypto/leadtime-guardian-agent/actions/runs/41275938671.
- Team2 PR#12 at `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`: Python CI SUCCESS at https://github.com/dohun3540-crypto/leadtime-guardian-agent/actions/runs/41265874061.
- **No single original-repository SHA combining PR#12 and QA PR#3 has yet been tested.** Separate repository successes are not combined E2E proof.

## Independent QA Studio / Human Gold status

- QA copy existing C001: reported `qa_status=NOT_VERIFIED`, `evidence_status=PARTIAL`; original exported QA report and Step input are still unavailable in the code workspace.
- Current operating V5 new Job, current QA copy Job and linked same source PDFs: NOT_VERIFIED.
- Team3 Human Gold: BLOCKED / DRAFT only.
- B0/E1/E2/E3/E4 measured improvements: NOT_VERIFIED (no matched source/run/gold).
- Overall release: **BLOCKED**.

See `docs/STUDIO_PYTHON_QA_E2E_REPORT_20261101.md` and `docs/FULL_PIPELINE_AUDIT_20261101.md` for stage-level details.
