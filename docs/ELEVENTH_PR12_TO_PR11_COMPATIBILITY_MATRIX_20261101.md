# LeadTime Guardian — 11차 PR12_TO_PR11_COMPATIBILITY_MATRIX

2026-11-01 KST. **두 PR 모두 QA 사본 `leadtime-guardian-agent.copy`의 번호**이다. 운영 엔진 저장소 `leadtime-guardian-agent#12`와 혼동하지 않는다.

## Verified refs

| Item | QA freeze #11 | Parallel QA #12 |
|---|---|---|
| URL | https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/11 | https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/12 |
| HEAD | `585142e718b444cbbd3e43d3c2b5e42d68637450` | `a1ceaf412a9c199f37b1ac0d41fb93d7e66e3d1d` |
| Base | `feat/qa-ninth-release-readiness-20261101` | `feat/qa-team2-v6-combined-20261101` |
| Independent pytest | 411 PASS | 349 PASS |
| Entire pytest | 600 PASS | 538 PASS |
| CI | https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41307188645 SUCCESS | https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41307353386 SUCCESS |
| Source of difference | Latest full safe Wrapper/Case/Stage/QA contract | One new commit on old base, only 2 paths changed |

Git compare PR #11 HEAD → QA PR #12 HEAD: **diverged; ahead_by=1, behind_by=134**. This is a code ancestry comparison, not a test regression count. Do not cherry-pick, merge, or replace PR #11 implementation with older one.

## PR12_TO_PR11_COMPATIBILITY_MATRIX

| ID | PR #11 existing behavior | PR #12 behavior | Difference and regression risk | Classification | Action / proof |
|---|---|---|---|---|---|
| T01 | `_typed_json_equal` json.dumps sorted, allow_nan=False | recursively checks exact Python `type` | Both distinguish `0` vs `false`, `1` vs `true` | ALREADY_IMPLEMENTED | Keep existing, positive regression |
| T02 | `100` serializes as 100 vs `100.0` as 100.0 | int and float type not equal | Both reject integer vs decimal representation change at QA input fidelity boundary; engine may separately normalize per schema | ALREADY_IMPLEMENTED | Existing typed comparison retained; new regression |
| T03 | Null, empty string, literal `"null"` distinct in canonical JSON | Explicit exact type identity | No meaningful missing safety | ALREADY_IMPLEMENTED | Keep existing code |
| T04 | `sort_keys=True` ignores dict key insertion order | Key membership check ignores insertion order | Same valid JSON outcome | ALREADY_IMPLEMENTED | Regression: reordered object remains LOCAL_CONTENT_MATCH, CLOUD BLOCKED |
| T05 | JSON array order preserved by dumps | list items compared in order | Same valid JSON outcome | ALREADY_IMPLEMENTED | Regression: reordered array mismatch |
| T06 | `allow_nan=False` rejects float NaN/Infinity when JSON serialized | math.isfinite checks float | Same invalid JSON outcome | ALREADY_IMPLEMENTED | Retain strict JSON; synthetic regression |
| T07 | `json.dumps((1,2))` becomes `[1,2]`, allowing tuple-vs-list to match | exact `type(x) is list`, reject tuple | **Confirmed false LOCAL_CONTENT_MATCH** for Python-only input | CONFIRMED_DEFECT | Pre-fix CI #41308355997 2 failures in test cases; patch prevalidates JSON tree |
| T08 | `json.dumps({1:"x"})` and `json.dumps({"1":"x"})` both become `{"1":"x"}`; invalid int keys may match | requires all keys to be str | **Confirmed false LOCAL_CONTENT_MATCH** for invalid JSON key | CONFIRMED_DEFECT | Pre-fix CI #41308355997 2 failures; patch checks type(key) is str recursively |
| T09 | `loads_strict` on documented `content/input/output` wrappers, detects double JSON encoding | only `output.documents` and direct `normalized_documents` | Overwriting with older PR would **lose wrapper support** | CONFIRMED_REGRESSION_RISK | Do NOT cherry-pick/replace |
| T10 | `expected_case_id` keyword-only, checks Normalize, QA Input, QA Report explicit case conflict | function lacks this parameter | **Breaking CLI/integration call** and safety regression | CONFIRMED_REGRESSION_RISK | Preserve latest function signature |
| T11 | Rejects duplicate/missing/blank document_id and malformed equal lists | directly flags equal JSON arrays as LOCAL_CONTENT_MATCH | Could accept malformed/duplicate documents locally | CONFIRMED_REGRESSION_RISK | Preserve latest document validation |
| T12 | Tracks `normalize_payload_path`, `qa_input_payload_path`, document counts, encoding layers | result fields limited to status, issues, bools | Existing consumers/report contract would break | CONFIRMED_REGRESSION_RISK | Preserve return keys unchanged |
| T13 | QA Report provenance non-null check, report error and explicit `case_id` conflict | provenance non-null check and report error, no explicit case binding | Base audit overlaps; latest has stronger case binding | ALREADY_IMPLEMENTED / CONFIRMED_REGRESSION_RISK | Preserve latest |
| T14 | No inference of Live cloud input delivery from local documents | Same false provenance claims | Both conservative | ALREADY_IMPLEMENTED | Keep `actual_cloud_input_authenticated=false` and `release_or_merge_authorized=false` |
| T15 | Strict JSON rejection for duplicate raw keys, malformed strings and wrappers | Old direct-Python fields only | Existing raw input path would be lost | CONFIRMED_REGRESSION_RISK | Retain `_read_documents` and `loads_strict` |
| T16 | Native/Normalize/Stage/Case/PDF Receipt local contracts tested | PR #12 tests simple bare value lists lacking IDs | PR12 tests do not transfer as-is to latest contract | USEFUL_MISSING_TEST | Rewrote **strict valid-document synthetic tests** in `tests/test_qa_cross_review_pr12_types.py` |

## Confirmed red CI before fix

Added tests first on isolated branch from PR #11 HEAD. GitHub Actions #41308355997 produced four genuine failures because existing `_typed_json_equal` treated:
- tuple `(1,2)` vs list `[1,2]` as LOCAL_CONTENT_MATCH.
- identical tuples on both sides as LOCAL_CONTENT_MATCH despite not being valid JSON.
- dict with numeric key 1 vs string key `"1"` as LOCAL_CONTENT_MATCH.
- identical integer-key dicts as LOCAL_CONTENT_MATCH.
- A mixed-key synthetic dictionary was also included; the native `sort_keys=True` comparator may reject it already without a false match.

All cases preserve a structurally valid document ID, type and explicit C001 case; these are not artifacts from an invalid whole-document fixture. This is a fidelity defect **only if Python objects with these non-JSON types reach the checker**. Actual Upstage source format remains NOT_VERIFIED.

## Narrowest resolution

Created isolated branch `feat/qa-cross-review-pr12-integration-20261101` from unchanged PR #11 HEAD, draft PR #13 https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/13. Kept original helper `_typed_json_equal` and strict canonical serialization, but added `_is_strict_json_tree` prevalidation:
- valid JSON object keys must be built-in strings,
- JSON arrays must be actual list, not Python tuple,
- numeric float must be finite,
- scalar values are exact built-in str/int/bool/None,
- no coercion, evidence writes or provider authentication,
- old Wrapper, expected_case_id, document validation, report output contract and CLI preserved.

**The older parallel PR #12 must not be merged wholesale.** 11차 change is limited to original strict comparator missing precondition and targeted regression tests; frozen PR #11 remains unchanged. Reuse current archived CI and run final full QA, Python/Ruff and local integration checks for latest PR #13 SHA.

## Studio interface / provenance limits

B0 C001 reported Job `job_NCik8shwrgM93PDnNNYukT`, Config `cfg_X2xXakDtmDTHh2RoqVysvL` v1. Only original XLSX reports one Job and Extract three branches. New B0 real Extract/Merge/Normalize/IndependentQA actual INPUT/REPORT, operational Native/PDF Upload receipts and Team2 Live Sidecar, Human-reviewed Gold not provided. Offline type fidelity checks do not establish actual Studio input delivery. Overall Release BLOCKED.
