"""Separate supplied Studio provenance from business validation and PDF verification."""
from copy import deepcopy


def provenance_sidecar(raw, documents, result, export_sha256):
    metadata = raw.get("metadata") if isinstance(raw, dict) else None
    return {
        "contract_version": "studio-provenance/1",
        "export_sha256": export_sha256,
        "studio_metadata_supplied": deepcopy(metadata),
        "agents_job_id_supplied": raw.get("id") if isinstance(raw, dict) else None,
        "business_validation_status": result["execution_status"],
        "evidence_verified_against_pdf": False,
        "documents": [{
            "document_id": doc.get("document_id"),
            "evidence_supplied": deepcopy(doc.get("evidence", [])),
            "evidence_status": "SUPPLIED_UNVERIFIED" if doc.get("evidence") else "ABSENT",
        } for doc in documents if isinstance(doc, dict)],
    }
