"""Type-sensitive bridge: original XLSX bytes -> reviewed cells -> CSV candidate.

This module never authenticates a human or promotes Gold. No implicit casting
of numeric identifiers, amounts, dates, null, zero or blank strings is allowed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from qa.inventory import strict_json
from qa.review_records import KEYS, load_csv, valid_timestamp
from qa.xlsx_snapshot import snapshot

MUTABLE = {"reviewer", "reviewed_at", "decision", "approval_state"}
DECISIONS = {None, "", "ACCEPT", "CORRECT", "AMBIGUOUS", "MISSING", "NOT_IN_SOURCE"}
STATES = {None, "", "PENDING", "REVIEWED_BY_MEMBER3", "TEAM_APPROVED"}


def parse_candidate(text, kind):
    if kind == "string":
        return text
    if kind == "null":
        if text != "null":
            raise ValueError("null literal required")
        return None
    if kind in {"integer", "boolean"}:
        value = strict_json(text)
        if type(value) is not (int if kind == "integer" else bool):
            raise ValueError("invalid typed value")
        return value
    raise ValueError("unsupported candidate kind")


def compare_snapshot(data, csv_bytes):
    baseline_rows = load_csv(csv_bytes)
    columns = list(baseline_rows[0])
    cells = {(cell["row"], cell["column"]): cell for cell in data["cells"]}
    headers = {}
    for col in range(1, data["max_column"] + 1):
        item = cells.get((1, col))
        if item:
            name = item["value"]
            if not isinstance(name, str) or name in headers:
                raise ValueError("duplicate or non-text XLSX header")
            headers[name] = col
    if set(headers) != set(columns):
        raise ValueError("XLSX header mismatch")
    if data["issues"] or data["hidden_rows"] or data["hidden_columns"] or (
            data["sheet_state"] != "visible"):
        return {"status": "BLOCKED", "issues": [{"code": "UNSAFE_XLSX_LAYOUT"}],
                "gold_promoted": False, "official_metrics_eligible": False}
    baseline = {}
    for row in baseline_rows:
        key = tuple(row[col] for col in KEYS)
        if any(not k for k in key) or key in baseline:
            raise ValueError("invalid or duplicate CSV field key")
        baseline[key] = row
    found, issues, accepted = set(), [], 0
    for number in range(2, data["max_row"] + 1):
        row = {name: cells.get((number, col), {}).get("value") for name, col in headers.items()}
        if all(value is None for value in row.values()):
            continue
        key = tuple(row[name] for name in KEYS)
        if key in found:
            issues.append({"row": number, "code": "DUPLICATE_FIELD"})
            continue
        found.add(key)
        if key not in baseline:
            issues.append({"row": number, "code": "UNKNOWN_FIELD"})
            continue
        reference = baseline[key]
        for name in columns:
            if name in MUTABLE:
                continue
            observed, text = row[name], reference[name]
            if name == "page":
                matches = type(observed) is int and str(observed) == text
            elif name == "normalized_candidate":
                try:
                    correct = parse_candidate(text, reference["value_type"])
                    if reference["value_type"] == "null":
                        # Explicit literal only. Blank Excel cells are not verified nulls.
                        matches = type(observed) is str and observed == "null"
                    else:
                        matches = type(observed) is type(correct) and observed == correct
                except ValueError:
                    matches = False
            elif text == "" and observed is None:
                # A missing source-text cell is not proof that a field was absent.
                matches = True
                if name == "source_text" and reference["value_type"] == "null":
                    issues.append({"row": number, "field": name,
                                   "code": "ABSENCE_EVIDENCE_REQUIRES_HUMAN_REVIEW"})
            else:
                matches = type(observed) is str and observed == text
            if not matches:
                issues.append({"row": number, "field": name,
                               "code": "BASELINE_TYPE_OR_VALUE_MISMATCH"})
        decision, state = row["decision"], row["approval_state"]
        if decision not in DECISIONS or state not in STATES:
            issues.append({"row": number, "code": "INVALID_REVIEW_STATE"})
        if decision != "ACCEPT" and state in {"REVIEWED_BY_MEMBER3", "TEAM_APPROVED"}:
            issues.append({"row": number, "code": "APPROVAL_WITHOUT_ACCEPT"})
        if decision not in {None, "", "ACCEPT"}:
            issues.append({"row": number, "code": "CORRECTION_REQUIRES_NEW_VERSION"})
        if decision == "ACCEPT":
            accepted += 1
            if not isinstance(row["reviewer"], str) or not row["reviewer"].strip():
                issues.append({"row": number, "code": "MISSING_REVIEWER"})
            if not valid_timestamp(row["reviewed_at"]):
                issues.append({"row": number, "code": "INVALID_REVIEW_TIME"})
            if state not in {"REVIEWED_BY_MEMBER3", "TEAM_APPROVED"}:
                issues.append({"row": number, "code": "REVIEW_NOT_APPROVED"})
    for missing in sorted(baseline.keys() - found):
        issues.append({"code": "MISSING_FIELD", "key": list(missing)})
    return {"status": "PASS" if not issues else "BLOCKED",
            "scope": "CELL_AND_BASELINE_CONSISTENCY_ONLY",
            "expected_rows": len(baseline), "received_rows": len(found),
            "claimed_accept_rows": accepted, "issues": issues,
            "human_identity_verified": False, "team_approval_verified": False,
            "gold_promoted": False, "official_metrics_eligible": False}


def inspect_xlsx_review(raw_xlsx, raw_csv, sheet=None):
    snap = snapshot(raw_xlsx, sheet)
    report = compare_snapshot(snap, raw_csv)
    report.update(xlsx_sha256=hashlib.sha256(raw_xlsx).hexdigest(),
                  baseline_sha256=hashlib.sha256(raw_csv).hexdigest(),
                  selected_sheet=snap["sheet"], source_bytes_modified=False)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--sheet")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out in {args.xlsx, args.csv}:
        raise FileExistsError("new output path required")
    report = inspect_xlsx_review(args.xlsx.read_bytes(), args.csv.read_bytes(), args.sheet)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
