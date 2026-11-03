"""Fake-client transport contracts only: no Upstage network calls or measured accuracy."""
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from leadtime_guardian.agents_api import inspect_pdfs, run_agent

ROOT = Path(__file__).resolve().parents[1]
PDFS = sorted((ROOT / "data/cases/SYN-C001").glob("*.pdf"))
AGENT_ID = "agt_CONTRACTTEST"


class Reply:
    def __init__(self, data):
        self.data = data

    def model_dump(self, mode):
        assert mode == "json"
        return deepcopy(self.data)


class FakeClient:
    def __init__(self, statuses=None, upload_error=None, submit_error=None):
        self.statuses = iter(statuses or ["queued", "in_progress", "completed"])
        self.last_status = "queued"
        self.uploads, self.submissions, self.retrievals = [], [], []
        self.upload_error, self.submit_error = upload_error, submit_error
        self.files = SimpleNamespace(create=self.upload)
        self.responses = SimpleNamespace(create=self.submit, retrieve=self.retrieve)

    def upload(self, **kwargs):
        self.uploads.append({"purpose": kwargs["purpose"], "bytes": kwargs["file"].read()})
        if self.upload_error:
            raise self.upload_error
        return Reply({"id": f"file-{len(self.uploads)}"})

    def next_reply(self):
        self.last_status = next(self.statuses, self.last_status)
        return Reply({"id": "job-CONTRACT", "status": self.last_status, "output": []})

    def submit(self, **kwargs):
        self.submissions.append(kwargs)
        if self.submit_error:
            raise self.submit_error
        return self.next_reply()

    def retrieve(self, job_id, **kwargs):
        self.retrievals.append({"id": job_id, **kwargs})
        if kwargs["include"] == ["all"]:
            return Reply({"id": job_id, "status": "completed", "output": []})
        return self.next_reply()


class Clock:
    def __init__(self):
        self.elapsed = 0

    def now(self):
        return self.elapsed

    def sleep(self, seconds):
        self.elapsed += seconds


def execute(client, target, **kwargs):
    clock = Clock()
    return run_agent(client, PDFS, AGENT_ID, target, case_id="SYN-C001-CONTRACT-ONLY",
                     config_version="fake-config", prompt_version="fake-prompt",
                     clock=clock.now, sleep=clock.sleep, **kwargs)


def test_three_source_pdfs_are_one_job_with_archived_history(tmp_path):
    client = FakeClient()
    meta = execute(client, tmp_path / "run")
    assert meta["status"] == "COMPLETED"
    assert meta["execution_mode"] == "contract_test"
    assert len(client.uploads) == 3
    assert len(client.submissions) == 1
    request = client.submissions[0]
    assert request == {"model": AGENT_ID, "include": ["last"], "input": [
        {"role": "user", "content": [
            {"type": "input_file", "file_id": f"file-{i}"} for i in range(1, 4)]}]}
    assert client.retrievals[-1]["include"] == ["all"]
    assert len(list((tmp_path / "run").glob("job-*.json"))) == 3
    assert (tmp_path / "run/studio_final.json").exists()
    assert (tmp_path / "run/studio_all_steps.json").exists()
    for pdf in PDFS:
        assert (tmp_path / "run/inputs" / pdf.name).read_bytes() == pdf.read_bytes()
    assert meta["evidence_verified_against_pdf"] is False


def test_upload_failure_cannot_submit_job_or_leak_exception_text(tmp_path):
    client = FakeClient(upload_error=ConnectionError("FAKE-SECRET-MUST-NOT-BE-SAVED"))
    meta = execute(client, tmp_path / "run")
    assert meta["status"] == "NEEDS_REVIEW"
    assert not client.submissions
    assert meta["job_submission_attempted"] is False
    assert "FAKE-SECRET" not in json.dumps(meta)


def test_unknown_submission_outcome_is_not_retried(tmp_path):
    client = FakeClient(submit_error=TimeoutError("unknown server outcome"))
    meta = execute(client, tmp_path / "run")
    assert meta["status"] == "NEEDS_REVIEW"
    assert meta["job_submission_attempted"] is True
    assert meta["job_id"] is None
    assert len(client.submissions) == 1
    assert not client.retrievals


def test_poll_deadline_preserves_job_id_and_snapshot(tmp_path):
    client = FakeClient(statuses=["queued"])
    meta = execute(client, tmp_path / "run", timeout_seconds=1, poll_seconds=1)
    assert meta["status"] == "NEEDS_REVIEW"
    assert meta["job_id"] == "job-CONTRACT"
    assert meta["error_type"] == "TimeoutError"
    assert len(client.submissions) == 1
    assert (tmp_path / "run/job-0001.json").exists()
    assert not (tmp_path / "run/studio_final.json").exists()


@pytest.mark.parametrize("terminal", ["failed", "cancelled", "incomplete", "unexpected"])
def test_noncompleted_job_is_archived_without_success(tmp_path, terminal):
    client = FakeClient(statuses=[terminal])
    meta = execute(client, tmp_path / "run")
    assert meta["status"] == "NEEDS_REVIEW"
    assert meta["studio_status"] == terminal
    assert not client.retrievals
    assert json.loads((tmp_path / "run/studio_final.json").read_text())["status"] == terminal


def test_existing_output_is_never_overwritten_or_uploaded(tmp_path):
    client = FakeClient()
    with pytest.raises(FileExistsError):
        execute(client, tmp_path)
    assert client.uploads == []


def test_duplicate_sources_are_rejected_before_network(tmp_path):
    with pytest.raises(ValueError, match="duplicate PDF"):
        inspect_pdfs([PDFS[0], PDFS[0]], AGENT_ID)


def test_gold_json_is_never_accepted_as_source_pdf(tmp_path):
    false_pdf = tmp_path / "gold.pdf"
    false_pdf.write_text('{"documents": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="only source PDFs"):
        inspect_pdfs([false_pdf], AGENT_ID)


def test_invalid_agent_identifier_blocks_before_upload(tmp_path):
    with pytest.raises(ValueError, match="invalid agent ID"):
        inspect_pdfs(PDFS, "https://untrusted.example")


def test_invalid_poll_interval_blocks_before_upload(tmp_path):
    client = FakeClient()
    with pytest.raises(ValueError, match="polling"):
        execute(client, tmp_path / "run", poll_seconds=0)
    assert client.uploads == []


def test_poll_job_id_conflict_preserves_original_job_and_stops(tmp_path):
    client = FakeClient()
    original_retrieve = client.responses.retrieve

    def retrieve(job_id, **kwargs):
        reply = original_retrieve(job_id, **kwargs)
        reply.data["id"] = "job-WRONG"
        return reply

    client.responses.retrieve = retrieve
    meta = execute(client, tmp_path / "run")
    assert meta["status"] == "NEEDS_REVIEW"
    assert meta["job_id"] == "job-CONTRACT"
    assert len(client.submissions) == 1
    assert len(client.retrievals) == 1
    assert (tmp_path / "run/job-0001.json").is_file()


@pytest.mark.parametrize("change", [{"id": "job-WRONG"}, {"status": "in_progress"},
                                    {"error": {"message": "history failed"}}])
def test_conflicting_history_is_archived_without_claiming_success(tmp_path, change):
    client = FakeClient(statuses=["completed"])
    original_retrieve = client.responses.retrieve

    def retrieve(job_id, **kwargs):
        reply = original_retrieve(job_id, **kwargs)
        if kwargs["include"] == ["all"]:
            reply.data.update(change)
        return reply

    client.responses.retrieve = retrieve
    meta = execute(client, tmp_path / "run")
    assert meta["status"] == "NEEDS_REVIEW"
    assert meta["job_id"] == "job-CONTRACT"
    assert (tmp_path / "run/studio_all_steps.json").is_file()
    assert len(client.submissions) == 1


def test_input_order_is_preserved_in_uploaded_file_ids(tmp_path):
    client = FakeClient(statuses=["completed"])
    paths = [PDFS[2], PDFS[0], PDFS[1]]
    run_agent(client, paths, AGENT_ID, tmp_path / "run", case_id="SYNTHETIC-ORDER",
              config_version="mock", prompt_version="mock")
    assert [upload["bytes"] for upload in client.uploads] == [path.read_bytes() for path in paths]
    metadata = json.loads((tmp_path / "run/run_metadata.json").read_text())
    assert [row["filename"] for row in metadata["uploaded_files"]] == [p.name for p in paths]
