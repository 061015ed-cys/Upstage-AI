"""Strict raw Native + IndependentQA → derived manifest + local verification."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.cross_agent import APPROVED_SANDBOX_AGENTS, audit_cross_agent_handoff
from leadtime_guardian.qa.handoff_builder import build_studio_raw_handoff


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--qa-report", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--agent-id", required=True, choices=sorted(APPROVED_SANDBOX_AGENTS))
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--config-version", required=True, type=int)
    parser.add_argument("--github-sha", required=True)
    parser.add_argument("--execution-kind", choices=(
        "ARCHIVED_STUDIO", "ARCHIVED_REPLAY", "NEW_LIVE_STUDIO",
    ), default="ARCHIVED_STUDIO")
    parser.add_argument("--manifest-output", required=True, type=Path)
    args = parser.parse_args()
    try:
        native = args.native.read_bytes()
        report = args.qa_report.read_bytes()
        manifest = build_studio_raw_handoff(
            native, report, case_id=args.case_id, agent_id=args.agent_id,
            config_id=args.config_id, config_version=args.config_version,
            github_sha=args.github_sha, execution_kind=args.execution_kind,
        )
        checked = audit_cross_agent_handoff(
            manifest, native_bytes=native, report_bytes=report,
            expected_agent_id=args.agent_id,
            expected_config_id=args.config_id,
            expected_github_sha=args.github_sha,
        )
        if checked["qa_status"] == "FAIL":
            raise ValueError("mapped manifest failed Cross-Agent validation")
        args.manifest_output.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output = {
            "qa_status": checked["qa_status"],
            "document_qa_status": checked["document_qa_status"],
            "python_qa_status": checked["python_qa_status"],
            "requires_human_review": checked["requires_human_review"],
            "manifest_path": str(args.manifest_output),
            "native_sha256": manifest["studio"]["native_sha256"],
            "original_qa_report_sha256": manifest["studio"]["qa_report_sha256"],
            "release_or_merge_authorized": False,
            "studio_live_execution_authenticated": False,
            "issues": checked["issues"],
        }
    except (OSError, ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        output = {
            "qa_status": "FAIL",
            "reason": type(exc).__name__ + ": " + str(exc),
            "release_or_merge_authorized": False,
            "studio_live_execution_authenticated": False,
        }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if output["qa_status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
