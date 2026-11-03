"""Archive a real Studio export and run the existing engine through the strict boundary."""
import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

def main():
    from leadtime_guardian.engine import blocked_result
    from leadtime_guardian.provenance import provenance_sidecar
    from leadtime_guardian.strict_json import loads_strict
    from leadtime_guardian.studio_integration import (
        analyze_studio_documents,
        documents_from_export,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config-version", required=True)
    parser.add_argument("--prompt-version", required=True)
    args = parser.parse_args()
    # Read once so the archive and its digest describe exactly the bytes analyzed.
    export_bytes = args.export.read_bytes()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "studio_original.json").write_bytes(export_bytes)
    metadata = {"run_id": args.run_id, "config_version": args.config_version,
                "prompt_version": args.prompt_version,
                "processed_at_utc": datetime.now(UTC).isoformat(),
                "export_sha256": hashlib.sha256(export_bytes).hexdigest(),
                "studio_provenance": "user-supplied export; verify against native run history",
                "evidence_verified_against_pdf": False}
    raw, base, documents = None, None, []
    try:
        base = loads_strict(args.base.read_bytes())
        schema = loads_strict((ROOT / "configs/schemas/document_extraction.schema.json").read_bytes())
        raw = loads_strict(export_bytes)
        documents = documents_from_export(raw, expected_job_id=args.run_id)
        result = analyze_studio_documents(base, documents, schema)
        (args.output / "normalized_documents.json").write_text(
            json.dumps(documents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, TypeError, KeyError) as exc:
        result = blocked_result(base, [f"EXPORT:{type(exc).__name__}:{exc}"])
    sidecar = provenance_sidecar(raw, documents, result, metadata["export_sha256"])
    for name, data in (("analysis.json", result), ("run_metadata.json", metadata),
                       ("provenance.json", sidecar)):
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
