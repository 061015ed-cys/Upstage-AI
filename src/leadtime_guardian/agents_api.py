"""Official Upstage Agents transport; contract tests are labeled separately from live runs."""
import hashlib
import json
import math
import re
import time
from datetime import UTC, datetime
from pathlib import Path

BASE_URL = "https://api.upstage.ai/v2"
ACTIVE = {"queued", "in_progress"}


def inspect_pdfs(paths, agent_id):
    """Validate before upload; never accept a gold JSON file in place of a source PDF."""
    if not isinstance(agent_id, str) or not re.fullmatch(r"agt_[A-Za-z0-9]+", agent_id):
        raise ValueError("invalid agent ID")
    if not paths:
        raise ValueError("at least one PDF is required")
    seen, files = set(), []
    for value in paths:
        path = Path(value)
        blob = path.read_bytes()
        if path.suffix.lower() != ".pdf" or not blob.startswith(b"%PDF-"):
            raise ValueError("only source PDFs are accepted")
        digest = hashlib.sha256(blob).hexdigest()
        if digest in seen:
            raise ValueError("duplicate PDF input")
        seen.add(digest)
        if any(item["filename"] == path.name for item in files):
            raise ValueError("duplicate filename")
        files.append({"filename": path.name, "sha256": digest, "bytes": len(blob),
                      "blob": blob})
    return files


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot(response):
    value = response.model_dump(mode="json")
    if not isinstance(value, dict):
        raise TypeError("API response is not an object")
    return value


def run_agent(client, paths, agent_id, destination, *, case_id, config_version,
              prompt_version, execution_mode="contract_test", timeout_seconds=180,
              poll_seconds=2, clock=time.monotonic, sleep=time.sleep, transport_errors=(),
              config_id=None):
    """Upload all PDFs as one job, archive snapshots, and stop safely on errors.

    No automatic POST retry or fixture fallback. The CLI constructs the live SDK
    client with max_retries=0 so an unknown submission outcome is never replayed.
    """
    if execution_mode not in {"live_agents_api", "contract_test", "sdk_http_mock"}:
        raise ValueError("invalid execution mode")
    if config_id is not None and (not isinstance(config_id, str)
                                  or not re.fullmatch(r"cfg_[A-Za-z0-9]+", config_id)):
        raise ValueError("invalid config ID")
    if (not math.isfinite(timeout_seconds) or timeout_seconds <= 0
            or not math.isfinite(poll_seconds) or not 0 < poll_seconds <= 60):
        raise ValueError("invalid timeout or polling interval")
    files = inspect_pdfs(paths, agent_id)
    handled_errors = (OSError, ValueError, TypeError) + transport_errors
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "inputs").mkdir()
    meta = {"execution_mode": execution_mode, "case_id": case_id, "agent_id": agent_id,
            "config_version": config_version, "prompt_version": prompt_version,
            "requested_config_id": config_id,
            "workflow_config_verified": False, "base_url": BASE_URL,
            "started_at_utc": datetime.now(UTC).isoformat(),
            "status": "NEEDS_REVIEW", "studio_status": None, "job_id": None,
            "job_submission_attempted": False, "job_submitted": False,
            "api_upload_attempts": 0, "uploaded_files": [],
            "source_files": [{k: v for k, v in item.items() if k != "blob"} for item in files],
            "evidence_verified_against_pdf": False, "external_procurement_action_taken": False}
    write_json(destination / "run_metadata.json", meta)
    try:
        content = []
        for index, item in enumerate(files):
            staged = destination / "inputs" / item["filename"]
            staged.write_bytes(item["blob"])
            meta["api_upload_attempts"] += 1
            write_json(destination / "run_metadata.json", meta)
            with staged.open("rb") as stream:
                uploaded = snapshot(client.files.create(file=stream, purpose="user_data"))
            write_json(destination / f"upload-{index + 1:02d}.json", uploaded)
            file_id = uploaded.get("id")
            if not isinstance(file_id, str) or not file_id:
                raise ValueError("upload response is missing file ID")
            meta["uploaded_files"].append({"filename": item["filename"], "file_id": file_id})
            content.append({"type": "input_file", "file_id": file_id})
            write_json(destination / "run_metadata.json", meta)
        request = {"model": agent_id, "include": ["last"],
                   "input": [{"role": "user", "content": content}]}
        # Upstage extension absent from the OpenAI SDK's typed signature.
        if config_id is not None:
            request["config_id"] = config_id
        write_json(destination / "job_request.json", request)
        meta["job_submission_attempted"] = True
        write_json(destination / "run_metadata.json", meta)
        sdk_request = {key: value for key, value in request.items() if key != "config_id"}
        if config_id is not None:
            sdk_request["extra_body"] = {"config_id": config_id}
        response = snapshot(client.responses.create(**sdk_request))
        meta["job_submitted"] = True
        started, index = clock(), 0
        while True:
            write_json(destination / f"job-{index:04d}.json", response)
            meta["studio_status"] = response.get("status")
            response_id = response.get("id")
            if not isinstance(response_id, str) or not response_id.strip():
                raise ValueError("job response is missing ID")
            if meta["job_id"] is not None and response_id != meta["job_id"]:
                raise ValueError("job ID changed during polling")
            meta["job_id"] = response_id
            write_json(destination / "run_metadata.json", meta)
            if meta["studio_status"] not in ACTIVE:
                break
            remaining = timeout_seconds - (clock() - started)
            if remaining <= 0:
                raise TimeoutError("poll deadline reached; job may still run on server")
            sleep(min(poll_seconds, remaining))
            response = snapshot(client.responses.retrieve(meta["job_id"], include=["last"]))
            index += 1
        write_json(destination / "studio_final.json", response)
        if meta["studio_status"] != "completed" or response.get("error"):
            raise ValueError("Studio job did not complete successfully")
        # Keep all Parse/Classify/Extract steps for later provenance inspection.
        all_steps = snapshot(client.responses.retrieve(meta["job_id"], include=["all"]))
        write_json(destination / "studio_all_steps.json", all_steps)
        if (all_steps.get("id") != meta["job_id"] or all_steps.get("status") != "completed"
                or all_steps.get("error")):
            raise ValueError("job history ID/status conflicts with completed job")
        meta["status"] = "COMPLETED"
    except handled_errors as exc:
        # SDK exception strings can contain request details; never persist them blindly.
        meta["error_type"] = type(exc).__name__
        code = getattr(exc, "status_code", None)
        if isinstance(code, int):
            meta["http_status"] = code
        meta["review_reason"] = (
            "Run incomplete. Inspect archived snapshots and job_id before any retry; "
            "a timed-out server job is not automatically cancelled.")
    meta["finished_at_utc"] = datetime.now(UTC).isoformat()
    write_json(destination / "run_metadata.json", meta)
    return meta
