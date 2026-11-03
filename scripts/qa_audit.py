"""Local read-only QA entrypoint; run from repository root."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import audit_json_files, load_json_strict
from leadtime_guardian.qa.portfolio import audit_portfolio


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = audit_json_files(args.case, args.output)
        if args.output is not None and result["qa_status"] == "PASS":
            case = load_json_strict(Path(args.case).read_bytes())
            output = load_json_strict(Path(args.output).read_bytes())
            verified = audit_portfolio(case, output)
            result["issues"].extend(verified["issues"])
            if verified["qa_status"] != "PASS":
                result["qa_status"] = "FAIL"
    except (OSError, ValueError, TypeError) as error:
        result = {"qa_status": "FAIL", "issues": [{"issue_code": "INPUT_ERROR", "reason": str(error)}]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["qa_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
