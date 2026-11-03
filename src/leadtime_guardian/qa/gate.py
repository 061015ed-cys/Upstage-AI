"""Conservative, read-only integration gate; no claimed live evidence is inferred.

The gate executes archived C001 checks, but deliberately leaves CI, current
Studio runs and human-reviewed Gold as unresolved external dependencies.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .archive import verify_c001_archive
from .audit import load_json_strict
from .cross_agent import SANDBOX_AGENT_ID, audit_cross_agent_handoff
from .replay import verify_c001_replay
from .studio_contract import audit_native_envelope

REQUIRED_EXTERNAL_GATES = {
    "source_snapshot_vs_upstream": ("NOT_VERIFIED", "Requires an independent upstream Git SHA comparison"),
    "python_ci_at_current_sha": ("NOT_RUN", "A local audit cannot query the current GitHub Actions conclusion"),
    "independent_qa_ci_at_current_sha": ("NOT_RUN", "A local audit cannot query the current GitHub Actions conclusion"),
    "new_live_c013": ("NOT_RUN", "C013 requires a new independently recorded Studio execution"),
    "new_live_c017": ("NOT_RUN", "C017 requires a new independently recorded Studio execution"),
    "team2_latest_adapter": ("BLOCKED", "Await the team's latest integrated Adapter contract"),
    "team3_source_verified_gold": ("BLOCKED", "Await independently source-reviewed Gold"),
    "measured_extraction_accuracy": ("NOT_VERIFIED", "No independent human Gold accuracy basis"),
}


def build_integration_gate(
    repo_root: str | Path, *, studio_handoff: str | Path | None = None,
    studio_native: str | Path | None = None, studio_qa_report: str | Path | None = None,
    expected_agent_id: str = SANDBOX_AGENT_ID,
    expected_config_id: str | None = None, expected_github_sha: str | None = None,
) -> dict[str, Any]:
    """Execute strictly local archive/replay checks without opening network access.

    A local PASS is never interpreted as permission to merge or submit.
    """
    root = Path(repo_root)
    checks: dict[str, dict[str, Any]] = {}
    for name, verifier in (
        ("c001_archive_integrity", verify_c001_archive),
        ("c001_offline_replay", verify_c001_replay),
    ):
        try:
            result = verifier(root)
        except (OSError, TypeError, ValueError, KeyError, AttributeError) as exc:
            result = {"qa_status": "FAIL",
                      "issues": [{"issue_code": "LOCAL_GATE_EXCEPTION",
                                  "reason": type(exc).__name__, "severity": "ERROR"}]}
        checks[name] = {"status": result["qa_status"], "evidence_type": "LOCAL_CHECK",
                        "issues": result.get("issues", [])}

    archive = root / "data/results/studio_runs/C001_20261030_v4"
    try:
        raw = load_json_strict((archive / "analysis/studio_original.json").read_bytes())
        record = load_json_strict((archive / "execution_record.json").read_bytes())
        if not isinstance(record, dict):
            raise TypeError("execution record must be object")
        native = audit_native_envelope(
            raw,
            expected_job_id=record.get("job_id"),
            expected_step_run_id=record.get("native_step_run_id"),
        )
        if (not isinstance(record.get("job_id"), str) or not record["job_id"]
                or not isinstance(record.get("native_step_run_id"), str)
                or not record["native_step_run_id"]):
            native = {"qa_status": "FAIL", "issues": [
                {"issue_code": "MISSING_EXPECTED_RUN_ID", "severity": "ERROR"}]}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        native = {"qa_status": "FAIL", "issues": [
            {"issue_code": "NATIVE_ARCHIVE_UNREADABLE", "reason": type(exc).__name__, "severity": "ERROR"}]}
    checks["c001_native_envelope"] = {
        "status": native["qa_status"], "evidence_type": "LOCAL_ARCHIVED_CONTRACT_ONLY",
        "issues": native.get("issues", []),
    }

    for name, (status, explanation) in REQUIRED_EXTERNAL_GATES.items():
        checks[name] = {"status": status, "reason": explanation,
                        "evidence_type": "EXTERNAL_REQUIREMENT_NOT_EXECUTED"}

    local = ("c001_archive_integrity", "c001_offline_replay", "c001_native_envelope")
    local_ok = all(checks[name]["status"] == "PASS" for name in local)
    if studio_handoff is not None:
        try:
            manifest = load_json_strict(Path(studio_handoff).read_bytes())
            native = Path(studio_native).read_bytes() if studio_native is not None else None
            report = Path(studio_qa_report).read_bytes() if studio_qa_report is not None else None
            cross = audit_cross_agent_handoff(
                manifest, native_bytes=native, report_bytes=report,
                expected_agent_id=expected_agent_id,
                expected_config_id=expected_config_id,
                expected_github_sha=expected_github_sha,
            )
        except (OSError, ValueError, TypeError, UnicodeDecodeError):
            cross = {"qa_status": "FAIL", "issues": [
                {"issue_code": "UNREADABLE_CROSS_AGENT_HANDOFF", "severity": "ERROR"}]}
        checks["studio_qa_sandbox_handoff"] = {
            "status": cross["qa_status"],
            "evidence_type": "CROSS_AGENT_MANIFEST_CONTRACT_ONLY",
            "issues": cross.get("issues", []),
        }
        # An explicitly supplied but invalid handoff is a local integration
        # failure. A good handoff never self-authorizes actual release.
        if cross["qa_status"] == "FAIL":
            local_ok = False
    readiness = "FAIL" if not local_ok else "BLOCKED"
    return {
        "overall_status": readiness,
        "local_checks_passed": local_ok,
        "release_or_merge_authorized": False,
        "studio_runs_started": 0,
        "human_gold_verified": False,
        "checks": checks,
    }
