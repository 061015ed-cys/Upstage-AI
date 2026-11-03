"""No experimental improvement metrics without original B0 AND E1 evidence."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.experiment_compare import (
    audit_b0_e1_readiness,
    compare_normalized_field_values,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b0", required=True, type=Path)
    parser.add_argument("--e1", required=True, type=Path)
    parser.add_argument("--b0-normalize", type=Path)
    parser.add_argument("--e1-normalize", type=Path)
    args = parser.parse_args()
    try:
        result = audit_b0_e1_readiness(
            load_json_strict(args.b0.read_bytes()),
            load_json_strict(args.e1.read_bytes()),
        )
        if args.b0_normalize is not None or args.e1_normalize is not None:
            if args.b0_normalize is None or args.e1_normalize is None:
                result["field_comparison"] = {
                    "field_comparison_status": "BLOCKED",
                    "issues": ["BOTH_NORMALIZE_RAW_REQUIRED"],
                    "human_gold_accuracy": "NOT_MEASURED",
                }
            else:
                b0_bytes = args.b0_normalize.read_bytes()
                e1_bytes = args.e1_normalize.read_bytes()
                result["field_comparison"] = compare_normalized_field_values(
                    load_json_strict(b0_bytes),
                    load_json_strict(e1_bytes),
                    result,
                    original_raw_sha256_by_side={
                        "B0": hashlib.sha256(b0_bytes).hexdigest(),
                        "E1": hashlib.sha256(e1_bytes).hexdigest(),
                    },
                )
    except (ValueError, TypeError, UnicodeDecodeError, OSError):
        result = {
            "eligibility": "FAIL",
            "comparison_status": "NOT_MEASURED",
            "issues": [{"issue_code": "UNREADABLE_COMPARISON_INPUT"}],
            "release_or_merge_authorized": False,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["eligibility"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
