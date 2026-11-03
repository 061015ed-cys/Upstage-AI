"""Run source PDFs as one official Upstage Agents job, or check prerequisites offline."""
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from leadtime_guardian.agents_api import BASE_URL, inspect_pdfs, run_agent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--pdf", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case-id", default="SYN-C001")
    parser.add_argument("--config-version", default="UNVERIFIED")
    parser.add_argument("--config-id", help="Pin a saved Studio cfg_ version on the API request")
    parser.add_argument("--prompt-version", default="UNVERIFIED")
    parser.add_argument("--timeout-seconds", type=float, default=180)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        files = inspect_pdfs(args.pdf, args.agent_id)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error_type": type(exc).__name__}))
        return 2
    key_available = bool(os.getenv("UPSTAGE_API_KEY", "").strip())
    sdk_available = importlib.util.find_spec("openai") is not None
    prerequisites = {"mode": "offline_preflight", "agent_id": args.agent_id,
                     "source_pdfs": [{k: v for k, v in f.items() if k != "blob"} for f in files],
                     "api_key_available": key_available, "sdk_available": sdk_available,
                     "workflow_access_verified": False, "network_requests_made": 0,
                     "studio_cases_executed": 0}
    if args.preflight:
        print(json.dumps(prerequisites, ensure_ascii=False, indent=2))
        return 0
    if not key_available or not sdk_available:
        print(json.dumps({**prerequisites, "status": "BLOCKED",
                          "reason": "Configure UPSTAGE_API_KEY locally and install optional SDK. "
                          "Do not put credentials in chat, Git, or command arguments."}, indent=2))
        return 2
    if args.output is None:
        parser.error("--output is required for a live run")
    from openai import APIError, OpenAI

    client = OpenAI(api_key=os.environ["UPSTAGE_API_KEY"], base_url=BASE_URL,
                    timeout=30, max_retries=0)
    meta = run_agent(client, args.pdf, args.agent_id, args.output, case_id=args.case_id,
                     config_version=args.config_version, prompt_version=args.prompt_version,
                     execution_mode="live_agents_api", timeout_seconds=args.timeout_seconds,
                     transport_errors=(APIError,), config_id=args.config_id)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
