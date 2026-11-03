"""Verify the saved C001 Studio archive without starting new Studio jobs."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from leadtime_guardian.qa.archive import verify_c001_archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    result = verify_c001_archive(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["qa_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
