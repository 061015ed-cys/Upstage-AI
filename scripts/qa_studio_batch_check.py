"""Check documented Studio B0 grouping before requesting a paid E1 comparison."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.studio_batch import audit_studio_case_batch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--config-id")
    parser.add_argument("--config-version", type=int)
    parser.add_argument("--expected-job-id")
    args = parser.parse_args()
    try:
        result = audit_studio_case_batch(
            load_json_strict(args.report.read_bytes()),
            expected_case_id=args.case_id,
            expected_config_id=args.config_id,
            expected_config_version=args.config_version,
            expected_job_id=args.expected_job_id,
        )
    except (OSError, TypeError, ValueError, UnicodeDecodeError):
        result = {
            "qa_status": "FAIL",
            "single_case_grouping_status": "NOT_VERIFIED",
            "experiment_comparison_allowed": False,
            "release_or_merge_authorized": False,
            "issues": [{"issue_code": "INVALID_OR_UNREADABLE_BATCH_REPORT",
                        "field": "report", "severity": "ERROR"}],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["qa_status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
