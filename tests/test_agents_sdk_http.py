"""Real OpenAI SDK over loopback HTTP; simulated responses, never live predictions."""
import json
import threading
import time
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from openai import APIError, OpenAI

from leadtime_guardian.agents_api import run_agent

ROOT = Path(__file__).resolve().parents[1]
PDFS = sorted((ROOT / "data/cases/SYN-C001").glob("*.pdf"))
DUMMY_KEY = "sdk-http-mock-credential-not-real"


def response(status="completed", *, error=None):
    return {"id": "job_HTTPMOCK", "object": "response", "created_at": 1,
            "model": "agt_HTTPMOCK", "status": status, "error": error,
            "output": [{"id": "msg_mock", "type": "message", "role": "assistant",
                        "status": "completed", "model": "step_mock",
                        "content": [{"type": "output_text", "text": '{"mock_only":true}',
                                     "annotations": [], "additional_values": '{"mock":true}'}]}]}


@pytest.fixture
def server():
    state = SimpleNamespace(requests=[], upload_error=None, submit_error=None,
                            submit_delay=0, statuses=iter(["queued", "in_progress", "completed"]),
                            last="queued", file_index=0, all_error=None)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, code, data):
            blob = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            try:
                self.wfile.write(blob)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_POST(self):
            blob = self.rfile.read(int(self.headers["Content-Length"]))
            # Never retain Authorization itself, even for a dummy credential.
            entry = {"method": "POST", "path": self.path,
                     "authorized": self.headers.get("Authorization") == "Bearer " + DUMMY_KEY}
            state.requests.append(entry)
            if self.path == "/v2/files":
                message = BytesParser(policy=policy.default).parsebytes(
                    ("Content-Type: " + self.headers["Content-Type"] + "\r\n\r\n").encode() + blob)
                parts = {part.get_param("name", header="Content-Disposition"): part
                         for part in message.iter_parts()}
                entry.update(purpose=parts["purpose"].get_content(),
                             filename=parts["file"].get_filename(),
                             pdf=parts["file"].get_payload(decode=True))
                if state.upload_error:
                    self.reply(state.upload_error, {"error": {"message": DUMMY_KEY}})
                    return
                state.file_index += 1
                self.reply(200, {"id": f"file-{state.file_index}", "object": "file",
                                 "bytes": len(entry["pdf"]), "created_at": 1,
                                 "filename": entry["filename"], "purpose": "user_data"})
            elif self.path == "/v2/responses":
                entry["json"] = json.loads(blob)
                time.sleep(state.submit_delay)
                if state.submit_error:
                    self.reply(state.submit_error, {"error": {"message": DUMMY_KEY}})
                    return
                state.last = next(state.statuses, state.last)
                self.reply(200, response(state.last))
            else:
                self.reply(404, {})

        def do_GET(self):
            state.requests.append({"method": "GET", "path": self.path,
                                   "authorized": self.headers.get("Authorization")
                                   == "Bearer " + DUMMY_KEY})
            if "include=all" in self.path or "include%5B%5D=all" in self.path:
                if state.all_error:
                    self.reply(state.all_error, {"error": {"message": DUMMY_KEY}})
                    return
            else:
                state.last = next(state.statuses, state.last)
            self.reply(200, response(state.last))

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    state.url = f"http://127.0.0.1:{httpd.server_port}/v2"
    yield state
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=2)


def execute(server, target, *, sdk_timeout=1, **kwargs):
    with OpenAI(api_key=DUMMY_KEY, base_url=server.url, timeout=sdk_timeout, max_retries=0,
                http_client=httpx.Client(trust_env=False)) as client:
        return run_agent(client, PDFS, "agt_HTTPMOCK", target, case_id="SYN-C001-MOCK-ONLY",
                         config_version="mock-config", prompt_version="mock-prompt",
                         execution_mode="sdk_http_mock", poll_seconds=0.001,
                         transport_errors=(APIError,), **kwargs)


def assert_no_secret(target):
    assert all(DUMMY_KEY.encode() not in p.read_bytes() for p in target.rglob("*") if p.is_file())


def test_sdk_multipart_single_job_polling_and_step_extras(server, tmp_path):
    target = tmp_path / "run"
    meta = execute(server, target, config_id="cfg_PINNEDMOCK")
    assert meta["status"] == "COMPLETED"
    assert meta["execution_mode"] == "sdk_http_mock"
    uploads = [r for r in server.requests if r["path"] == "/v2/files"]
    jobs = [r for r in server.requests if r["method"] == "POST"
            and r["path"] == "/v2/responses"]
    assert len(uploads) == 3 and len(jobs) == 1
    assert all(r["authorized"] for r in server.requests)
    assert {r["filename"]: r["pdf"] for r in uploads} == {p.name: p.read_bytes() for p in PDFS}
    assert all(r["purpose"] == "user_data" for r in uploads)
    assert jobs[0]["json"] == {"model": "agt_HTTPMOCK", "include": ["last"],
                              "config_id": "cfg_PINNEDMOCK", "input": [{"role": "user",
                              "content": [{"type": "input_file", "file_id": f"file-{i}"}
                                          for i in range(1, 4)]}]}
    assert json.loads((target / "job_request.json").read_text()) == jobs[0]["json"]
    assert len([r for r in server.requests if r["method"] == "GET"]) == 3
    steps = json.loads((target / "studio_all_steps.json").read_text())
    assert steps["output"][0]["model"] == "step_mock"
    assert steps["output"][0]["content"][0]["additional_values"] == '{"mock":true}'
    assert_no_secret(target)


@pytest.mark.parametrize("status", [401, 429, 500])
def test_sdk_upload_error_is_not_retried_or_submitted(server, tmp_path, status):
    server.upload_error = status
    target = tmp_path / "run"
    meta = execute(server, target)
    assert meta["status"] == "NEEDS_REVIEW" and meta["http_status"] == status
    assert meta["job_submission_attempted"] is False
    assert len(server.requests) == 1
    assert_no_secret(target)


def test_sdk_submit_error_is_not_retried_and_exception_body_not_saved(server, tmp_path):
    server.submit_error = 500
    target = tmp_path / "run"
    meta = execute(server, target)
    assert meta["job_submission_attempted"] is True
    assert meta["job_submitted"] is False and meta["job_id"] is None
    assert len([r for r in server.requests if r["path"] == "/v2/responses"]) == 1
    assert_no_secret(target)


def test_sdk_unknown_submit_timeout_is_never_replayed(server, tmp_path):
    server.submit_delay = 0.2
    target = tmp_path / "run"
    meta = execute(server, target, sdk_timeout=0.05)
    assert meta["status"] == "NEEDS_REVIEW"
    assert meta["error_type"] == "APITimeoutError"
    assert meta["job_submission_attempted"] is True and meta["job_id"] is None
    assert len([r for r in server.requests if r["path"] == "/v2/responses"]) == 1
    assert_no_secret(target)


@pytest.mark.parametrize("terminal", ["failed", "cancelled", "incomplete", "unexpected"])
def test_sdk_terminal_failure_cannot_claim_success(server, tmp_path, terminal):
    server.statuses = iter([terminal])
    meta = execute(server, tmp_path / "run")
    assert meta["status"] == "NEEDS_REVIEW" and meta["studio_status"] == terminal
    assert meta["job_id"] == "job_HTTPMOCK"
    assert not any(r["method"] == "GET" for r in server.requests)


def test_sdk_step_history_error_preserves_final_and_job_id(server, tmp_path):
    server.all_error = 500
    target = tmp_path / "run"
    meta = execute(server, target)
    assert meta["status"] == "NEEDS_REVIEW" and meta["job_id"] == "job_HTTPMOCK"
    assert (target / "studio_final.json").exists()
    assert not (target / "studio_all_steps.json").exists()
    assert_no_secret(target)


def test_sdk_poll_timeout_retains_job_without_new_post(server, tmp_path):
    server.statuses = iter(["queued"])
    meta = execute(server, tmp_path / "run", timeout_seconds=0.02)
    assert meta["status"] == "NEEDS_REVIEW" and meta["job_id"] == "job_HTTPMOCK"
    assert meta["error_type"] == "TimeoutError"
    assert len([r for r in server.requests if r["path"] == "/v2/responses"]) == 1


def test_invalid_config_id_blocks_all_http(server, tmp_path):
    with pytest.raises(ValueError, match="config ID"):
        execute(server, tmp_path / "run", config_id="not-a-config")
    assert server.requests == []
