"""Read-only strict original Stage evidence intake. No provider API requests."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leadtime_guardian.qa.audit import load_json_strict
from leadtime_guardian.qa.stage_trace import STAGES, audit_stage_evidence

MAX_MANIFEST_BYTES = 1024 * 1024  # Identity + relative paths; no raw PDFs.
MAX_STAGE_BYTES = 32 * 1024 * 1024  # Bounded offline JSON intake per Stage.


def inspect_manifest_path(provided_path: Path) -> dict:
    """Reuse exact same stage intake in standalone and combined E2E CLI."""
    try:
        manifest_path = provided_path.resolve(strict=True)
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError("stage manifest exceeds bounded metadata limit")
        manifest = load_json_strict(manifest_path.read_bytes())
        if not isinstance(manifest, dict):
            raise TypeError("manifest must be a JSON object")
        metadata = manifest.get("stages", {})
        if not isinstance(metadata, dict):
            raise TypeError("stages must be object")
        def read_relative(relative: str) -> bytes:
            if (not isinstance(relative, str) or not relative
                    or Path(relative).is_absolute()):
                raise ValueError("path must be nonempty manifest-relative")
            path = (manifest_path.parent / relative).resolve(strict=True)
            if not path.is_relative_to(manifest_path.parent):
                raise ValueError("path escapes manifest directory")
            if path.stat().st_size > MAX_STAGE_BYTES:
                raise ValueError("Stage JSON exceeds offline evidence size limit")
            return path.read_bytes()

        artifacts = {}
        for name in STAGES:
            item = metadata.get(name)
            if not isinstance(item, dict):
                continue
            if name == "Extract" and isinstance(item.get("branches"), dict):
                artifacts[name] = {}
                for kind, entry in item["branches"].items():
                    if isinstance(entry, dict) and entry.get("path") is not None:
                        artifacts[name][kind] = read_relative(entry["path"])
                continue
            if item.get("path") is not None:
                artifacts[name] = read_relative(item["path"])
        result = audit_stage_evidence(manifest, artifacts)
    except (OSError, TypeError, ValueError, UnicodeDecodeError, RecursionError):
        result = {
            "status": "FAIL", "release_or_merge_authorized": False,
            "studio_live_execution_authenticated": False,
            "issues": [{"issue_code": "MANIFEST_OR_STAGE_FILE_UNREADABLE",
                        "stage": "cli", "severity": "ERROR"}],
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    result = inspect_manifest_path(args.manifest)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if result["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
