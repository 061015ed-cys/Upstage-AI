"""Read-only Studio workflow draft graph/null/schema inspection CLI."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.pipeline_config_audit import audit_studio_config_draft


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        content = load_json_strict(args.config.read_bytes())
        result = audit_studio_config_draft(content)
    except (OSError, TypeError, ValueError, UnicodeDecodeError):
        result = {
            "qa_status": "FAIL", "live_run_verified": False,
            "issues": [{"issue_code": "UNREADABLE_STUDIO_CONFIG",
                        "severity": "ERROR", "field": "config"}],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if result["qa_status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
