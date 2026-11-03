# LeadTime Guardian — 11차 교차 검토·최종 회귀 검증

Date: 2026-11-01 KST. Only the isolated QA copy Draft PR #13 is modified.

## Repositories and CI provenance

- Frozen QA PR #11: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/11, SHA `585142e718b444cbbd3e43d3c2b5e42d68637450`. CI #41307188645: 600 full Python PASS, 411 independent QA PASS, Ruff both PASS.
- Parallel old-base QA PR #12: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/12, SHA `a1ceaf412a9c199f37b1ac0d41fb93d7e66e3d1d`. CI #41307353386: 538 full / 349 QA PASS, Ruff both PASS; due to a **different base**, no direct conclusion about regressions can be drawn from test count differences.
- New selective branch `feat/qa-cross-review-pr12-integration-20261101`, Draft PR #13 https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/13, based on PR #11 frozen HEAD (not PR #12 old base).
- **Pre-fix proof:** SHA `f93c71316856603694da448653efad894db7537b`, CI #41308355997 FAILURE only from newly added synthetic regression tests. Four failed cases revealed false LOCAL_CONTENT_MATCH for tuple/list and numeric object-key edge cases.
- **Code fixed SHA:** `2b1c17c10701b3ed06db13708d42e2d0e375683d`, CI #41308460878 SUCCESS.
- **Code fixed CI result:** Independent QA **428 passed**, full Python **617 passed**, QA Ruff **All checks passed**, full Ruff **All checks passed**, archived C001 replay CI success, local_checks_passed true, overall_status **BLOCKED**.
- Independent 428 are included in all-Python 617. 17 new tests were added; no pre-existing tests removed to inflate or alter comparisons.

## Reproduced defect and scope

The modern `_typed_json_equal` used sorted `json.dumps` to distinguish `0` vs `false` and `100` vs `100.0`, which was correct for JSON primitives. However Python `json.dumps` automatically serializes **tuple** as JSON array and **non-string mapping key** as JSON string, e.g. `(1,2)` vs `[1,2]` and `{1:"x"}` vs `{"1":"x"}`. This could label non-JSON Python objects as valid local Studio transfer equality, a fidelity defect.

A **minimal prevalidation** helper `_is_strict_json_tree` now rejects non-JSON tuples/sets/custom objects/keys and non-finite floats before canonical serialization. JSON object keys must be built-in strings; JSON arrays built-in lists. Local QA mismatch remains FAIL; actual cloud input still NOT_AUTHENTICATED; release_or_merge_authorized false.

PR #12's entire `input_delivery.py` was *not* copied or merged. Keeping latest protected functions:
- `_read_documents` for Strict JSON content/output/input wrappers.
- `expected_case_id` keyword argument, explicit QA Report/Normalize/QA Input Case ID binding.
- Document ID present/nonblank and duplicate checks.
- JSON encoding layer/path/document count metadata and status contracts.
- `QA_EXECUTION_PROVENANCE_INCOMPLETE` and other conservative report issue handling.
- All older QA and Python V6 contracts and prior C001/C013/C017/C008 regression paths.

## Case tests and boundary matrix

| Test area | Evidence | Scope |
|---|---|---|
| Non-JSON tuple/list equality | New synthetic red-before/green-after | PASS_LOCAL after patch |
| Object numeric vs string keys | New synthetic red-before/green-after | PASS_LOCAL after patch |
| 0/false, 1/true, 100/100.0, null/empty | New and existing typed field tests | PASS_LOCAL |
| NaN, Infinity | Existing strict JSON and new synthetic cases | PASS_LOCAL |
| Object key order and array order | New positive/negative tests, existing QA regressions | PASS_LOCAL |
| Case C001 explicit C001/C013 mismatch | New synthetic and older strict-case tests | PASS_LOCAL |
| Nested Wrapper/double encoded JSON/duplicate IDs | Existing QA regression suite retained | PASS_LOCAL |
| Stage Intake/Release Evidence Inventory | Existing full pytest + Ruff | PASS_LOCAL |
| Python Safety V6/operational adapter | Existing unchanged Team2 core modules + 617 full regression | PASS_LOCAL |
| Cross-Agent, PDF source file_id SHA, Provenance | Existing offline CI and local integration | PASS_LOCAL |
| B0/E1 comparison original Native SHA and Gold gate | Existing full regression; no Live E1 | PASS_LOCAL / Live BLOCKED |
| Archived C001 replay | CI success, original archived/historical | PASS_LOCAL |
| C013 PO1/PO999, C017 Korean date, C008 partial allocation | Existing full suite retained | PASS_LOCAL |
| Actual C001 NCik Native/QA provider flow | Not supplied | NOT_VERIFIED |
| Human-reviewed Gold, actual E1 | Not supplied | BLOCKED / NOT_MEASURED |
| Overall release | Required external evidence missing | BLOCKED |

**Final docs HEAD verification:** This report is written after the first green code CI. The GitHub PR #13 latest SHA will move as reports are committed. Query the exact final HEAD and its own GitHub Actions run to substantiate terminal verification; do not cite the earlier code SHA as final documentation SHA.

## Original-source protection

Original QA PR#11, parallel QA PR#12, operational Team2 `leadtime-guardian-agent#12`, and main remained unmerged/unmodified. No original XLSX/PDF/Native/Gold upload or mutation, no new paid Studio Job, no cherry-pick/force push. Verify exact six Team2 core module Blob SHA against the operational PR #12 final HEAD.
