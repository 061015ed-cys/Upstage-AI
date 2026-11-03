"""Read-only team2 ↔ QA local PDF/provenance comparison (never cloud PASS)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.provenance_link import audit_team2_provenance_link


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-handoff", required=True, type=Path)
    parser.add_argument("--team2-provenance", required=True, type=Path)
    parser.add_argument("--qa-pdf-receipt", required=True, type=Path)
    parser.add_argument("--operational-pdf-receipt", required=True, type=Path)
    parser.add_argument("--pdf-root", type=Path)
    args = parser.parse_args()
    try:
        result = audit_team2_provenance_link(
            load_json_strict(args.qa_handoff.read_bytes()),
            load_json_strict(args.team2_provenance.read_bytes()),
            load_json_strict(args.qa_pdf_receipt.read_bytes()),
            load_json_strict(args.operational_pdf_receipt.read_bytes()),
            pdf_root=args.pdf_root,
        )
    except (OSError, TypeError, ValueError, UnicodeDecodeError):
        result = {
            "qa_status": "FAIL",
            "python_qa_status": "NOT_VERIFIED",
            "cross_agent_release_authorized": False,
            "issues": [{"issue_code": "PROVENANCE_INPUT_UNREADABLE",
                        "severity": "ERROR", "field": "input_files"}],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if result["qa_status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
