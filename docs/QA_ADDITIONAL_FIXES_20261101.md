# QA Additional Integration Fixes — third development pass

Actual isolated QA-copy Draft PR#4 based on QA PR#3. Source of truth Team2 PR#12 HEAD `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`.

**P1 resolved in isolated integration candidate:**
1. QA copy core missing `strict_json.py`, `provenance.py`: exact Team2 files staged (same Git blobs), no handwritten substitute.
2. Outdated core behavior: Team2 authoritative `engine.py`, `studio_adapter.py`, `studio_integration.py`, `agents_api.py` staged only in isolated branch (original protected). All six blobs checked against original PR#12.
3. Missing Team2 V6 integration tests in QA copy: staged Team2 tests + new `test_qa_combined_v6_contract.py`; four core cases independently rechecked with QA reference.
4. Missing unified offline intake of operating Native / independent QA raw report: added read-only `scripts/qa_combined_e2e_check.py`, exact original byte SHA, job/case guards, independent Python and Studio QA states; deliberately BLOCKED without original QA pair.
5. Raw intake regression: added `tests/test_qa_combined_e2e_cli.py`, malformed JSON, wrong case/Job, missing QA report, synthetic QA pairing. A serialization-only Decimal test initially failed ('60500.00' vs '60500'); corrected to numeric Decimal equality without changing the calculation.

**Residual external blockers:** operating V5 live saved Config/Native and Python result, QA copy actual Native/IndependentQA raw, same original PDF SHA/Job binding, Human Gold, E1/E2/E3 experimental evidence, official original-repo combined release CI. No claims of actual live E2E.
