"""One-command read-only evidence inventory; never changes original files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from leadtime_guardian.qa.release_inventory import audit_release_folder, render_markdown


def _write_reports_exclusively(
    reports: list[tuple[Path, str]],
) -> None:
    """All-or-rollback output creation; never overwrite original evidence.

    The paths must be distinct even when one uses a symlinked parent.
    Exclusively create each file and remove only files created in this call
    if a subsequent create/write fails. No existing source is touched.
    """
    if len({path.resolve(strict=False) for path, _ in reports}) != len(reports):
        raise FileExistsError("JSON and Markdown report paths must differ")

    created: list[Path] = []
    try:
        for path, body in reports:
            with path.open("x", encoding="utf-8") as output:
                created.append(path)
                output.write(body)
    except OSError:
        for path in reversed(created):
            try:
                path.unlink()
            except OSError:
                pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--markdown-report", type=Path)
    args = parser.parse_args()
    result = audit_release_folder(args.manifest)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        reports = []
        if args.json_report is not None:
            reports.append((args.json_report, rendered))
        if args.markdown_report is not None:
            reports.append((args.markdown_report, render_markdown(result)))
        _write_reports_exclusively(reports)
    except OSError:
        result["status"] = "FAIL"
        result["release_authorized"] = False
        result["blocking_issues"].append({
            "issue_code": "REPORT_OUTPUT_NOT_WRITABLE", "source": "cli",
        })
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    return 1 if result["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
