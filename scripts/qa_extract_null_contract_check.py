"""Read-only Extract-vs-Python schema conflict report. NEVER saves Studio config."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.extract_null_contract import analyze_extract_nullable_contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--python-schema", type=Path,
        default=ROOT / "configs/schemas/document_extraction.schema.json",
    )
    args = parser.parse_args()
    try:
        result = analyze_extract_nullable_contract(
            load_json_strict(args.config.read_bytes()),
            load_json_strict(args.python_schema.read_bytes()),
        )
    except (OSError, TypeError, ValueError, UnicodeDecodeError):
        result = {"qa_status": "FAIL", "issues": ["SOURCE_UNREADABLE"],
                  "studio_nullable_support_verified": False,
                  "live_run_verified": False}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["qa_status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
