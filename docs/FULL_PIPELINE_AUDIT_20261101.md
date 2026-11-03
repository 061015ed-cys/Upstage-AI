# LeadTime Guardian — Full pipeline code/contract audit (Team 1, 2026-11-01)

## Evidence and scope

**Actual GitHub refs read:**
- Operational PR #11 `f196c694917f2d9e5f4ec228c752bd3f2a4eb882`, original repository, Draft.
- Team 2 PR #12 `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`, based on #11, Draft.
- Independent QA PR #2 `36af77ee83307a2db8371fcd0ee4fe86c65285e9`, copy repository, Draft.
- Independent QA PR #3, base #2, development changes on `feat/qa-sandbox-copy-validation-20261101`.
- The operational v5 `configs/studio_native/config_v5.user-supplied.export.json` identifies Agent `agt_bXRXFSAgFmBayPjZF7VqRQ`, Config `cfg_o645qH9hDUgVnkrjw7Vets`, v5, but `kind=studio.workflow-config-draft`. A draft is **not authenticated running config**.
- The independent QA copy is user-identified as `agt_HdtUJPQPXir9rGKgPWSyZG`, `cfg_X2xXakDtmDTHh2RoqVysvL`, v1, archived Job `job_9DmRWeQsSShHgWUugkELtk`. Native/QA report bytes for that Job are not in this Git branch.

This report audits all **requested pipeline stages against accessible source**, not every line in every GitHub file or an inaccessible Studio workspace. No paid/remote inference was initiated.

## Verified architectural boundary

```text
Operational (config draft):
PDF → Parse(standard/OCR force) → Classify(file_boundary / four types)
    → Extract_{purchase_order,delivery_notice,quotation,other} → MergeDocuments
    → NormalizeDocuments (Instruct)
Python (source code, not confirmed live Studio wire):
studio_integration.documents_from_export → validate_documents
    → studio_adapter.apply_studio_extractions → engine.analyze_portfolio
    → prepare/evidence_flags → allocate(original/revised ETA) → quote_draft
    → result (external_action_taken=false)
Independent QA (separate Studio workflow; live output not externally fetched):
Parse → Classify → Extract → Merge → NormalizeDocuments → IndependentQA
    → raw IndependentQA report
QA Python (source code):
studio_qa_adapter.normalize_studio_qa_report
    → handoff_builder.build_studio_raw_handoff (new explicit format)
    → cross_agent.audit_cross_agent_handoff
    → gate.build_integration_gate (release remains BLOCKED)
Team2 sidecar studio-provenance/1 → provenance_link.audit_team2_provenance_link
    (local PDF hashes; no cloud/Job authentication)
```

**Match/Validate is a Python boundary, not a proven standalone Studio Node.**
`studio_integration.validate_documents` rejects ambiguous/mismatched receipts, type problems, unknown product/PO and missing evidence; `studio_adapter.apply_studio_extractions` maps revised ETA only when a unique receipt matches. `engine.allocate` computes baseline and revised allocations independently. `engine.quote_draft` applies quote capacity and shipping once per used quote; it documents that it is a draft, not global optimization.

## Stage-by-stage verified code/contract matrix

| Stage | Source / entrypoint | Implemented/test level | Actual Studio proof and release blocker |
| --- | --- | --- | --- |
| Parse | Operational v5 config draft `documentParseConfiguration` | CONFIG_REVIEWED | OCR/coordinates set; uploaded PDF-to-page mapping unverified |
| Classify | v5 draft `documentClassifyConfiguration`, `pipelineEdges` | CONFIG_REVIEWED | file_boundary/four conditional routes visible; per-Job class accuracy unverified |
| Extract | v5 `informationExtractConfiguration.schemas` | CONFIG_REVIEWED / STATIC_CONTRACT_ISSUE | explicit null instructions conflict with strict primitive field types; no new live field accuracy |
| Merge | v5 `pipelineEdges` → `MergeDocuments` | CONFIG_REVIEWED | no verified skip/failure Step exports; file-row mixing unknown |
| NormalizeDocuments | v5 `instructConfiguration`; archived v4 content | VERIFIED_ARCHIVED | v4 C001 documents=3; new QA copy Native/raw unchanged bytes missing |
| Python strict adapter | `strict_json.py`, `studio_integration.py`, `studio_adapter.py` PR #12 | IMPLEMENTED/PR#12_CI | PR #12 is not ported into the QA copy branch; live v5 execution missing |
| Match/Validate | `studio_integration.validate_documents` PR #12 | TESTED_LOCAL via own PR CI | document PO/SKU/receipt checks, no separate Studio Match Node verified |
| Calculations | `engine.prepare/allocate/quote_draft/analyze_portfolio` | TESTED_LOCAL/VERIFIED_ARCHIVED | archived C001 not current operating Studio execution |
| Counterfactual | `allocate(..., baseline=True/False)`, `analyze_portfolio` | IMPLEMENTED/TESTED_LOCAL | current source original/revised ETA used; new live receipt evidence missing |
| Partial Delivery | `allocate` per receipt and `validate_documents` unique matching | IMPLEMENTED/TESTED_LOCAL | C008 new Job unverified; R1/R2 cannot collapse into one |
| Python Safety | `blocked_result`, `evidence_flags`, `analyze_studio_documents` | IMPLEMENTED/TESTED_LOCAL | no purchased items/emails, unsafe inputs block with null numeric results |
| IndependentQA | separate QA Sandbox copy, configuration draft and reported Job | REPORTED_ARCHIVED / NOT_VERIFIED | user-reported C001 QA=NOT_VERIFIED, evidence=PARTIAL, provenance null; raw Step input missing |
| Studio QA adapter | `qa/studio_qa_adapter.py` | TESTED_LOCAL | keeps raw statuses, does not infer Python PASS, needs real original report bytes |
| Cross-Agent manifest | `qa/handoff_builder.py` → `qa/cross_agent.py` | TESTED_LOCAL | raw Native/report SHA + Job/Step/source-file and identity verification; cloud authenticity false |
| Team2 provenance | `qa/provenance_link.py` and `provenance.py` | TESTED_LOCAL | different Job IDs permitted; local PDF byte equality != Studio upload proof |
| Human Gold | `data/cases/SYN-C001..C020/extraction_gold.DRAFT.json` | DRAFT_NOT_HUMAN_VERIFIED | 20 synthetic case dirs found; 19 cases' PDFs held in archive, not individually demonstrated as live |
| CI | QA workflow `.github/workflows/qa.yml`; PR#12 Python CI | CODE_PASS_AT_SHA | QA branch tests PR#11 baseline + QA, not Team2 PR#12 merged tree |
| Offline E2E | `tests/test_qa_full_offline_e2e.py` and `qa/replay.py` | TESTED_LOCAL | v4 operational archived Native + synthetic QA report; deliberately no live claims |
| Actual Studio E2E | New operating Job + new QA Sandbox Job + same verified PDFs | BLOCKED | actual raw pair and independent source PDF provenance absent |
| Release | `qa/gate.py` | BLOCKED | Human Gold, current combined HEAD/CI, actual Studio runs absent |

## Confirmed source-level findings

- **P1 / Static schema mismatch:** Operational v5 Extract fields (especially nullable PO/supplier/date contexts) include explicit null/missing instructions while the associated static JSON Schema declares primitive-only types. The new `qa/pipeline_config_audit.py` detects conflicts and graph/route regressions from source JSON; draft properties must be corrected by Studio owner and verified in a saved Config export before production.
- **P1 / Missing source-file enforcement (fixed in QA):** The previous Cross-Agent checker did not fail explicitly when Native `metadata.source_files` was absent in the legacy report format. The checker now requires a populated list whenever Native is provided.
- **P1 / Path traversal through symlink (fixed QA):** Local source-PDF digest comparison was potentially able to follow a same-name symlink outside the designated original PDF directory. The verifier now rejects a symlink or resolved path outside the root.
- **P2 / Excel false attribution (fixed QA):** Cached `49` in a formula cell is now distinguished as `FORMULA_CACHED_49`. XLSX=49 in 22 reported cells has no proven originating Extract/Normalize stage without raw Step exports.
- **P1 / Provenance link:** QA copy existing C001 metadata `workflow_id/config_id/job_id/source_files=null` are incomplete evidence, not proof of actual identity conflict. `EXECUTION_PROVENANCE_MISMATCH` warning + human review is for observed same-run conflicting non-null IDs only.
- **P1 / Studio IndependentQA input:** `NORMALIZED_OUTPUT_NOT_PROVIDED` is an output report claim; completed NormalizeDocuments alone cannot establish whether 3 documents reached IndependentQA. Needs raw IndependentQA input Step.
- **P1 / Workflow naming:** B0/E1/E2/E3/E4 are experiment labels, not verified Config IDs. No measured comparisons possible without raw files and human review.

## Provenance and status conventions

Code source/version, archived replay, synthetic fixture, current live job, and human-verified PDF Gold are **non-interchangeable**.
`document_qa_status=PASS` with `python_qa_status=NOT_VERIFIED` => Cross-Agent BLOCKED. Local CI success does not authenticate Studio outputs or release.
Issue register and final release conditions: see `docs/FINAL_RELEASE_READINESS_20261101.md`.

## Restricted ownership, no collateral changes

Changes made only to QA source/tests/scripts/docs/QA CI in the copy repository. Operational PRs #11/#12, original Studio/QA Agent, PDF/Gold files, main/branches were not merged, force-pushed or rewritten.
