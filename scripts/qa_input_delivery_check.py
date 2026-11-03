"""Compare exact saved local Normalize output and QA Step input; never cloud-authenticate."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.input_delivery import audit_normalize_qa_input


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalize", type=Path, required=True)
    parser.add_argument("--qa-input", type=Path)
    parser.add_argument("--qa-report", type=Path)
    parser.add_argument("--case-id")
    args = parser.parse_args()
    try:
        result = audit_normalize_qa_input(
            load_json_strict(args.normalize.read_bytes()),
            load_json_strict(args.qa_input.read_bytes()) if args.qa_input else None,
            load_json_strict(args.qa_report.read_bytes()) if args.qa_report else None,
            expected_case_id=args.case_id,
        )
    except (OSError, ValueError, UnicodeDecodeError, TypeError):
        result = {
            "qa_status": "FAIL", "input_delivery_status": "NOT_VERIFIED",
            "actual_cloud_input_authenticated": False,
            "release_or_merge_authorized": False,
            "issues": [{"issue_code": "UNREADABLE_RAW_STEP_EVIDENCE",
                        "severity": "ERROR"}],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["qa_status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
