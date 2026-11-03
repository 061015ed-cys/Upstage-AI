"""Reproduce PR #12 valid JSON type policy against latest PR #11 wrappers.

All records here are synthetic; a local match never proves cloud delivery.
"""
from copy import deepcopy

import pytest

from leadtime_guardian.qa.input_delivery import audit_normalize_qa_input


def inspect_quantity(left, right):
    def doc(value):
        return {
            "document_id": "SYN-PO-C001", "document_type": "purchase_order",
            "items": [{"quantity": value}],
        }

    return audit_normalize_qa_input(
        {"status": "COMPLETED", "case_id": "C001",
         "output": {"documents": [doc(left)]}},
        {"case_id": "C001", "normalized_documents": [doc(right)]},
        expected_case_id="C001",
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ((1, 2), [1, 2]),
        ((1, 2), (1, 2)),
        ({1: "x"}, {"1": "x"}),
        ({1: "x"}, {1: "x"}),
        ({1: "x", "a": 2}, {1: "x", "a": 2}),
    ],
)
def test_non_json_container_or_integer_key_fails_closed(left, right):
    result = inspect_quantity(left, right)
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MISMATCH"
    assert result["qa_status"] == "FAIL"
    assert result["actual_cloud_input_authenticated"] is False
    assert result["release_or_merge_authorized"] is False


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (0, False), (1, True), (100, 100.0), (0, 0.0),
        (None, ""), (None, "null"), ([1, 2], [2, 1]),
        (float("nan"), float("nan")),
        (float("inf"), float("inf")),
    ],
)
def test_strict_type_difference_and_nonfinite_json_fail_closed(left, right):
    report = inspect_quantity(left, right)
    assert report["input_delivery_status"] == "LOCAL_CONTENT_MISMATCH"
    assert report["qa_status"] == "FAIL"


def test_object_key_order_is_not_a_content_change_and_no_cloud_claim():
    left = {"quantity": 100, "quote": None}
    right = {"quote": None, "quantity": 100}
    report = inspect_quantity(left, right)
    assert report["input_delivery_status"] == "LOCAL_CONTENT_MATCH"
    assert report["qa_status"] == "BLOCKED"
    assert report["actual_cloud_input_authenticated"] is False


def test_input_docs_are_not_mutated():
    payload = {"inner": [100, None]}
    clone = deepcopy(payload)
    inspect_quantity(payload, payload)
    assert payload == clone


def test_case_id_binding_and_wrapper_regressions_are_kept():
    docs = [{"document_id": "PO", "document_type": "purchase_order"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "case_id": "C001",
         "output": {"documents": docs}},
        {"case_id": "C013", "input": {"normalized_documents": docs}},
        expected_case_id="C001",
    )
    assert result["case_binding_conflict"] is True
    assert result["qa_status"] == "FAIL"
