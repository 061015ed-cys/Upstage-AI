# Team 4 CI matrix

Target: `061015ed-cys/Upstage-AI`; base `575745bd8c6a8f00627197de6e6bb8530bcec6bb`.

| Check | Current local result | Scope |
|---|---|---|
| Source PR #3 | Draft; HEAD `80fb5814d6053fc592c627ea70ba30e1a2b6f451` | Read-only external baseline, not this repository's CI |
| Imported evaluator and bridge tests | 27 passed | Local synthetic regression fixtures only |
| `python -m pytest tests/qa -q` | 83 passed, 1 skipped | Local QA suite; Windows symlink permission skip |
| `PYTHONUTF8=1 python -m pytest -q` | 761 passed, 5 skipped | Local full suite on Python 3.12.10 / Windows |
| `python -m ruff check .` | PASS | Local source lint |
| `python -m qa.inventory --root . --out <fresh folder>` | 60 PASS, 0 FAIL, 0 BLOCKED | PDF byte/page machine inspection only |
| `scripts/qa_archive_check.py` and `scripts/qa_gate_check.py` | Both exit 0 | Archived replay/code gates; no new live Studio claim |
| New branch GitHub Actions | PENDING | Must match final PR HEAD; prior PR #1 success is not reusable |
| Reviewed XLSX intake | BLOCKED | Original XLSX and human record absent |
| Official Gold metrics | NOT_MEASURED | Approved frozen Gold and bound Native absent |
| Release | BLOCKED | External evidence gates absent |

The first local full suite run under Windows' default `cp949` locale produced 1 `UnicodeDecodeError`, 733 passed, 5 skipped. The repository workflow sets `PYTHONUTF8=1`; the rerun with that setting passed 761 tests, with 5 Windows skips. The final result and exact commit CI should be read from the branch's current GitHub Actions run.
