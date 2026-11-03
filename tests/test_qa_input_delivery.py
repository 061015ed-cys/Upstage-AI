"""No assertion of cloud delivery from local Normalize status alone."""
from leadtime_guardian.qa.input_delivery import audit_normalize_qa_input


def test_completed_normalize_does_not_imply_qa_input_delivery():
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": [{"document_id": "A"}]}}
    )
    assert result["input_delivery_status"] == "UNKNOWN"
    assert result["qa_status"] == "BLOCKED"


def test_explicit_qa_input_payload_match_is_only_local_evidence():
    value = [{"document_id": "A"}, {"document_id": "B"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": value}},
        {"normalized_documents": value},
    )
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MATCH"
    assert result["qa_status"] == "BLOCKED"
    assert result["actual_cloud_input_authenticated"] is False


def test_qa_input_payload_mismatch_is_error():
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": [1, 2, 3]}},
        {"normalized_documents": [1, 2, 4]},
    )
    assert result["qa_status"] == "FAIL"
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MISMATCH"


def test_qa_missing_report_is_not_evidence_of_missing_transmission():
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": [1]}},
        qa_report={
            "issues": [{"issue_code": "NORMALIZED_OUTPUT_NOT_PROVIDED"}],
            "execution_provenance": None,
        },
    )
    assert result["input_delivery_status"] == "UNKNOWN"
    assert "QA_REPORTS_NORMALIZED_OUTPUT_MISSING" in {
        i["issue_code"] for i in result["issues"]
    }


def test_incomplete_normalize_not_falsely_mapped_to_qa_input_failure():
    result = audit_normalize_qa_input({"status": "queued"})
    assert result["input_delivery_status"] == "NORMALIZE_NOT_COMPLETED"
    assert result["qa_status"] == "BLOCKED"


def test_native_normalize_content_string_and_wrapped_qa_input_match_locally():
    import json
    docs = [{"document_id": "D1", "document_type": "purchase_order"},
            {"document_id": "D2", "document_type": "delivery_notice"},
            {"document_id": "D3", "document_type": "quotation"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "content": json.dumps({"documents": docs})},
        {"input": {"normalized_documents": json.dumps(docs)}},
    )
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MATCH"
    assert result["normalize_document_count"] == 3
    assert result["qa_input_document_count"] == 3
    assert result["qa_input_json_encoding_layers"] == 1
    assert result["actual_cloud_input_authenticated"] is False
    assert result["qa_status"] == "BLOCKED"


def test_malformed_qa_json_string_is_not_silently_repaired():
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": [{"document_id": "D1"}]}},
        {"normalized_documents": '[{"document_id":"D1",]'},
    )
    assert result["input_delivery_status"] == "UNKNOWN"
    assert result["qa_status"] == "BLOCKED"
    assert "QA_INPUT_MALFORMED_JSON_STRING" in {
        x["issue_code"] for x in result["issues"]
    }


def test_double_json_wrapped_qa_input_is_not_promoted_to_delivery():
    import json
    docs = [{"document_id": "D1"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": docs}},
        {"normalized_documents": json.dumps(json.dumps(docs))},
    )
    assert result["input_delivery_status"] == "QA_INPUT_WRAPPING_UNVERIFIED"
    assert result["qa_input_json_encoding_layers"] == 2
    assert "QA_INPUT_DOUBLE_JSON_WRAPPED" in {
        x["issue_code"] for x in result["issues"]
    }


def test_qa_report_missing_claim_does_not_override_locally_observed_input():
    docs = [{"document_id": "D1"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": docs}},
        {"normalized_documents": docs},
        {"issues": [{"issue_code": "NORMALIZED_OUTPUT_NOT_PROVIDED"}]},
    )
    assert result["input_delivery_status"] == "LOCAL_CONTENT_MATCH"
    assert result["qa_status"] == "BLOCKED"
    assert "QA_REPORTS_NORMALIZED_OUTPUT_MISSING" in {
        x["issue_code"] for x in result["issues"]
    }


def test_qa_input_unrecognized_document_key_is_not_accepted():
    docs = [{"document_id": "D1"}]
    result = audit_normalize_qa_input(
        {"status": "COMPLETED", "output": {"documents": docs}},
        {"input": {"documents": docs}},
    )
    assert result["input_delivery_status"] == "UNKNOWN"
    assert result["qa_status"] == "BLOCKED"
    assert "QA_INPUT_DOCUMENTS_KEY_NOT_OBSERVED" in {
        x["issue_code"] for x in result["issues"]
    }
