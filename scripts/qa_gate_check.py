"""Read-only local integration gate; BLOCKED is not permission to release."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.cross_agent import APPROVED_SANDBOX_AGENTS, SANDBOX_AGENT_ID
from leadtime_guardian.qa.gate import build_integration_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--studio-handoff", type=Path)
    parser.add_argument("--studio-native", type=Path)
    parser.add_argument("--studio-qa-report", type=Path)
    parser.add_argument("--expected-agent-id", choices=sorted(APPROVED_SANDBOX_AGENTS),
                        default=SANDBOX_AGENT_ID)
    parser.add_argument("--expected-config-id")
    parser.add_argument("--expected-github-sha")
    parser.add_argument(
        "--require-release", action="store_true",
        help="Return exit code 2 when external release evidence remains blocked",
    )
    args = parser.parse_args()
    result = build_integration_gate(
        args.root, studio_handoff=args.studio_handoff,
        studio_native=args.studio_native, studio_qa_report=args.studio_qa_report,
        expected_agent_id=args.expected_agent_id,
        expected_config_id=args.expected_config_id,
        expected_github_sha=args.expected_github_sha,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    if not result["local_checks_passed"]:
        return 1
    if args.require_release and not result["release_or_merge_authorized"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
