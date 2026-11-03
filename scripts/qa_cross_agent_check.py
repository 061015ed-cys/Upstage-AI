"""Validate an explicitly exported Studio-to-Python QA handoff.

The validator does not connect to Studio. --require-contract distinguishes
a structural PASS from absent/unverified external artifacts.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.cross_agent import (
    APPROVED_SANDBOX_AGENTS,
    SANDBOX_AGENT_ID,
    audit_cross_agent_handoff,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--qa-report", type=Path)
    parser.add_argument("--expected-agent-id", choices=sorted(APPROVED_SANDBOX_AGENTS),
                        default=SANDBOX_AGENT_ID)
    parser.add_argument("--expected-config-id")
    parser.add_argument("--expected-github-sha")
    parser.add_argument("--require-contract", action="store_true")
    args = parser.parse_args()

    try:
        manifest = load_json_strict(args.manifest.read_bytes())
        native = args.native.read_bytes() if args.native else None
        qa_report = args.qa_report.read_bytes() if args.qa_report else None
    except (OSError, ValueError, UnicodeDecodeError, TypeError) as exc:
        output = {"qa_status": "FAIL", "release_or_merge_authorized": False,
                  "issues": [{"issue_code": "UNREADABLE_HANDOFF_ARTIFACT",
                              "field": "inputs", "reason": type(exc).__name__}]}
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 1

    result = audit_cross_agent_handoff(
        manifest, native_bytes=native, report_bytes=qa_report,
        expected_agent_id=args.expected_agent_id,
        expected_config_id=args.expected_config_id,
        expected_github_sha=args.expected_github_sha,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    if result["qa_status"] == "FAIL":
        return 1
    if args.require_contract and result["qa_status"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
