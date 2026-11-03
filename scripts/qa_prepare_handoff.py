"""Build a reviewed handoff manifest from exported Studio artifacts, offline.

No Studio network calls. Never silently convert an unknown IndependentQA
report schema to a fabricated normalized verdict.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.cross_agent import HANDOFF_VERSION, audit_cross_agent_handoff
from leadtime_guardian.qa.evidence import audit_export_binding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-export", required=True, type=Path)
    parser.add_argument("--execution-record", required=True, type=Path)
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--qa-report", required=True, type=Path)
    parser.add_argument("--github-sha", required=True)
    parser.add_argument("--execution-kind", choices=(
        "NEW_LIVE_STUDIO", "ARCHIVED_STUDIO", "ARCHIVED_REPLAY",
        "SDK_HTTP_MOCK", "FAKE_CLIENT_TEST", "SYNTHETIC_FIXTURE",
    ), default="ARCHIVED_STUDIO")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    def error(code: str) -> int:
        print(json.dumps({"qa_status": "FAIL", "issue_code": code,
                          "manifest_written": False}, sort_keys=True))
        return 1

    try:
        config = load_json_strict(args.config_export.read_bytes())
        record = load_json_strict(args.execution_record.read_bytes())
        native_bytes = args.native.read_bytes()
        report_bytes = args.qa_report.read_bytes()
        native = load_json_strict(native_bytes)
        report = load_json_strict(report_bytes)
    except (OSError, ValueError, TypeError, UnicodeDecodeError):
        return error("INVALID_OR_MISSING_EXPORT_BYTES")

    if not all(isinstance(x, dict) for x in (config, record, native, report)):
        return error("INVALID_EXPORT_STRUCTURE")

    # This is a reviewed-adapter boundary. Unknown Studio report shapes
    # are blocked rather than guessed or converted from unrelated fields.
    required_report_keys = ("document_qa_status", "python_qa_status", "issues")
    if any(k not in report for k in required_report_keys):
        return error("QA_REPORT_MAPPING_REVIEW_REQUIRED")

    meta = native.get("metadata")
    if not isinstance(meta, dict) or not isinstance(meta.get("source_files"), list):
        return error("NATIVE_SOURCE_MANIFEST_MISSING")
    if any(not isinstance(x, dict) or not isinstance(x.get("file_id"), str)
           for x in meta["source_files"]):
        return error("NATIVE_SOURCE_FILE_ID_INVALID")

    origin = config.get("exportedFrom")
    if not isinstance(origin, dict):
        return error("CONFIG_PROVENANCE_MISSING")

    manifest = {
        "protocol_version": HANDOFF_VERSION,
        "producer": "UPSTAGE_QA_SANDBOX",
        "studio": {
            "agent_id": origin.get("workflowId"),
            "config_id": origin.get("configId"),
            "config_version": origin.get("configVer"),
            "job_id": record.get("job_id"),
            "step_run_id": record.get("native_step_run_id"),
            "execution_kind": args.execution_kind,
            "input_file_ids": [x["file_id"] for x in meta["source_files"]],
            "native_sha256": hashlib.sha256(native_bytes).hexdigest(),
            "qa_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        },
        "verdict": {
            "document_qa_status": report["document_qa_status"],
            "python_qa_status": report["python_qa_status"],
            "issues": report["issues"],
        },
        "github": {
            "repository": "dohun3540-crypto/leadtime-guardian-agent.copy",
            "head_sha": args.github_sha,
            "contract_version": HANDOFF_VERSION,
        },
    }

    binding = audit_export_binding(manifest, config, record)
    contract = audit_cross_agent_handoff(manifest, native_bytes=native_bytes,
                                         report_bytes=report_bytes,
                                         expected_github_sha=args.github_sha)
    if binding["qa_status"] == "FAIL" or contract["qa_status"] == "FAIL":
        print(json.dumps({
            "qa_status": "FAIL", "manifest_written": False,
            "binding_issues": binding["issues"],
            "contract_issues": contract["issues"],
        }, indent=2, sort_keys=True))
        return 1

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Do not overwrite another person's prepared artifact.
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        return error("MANIFEST_OUTPUT_EXISTS")
    except OSError:
        return error("MANIFEST_OUTPUT_UNWRITABLE")

    print(json.dumps({
        "qa_status": contract["qa_status"],
        "export_binding_status": binding["qa_status"],
        "manifest_written": True,
        "output": str(args.output),
        "studio_authenticated": False,
        "release_or_merge_authorized": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
