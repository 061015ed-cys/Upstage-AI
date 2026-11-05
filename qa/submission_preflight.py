"""Read-only folder or ZIP integrity precheck; never authorizes submission."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

from qa.inventory import strict_json

SHA = re.compile(r"[0-9a-f]{64}\Z")
SENSITIVE = re.compile(r"(^|/)(\.env|.*\.(?:pem|key|p12|pfx|xlsx)|.*(?:native|secret|token|credential|private).*)$", re.IGNORECASE)
SECRET_BYTES = re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:OPENAI|UPSTAGE)_API_KEY\s*[:=]|ghp_[A-Za-z0-9]{30,}")
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_COUNT = 500


def _safe(name: str) -> bool:
    path = PurePosixPath(name)
    return (bool(name) and "\\" not in name and not name.startswith("/")
            and ":" not in name and all(part not in ("", ".", "..") for part in name.split("/"))
            and str(path) == name)


def inspect(candidate: Path | None, manifest_path: Path) -> dict:
    result = {"status": "BLOCKED", "scope": "PRECHECK_ONLY",
              "release_authorized": False, "submission_authorized": False,
              "file_count": 0, "files": {}, "blockers": []}
    try:
        manifest = strict_json(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            raise TypeError("manifest files list required")
        expected = {}
        for entry in manifest["files"]:
            if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str)
                    or not _safe(entry["path"]) or entry["path"] in expected
                    or type(entry.get("size_bytes")) is not int or entry["size_bytes"] < 0
                    or not isinstance(entry.get("sha256"), str)
                    or not SHA.fullmatch(entry["sha256"])):
                raise ValueError("invalid or duplicate manifest entry")
            expected[entry["path"]] = entry
        if not expected or len(expected) > MAX_COUNT:
            raise ValueError("file count outside bounds")
        if not isinstance(manifest.get("required_evidence_references"), list):
            raise TypeError("evidence reference list required")
        if not manifest["required_evidence_references"]:
            result["blockers"].append("EVIDENCE_REFERENCES_NOT_PROVIDED")
        for ref in manifest["required_evidence_references"]:
            if not isinstance(ref, str) or not _safe(ref) or ref not in expected:
                result["blockers"].append("EVIDENCE_REFERENCE_INVALID")
        approved = manifest.get("approved_sensitive_paths", [])
        if not isinstance(approved, list) or any(not isinstance(x, str) for x in approved):
            raise ValueError("approved_sensitive_paths must be list")
        if candidate is None or not candidate.exists():
            result["blockers"].append("SUBMISSION_CANDIDATE_NOT_PROVIDED")
            return result
        observed = {}
        if candidate.is_dir():
            root = candidate.resolve()
            for path in candidate.rglob("*"):
                if path.is_symlink():
                    result["blockers"].append("SYMLINK_NOT_ALLOWED")
                if not path.is_file():
                    continue
                name = path.relative_to(candidate).as_posix()
                if not path.resolve().is_relative_to(root) or not _safe(name):
                    result["blockers"].append("UNSAFE_PATH")
                    continue
                if path.stat().st_size > MAX_FILE:
                    result["blockers"].append("FILE_TOO_LARGE:" + name)
                    continue
                observed[name] = path.read_bytes()
        elif zipfile.is_zipfile(candidate):
            with zipfile.ZipFile(candidate) as archive:
                all_infos = archive.infolist()
                infos = [x for x in all_infos if not x.is_dir()]
                if len(all_infos) > MAX_COUNT or sum(x.file_size for x in infos) > MAX_TOTAL:
                    raise ValueError("ZIP exceeds limits")
                names = [x.filename.rstrip("/") for x in all_infos]
                if len(names) != len(set(names)):
                    result["blockers"].append("DUPLICATE_ZIP_PATH")
                for info in all_infos:
                    name = info.filename.rstrip("/") if info.is_dir() else info.filename
                    if (not _safe(name) or info.flag_bits & 1
                            or (info.external_attr >> 16) & 0o170000 == 0o120000):
                        result["blockers"].append("UNSAFE_ZIP_ENTRY")
                if archive.testzip() is not None:
                    result["blockers"].append("ZIP_CRC_FAILURE")
                for info in infos:
                    name = info.filename
                    if not _safe(name) or info.flag_bits & 1 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                        result["blockers"].append("UNSAFE_ZIP_ENTRY")
                        continue
                    if info.file_size > MAX_FILE:
                        result["blockers"].append("FILE_TOO_LARGE:" + name)
                        continue
                    observed[name] = archive.read(info)
        else:
            raise ValueError("candidate must be directory or readable ZIP")
        if len(observed) > MAX_COUNT or sum(map(len, observed.values())) > MAX_TOTAL:
            raise ValueError("candidate exceeds limits")
        result["file_count"] = len(observed)
        for name in sorted(set(expected) | set(observed)):
            if name not in observed:
                result["blockers"].append("MISSING_FILE:" + name)
                continue
            if name not in expected:
                result["blockers"].append("UNDECLARED_FILE:" + name)
                continue
            raw = observed[name]
            digest = hashlib.sha256(raw).hexdigest()
            result["files"][name] = {"sha256": digest, "size_bytes": len(raw)}
            if digest != expected[name]["sha256"] or len(raw) != expected[name]["size_bytes"]:
                result["blockers"].append("CONTENT_MISMATCH:" + name)
            if SENSITIVE.search(name) and name not in approved:
                result["blockers"].append("SENSITIVE_FILE_UNAPPROVED:" + name)
            if SECRET_BYTES.search(raw):
                result["blockers"].append("SECRET_CONTENT_DETECTED:" + name)
        reference = manifest.get("public_approval_reference")
        if approved and (not isinstance(reference, str) or not reference.strip()):
            result["blockers"].append("PUBLIC_APPROVAL_REFERENCE_MISSING")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, zipfile.BadZipFile,
            RuntimeError) as exc:
        result["blockers"].append("INVALID_INPUT:" + type(exc).__name__)
    result["status"] = "FAIL" if result["blockers"] else "PRECHECK_ONLY"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    result = inspect(args.candidate, args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
