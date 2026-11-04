"""Read-only evaluator. Neither DRAFT nor AI candidates are official Gold."""
import argparse
import json
import re
from pathlib import Path

from qa.inventory import strict_json
from qa.review_records import valid_timestamp

MISSING = object()
DATE_KEYS = {"original_delivery", "revised_delivery", "arrival_date", "eta", "due_date"}


def typed_equal(a, b):
    if b is MISSING or type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(typed_equal(v, b[k]) for k, v in a.items())
    if isinstance(a, list):
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def index_documents(documents):
    if not isinstance(documents, list):
        raise TypeError("expected list")
    result = {}
    for doc in documents:
        if not isinstance(doc, dict):
            raise TypeError("expected object")
        name = doc.get("document_id")
        if not isinstance(name, str) or not name or name in result:
            raise ValueError("missing or duplicate document_id")
        result[name] = doc
    return result


def flatten(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            if not prefix and key == "document_id":
                continue
            yield from flatten(item, (prefix + "." if prefix else "") + key)
    elif isinstance(value, list):
        for n, item in enumerate(value):
            yield from flatten(item, f"{prefix}[{n}]")
    else:
        yield prefix, value


def lookup(value, path):
    node = value
    for step in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if step.startswith("["):
            n = int(step[1:-1])
            if not isinstance(node, list) or n >= len(node):
                return MISSING
            node = node[n]
        elif not isinstance(node, dict) or step not in node:
            return MISSING
        else:
            node = node[step]
    return node


def is_approved(gold):
    if not isinstance(gold, dict):
        return False
    flags = ("human_reviewed", "team_approved", "eligible_for_official_metrics",
             "gold_frozen")
    review = gold.get("approval_provenance")
    return (gold.get("label_status") == "HUMAN_GOLD_FROZEN"
            and all(gold.get(k) is True for k in flags)
            and re.fullmatch(r"[0-9a-f]{64}", str(gold.get("gold_sha256", ""))) is not None
            and isinstance(review, dict)
            and isinstance(review.get("reviewer"), str)
            and bool(review["reviewer"].strip())
            and valid_timestamp(review.get("reviewed_at"))
            and re.fullmatch(r"[0-9a-f]{64}",
                             str(review.get("approval_record_sha256", ""))) is not None)


def approved_evidence(gold):
    """Validate every approved normalized field against its source citation.

    Referenced review hashes are integrity pointers, not identity authentication.
    """
    try:
        documents = index_documents(gold["field_gold_candidate"])
        sources = index_documents(gold["sources"])
        records = gold["approved_field_evidence"]
    except (KeyError, ValueError, TypeError):
        return None
    if not isinstance(records, list) or documents.keys() != sources.keys():
        return None
    expected = {(did, path) for did, doc in documents.items() for path, _ in flatten(doc)}
    if not expected:
        return None
    validated = {}
    for row in records:
        if not isinstance(row, dict):
            return None
        did, path = row.get("document_id"), row.get("field_path")
        try:
            key = did, path
            if key not in expected or key in validated:
                return None
        except TypeError:
            return None
        source = sources[did]
        value = lookup(documents[did], path)
        if (row.get("decision") != "ACCEPT"
                or re.fullmatch(r"[0-9a-f]{64}",
                                str(row.get("review_record_sha256", ""))) is None
                or row.get("source_file_sha256") != source.get("sha256")
                or type(row.get("page")) is not int
                or row["page"] != source.get("source_page") or row["page"] < 1):
            return None
        if value is None:
            if (row.get("absence_confirmed") is not True
                    or row.get("source_original_text") not in (None, "")):
                return None
        elif (not isinstance(row.get("source_original_text"), str)
              or not row["source_original_text"].strip()):
            return None
        validated[key] = row
    return validated if validated.keys() == expected else None


def same_case_id(expected, observed):
    """Only the documented SYN- prefix differs between Gold and Team 1 IDs."""
    if not isinstance(expected, str) or not isinstance(observed, str):
        return False
    return expected.removeprefix("SYN-") == observed.removeprefix("SYN-")


def bound_native(gold, binding):
    if (not isinstance(binding, dict) or binding.get("execution_kind") != "STUDIO_NATIVE"
            or not same_case_id(gold.get("case_id"), binding.get("case_id"))):
        return False
    if not all(isinstance(binding.get(k), str) and binding[k]
               for k in ("job_id", "config_id", "workflow_version")):
        return False
    try:
        expected = index_documents(gold["sources"])
        observed = index_documents(binding["file_bindings"])
    except (KeyError, ValueError, TypeError):
        return False
    if expected.keys() != observed.keys():
        return False
    return all(isinstance(observed[k].get("file_id"), str) and observed[k]["file_id"]
               and expected[k].get("sha256") == observed[k].get("sha256")
               and expected[k].get("filename") == observed[k].get("filename")
               for k in expected)


def metric(n, d):
    return {"status": "MEASURED" if d else "NOT_MEASURED",
            "numerator": n, "denominator": d, "rate": n / d if d else None}


def evaluate(prediction, gold, native=None):
    """Official denominator requires frozen reviewed Gold AND bound native execution."""
    result = {"case_id": gold.get("case_id"), "status": "BLOCKED",
              "accuracy_status": "NOT_MEASURED", "official_metrics_eligible": False,
              "release_authorized": False, "metrics": {}, "field_results": [], "reason": ""}
    if not is_approved(gold):
        result["reason"] = "HUMAN_GOLD_NOT_APPROVED"
        return result
    if not bound_native(gold, native):
        result["reason"] = "NATIVE_JOB_CONFIG_FILE_BINDINGS_REQUIRED"
        return result
    if not isinstance(prediction, dict) or not isinstance(prediction.get("documents"), list):
        result["reason"] = "NATIVE_PREDICTION_REQUIRED"
        return result
    if not same_case_id(gold.get("case_id"),
                        prediction.get("case_id", gold.get("case_id"))):
        result["reason"] = "NATIVE_PREDICTION_CASE_MISMATCH"
        return result
    approved_citations = approved_evidence(gold)
    if approved_citations is None:
        result["reason"] = "APPROVED_FIELD_EVIDENCE_MISSING_OR_INVALID"
        return result
    try:
        gold_docs = index_documents(gold["field_gold_candidate"])
        pred_docs = index_documents(prediction["documents"])
        sources = index_documents(gold["sources"])
    except (KeyError, ValueError, TypeError):
        result["reason"] = "INVALID_DOCUMENT_SET"
        return result
    if gold_docs.keys() != sources.keys():
        result["reason"] = "GOLD_SOURCE_MISMATCH"
        return result
    scores = {k: [0, 0] for k in ("classification", "fields", "null_preservation",
                                  "date_normalization", "receipt_identity",
                                  "quotation_fields", "evidence_linkage", "item_receipt_identity",
                                  "sentinel_preservation", "date_source_preservation")}
    evidence = prediction.get("evidence")
    evidence_issues = []
    if not isinstance(evidence, list):
        evidence_issues.append({"code": "EVIDENCE_NOT_ARRAY"})
        evidence = []
    evidence_index = {}
    seen_evidence = set()
    for record in evidence:
        if not isinstance(record, dict):
            evidence_issues.append({"code": "MALFORMED_EVIDENCE_RECORD"})
            continue
        did, field_path = record.get("document_id"), record.get("field_path")
        if not isinstance(did, str) or not isinstance(field_path, str):
            evidence_issues.append({"code": "INVALID_EVIDENCE_KEY"})
            continue
        key = did, field_path
        if key in seen_evidence:
            evidence_issues.append({"code": "DUPLICATE_EVIDENCE",
                                    "document_id": did, "field_path": field_path})
            evidence_index.pop(key, None)
        else:
            evidence_index[key] = record
            seen_evidence.add(key)
        if key not in approved_citations:
            evidence_issues.append({"code": "UNAPPROVED_EVIDENCE_SCOPE",
                                    "document_id": did, "field_path": field_path})
        if ("case_id" in record and
                not same_case_id(gold.get("case_id"), record["case_id"])):
            evidence_issues.append({"code": "CROSS_CASE_EVIDENCE",
                                    "document_id": did, "field_path": field_path})
        if type(record.get("page")) is not int:
            evidence_issues.append({"code": "INVALID_EVIDENCE_PAGE",
                                    "document_id": did, "field_path": field_path})
    failed = []
    missing = []
    for did, expected in gold_docs.items():
        actual = pred_docs.get(did, {})
        scores["classification"][1] += 1
        scores["classification"][0] += int(typed_equal(
            expected.get("document_type", MISSING), actual.get("document_type", MISSING)))
        for path, want in flatten(expected):
            got = lookup(actual, path)
            ok = typed_equal(want, got)
            scores["fields"][1] += 1
            scores["fields"][0] += int(ok)
            if not ok:
                failed.append({"document_id": did, "field_path": path,
                               "reason": "MISSING" if got is MISSING else "TYPE_OR_VALUE"})
            if got is MISSING:
                missing.append({"document_id": did, "field_path": path})
            column = path.rsplit(".", 1)[-1]
            for category, selected in (
                ("null_preservation", want is None),
                ("date_normalization", column in DATE_KEYS and want is not None),
                ("receipt_identity", column == "receipt_id"),
                ("quotation_fields", path.startswith("quote.")),
                ("item_receipt_identity", path.startswith("items[") and
                 column in {"product_id", "receipt_id"}),
                ("sentinel_preservation", want is None or
                 (type(want) is str and want == "") or
                 (type(want) is int and want == 0) or
                 (type(want) is bool and want is False)),
            ):
                if selected:
                    scores[category][1] += 1
                    scores[category][0] += int(ok)
            source = sources[did]
            approved_citation = approved_citations[did, path]
            # Each output slot is counted once; raw text must match approved source.
            scores["evidence_linkage"][1] += 1
            e = evidence_index.get((did, path))
            if (e is not None
                    and type(e.get("page")) is int
                    and ("case_id" not in e or
                         same_case_id(gold.get("case_id"), e["case_id"]))
                    and e.get("source_file_sha256") == source.get("sha256")
                    and e.get("page") == source.get("source_page")
                    and e.get("source_original_text") == approved_citation.get(
                        "source_original_text")
                    and (want is not None or
                         (e.get("absence_confirmed") is True
                          and e.get("review_record_sha256") ==
                          approved_citation.get("review_record_sha256")))):
                scores["evidence_linkage"][0] += 1
    # Preserve original language dates separately from their normalized ISO values.
    for did, source in sources.items():
        for entry in source.get("date_evidence", []):
            scores["date_source_preservation"][1] += 1
            e = evidence_index.get((did, entry.get("field")))
            if (e is not None and type(e.get("page")) is int
                    and ("case_id" not in e or
                         same_case_id(gold.get("case_id"), e["case_id"]))
                    and e.get("source_original_text") == entry.get("source_text")
                    and approved_citations.get((did, entry.get("field")), {}).get(
                        "source_original_text") == entry.get("source_text")
                    and e.get("source_file_sha256") == source.get("sha256")
                    and e.get("page") == source.get("source_page")):
                scores["date_source_preservation"][0] += 1
    po = {d.get("po_id") for d in gold_docs.values() if isinstance(d.get("po_id"), str)}
    conflict = len(po) > 1
    detected = typed_equal(conflict, prediction.get("po_conflict_detected", MISSING))
    blocked = not conflict or prediction.get("business_status") == "BLOCKED"
    scores["po_conflict_detection"] = [int(detected), 1]
    scores["po_conflict_business_block"] = [int(conflict and blocked), int(conflict)]
    # Incidence is a missing-field rate (lower is better), not detection accuracy.
    scores["missing_field_incidence"] = [len(missing), scores["fields"][1]]
    result["metrics"] = {key: metric(*score) for key, score in scores.items()}
    result["field_results"] = failed
    result["evidence_issues"] = evidence_issues
    result["missing_fields"] = missing
    result["extra_document_ids"] = sorted(pred_docs.keys() - gold_docs.keys())
    result["accuracy_status"] = "MEASURED"
    result["official_metrics_eligible"] = True
    result["status"] = ("PASS" if not failed and not evidence_issues
                        and not result["extra_document_ids"]
                        and detected and blocked
                        and scores["evidence_linkage"][0] == scores["evidence_linkage"][1]
                        and scores["date_source_preservation"][0] ==
                        scores["date_source_preservation"][1]
                        else "FAIL")
    result["reason"] = "VALIDATED" if result["status"] == "PASS" else "MISMATCH"
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gold", type=Path, required=True)
    p.add_argument("--prediction", type=Path)
    p.add_argument("--binding", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists() or args.out in {args.gold, args.prediction, args.binding}:
        raise FileExistsError("output must be new")
    def read(path):
        return strict_json(path.read_text(encoding="utf-8")) if path else None
    result = evaluate(read(args.prediction), read(args.gold), read(args.binding))
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
