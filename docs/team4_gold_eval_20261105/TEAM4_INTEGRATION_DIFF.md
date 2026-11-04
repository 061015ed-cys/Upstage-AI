# Team 4 Gold evaluation integration diff

Target repository: `061015ed-cys/Upstage-AI`. Starting `main` HEAD: `575745bd8c6a8f00627197de6e6bb8530bcec6bb`.

The task documents name a different repository. Its Draft PR #3, `80fb5814d6053fc592c627ea70ba30e1a2b6f451`, was inspected as a read-only source. This target repository has no PR #3. Its open PR #1 is a separate documentation handoff and was not modified.

## Selected code

| Path | Treatment | Source blob SHA |
|---|---|---|
| `qa/gold_metrics.py` | Copied unchanged from source PR #3 | `84057c4397a1fcc178eee238df1d29055f13d320` |
| `qa/review_bridge.py` | Copied unchanged from source PR #3 | `b9d2fadb913948bcd3fa652ea0d57eaa43e2789b` |
| `tests/qa/test_gold_metrics.py` | Copied source regression tests | Source PR #3 |
| `tests/qa/test_review_bridge.py` | Copied source regression tests | Source PR #3 |

The existing inventory and CI workflow were retained. The source PR's `qa/inventory.py` differs from this target; it was not applied without a reviewed compatibility need. Existing `qa.integration` already connects inventory, XLSX snapshots, candidate diagnostics, V6, and QA while reporting official accuracy as `NOT_MEASURED`.

No reviewed XLSX, human/team approval record, frozen Gold, or new live Studio Native was present in the target repository. Candidate and archived C001 files are not eligible inputs for official accuracy. The imported evaluator was not run on fabricated approved inputs. The report files record the missing inputs and downstream owners.

The task prompt names `scripts/qa_final_file_integrity_check.py` and `scripts/qa_semantic_pdf_audit.py`; neither exists in this target checkout. The existing `qa.inventory` and CI archive/gate commands are used instead. No protected source PDF, DRAFT, or archived Native file changed.
