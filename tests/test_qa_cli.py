"""Exercise the user-facing QA CLI as a subprocess, including exit codes."""
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from leadtime_guardian.engine import analyze_portfolio

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/qa_audit.py"


def run_cli(*args):
    process = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True, text=True, check=False, cwd=ROOT, timeout=20,
    )
    assert process.stderr == "", process.stderr
    return process.returncode, json.loads(process.stdout)


def prepared(tmp_path):
    case = json.loads((ROOT / "data/sample/portfolio_case.json").read_text(encoding="utf-8"))
    result = analyze_portfolio(deepcopy(case))
    assert result["status"] == "OK"
    source = tmp_path / "case.json"
    outcome = tmp_path / "analysis.json"
    source.write_text(json.dumps(case), encoding="utf-8")
    outcome.write_text(json.dumps(result), encoding="utf-8")
    return source, outcome, case, result


def test_cli_accepts_valid_case_with_matching_engine_output(tmp_path):
    source, outcome, _, _ = prepared(tmp_path)
    rc, payload = run_cli("--case", source, "--output", outcome)
    assert rc == 0
    assert payload == {"qa_status": "PASS", "issues": []}


def test_cli_rejects_wrong_cost_with_nonzero_exit(tmp_path):
    source, outcome, _, result = prepared(tmp_path)
    result["estimated_quote_cost_krw"] = "0"
    outcome.write_text(json.dumps(result), encoding="utf-8")
    rc, payload = run_cli("--case", source, "--output", outcome)
    assert rc == 1
    assert "COST_MISMATCH" in {item["issue_code"] for item in payload["issues"]}


def test_cli_rejects_unhashable_output_identifier_gracefully(tmp_path):
    source, outcome, _, result = prepared(tmp_path)
    result["impacted_orders"][0]["order_id"] = ["not-an-id"]
    outcome.write_text(json.dumps(result), encoding="utf-8")
    rc, payload = run_cli("--case", source, "--output", outcome)
    assert rc == 1
    assert "INVALID_ORDER_REFERENCE" in {item["issue_code"] for item in payload["issues"]}


def test_cli_rejects_duplicate_json_key_and_returns_json(tmp_path):
    source, _, _, _ = prepared(tmp_path)
    source.write_text('{"case_id":"a","case_id":"b"}', encoding="utf-8")
    rc, payload = run_cli("--case", source)
    assert rc == 1
    assert payload["issues"][0]["issue_code"] == "INPUT_ERROR"


def test_cli_rejects_missing_file_without_traceback(tmp_path):
    rc, payload = run_cli("--case", tmp_path / "missing.json")
    assert rc == 1
    assert payload["qa_status"] == "FAIL"


def test_cli_accepts_valid_case_in_input_only_mode(tmp_path):
    source, _, _, _ = prepared(tmp_path)
    rc, payload = run_cli("--case", source)
    assert rc == 0
    assert payload["qa_status"] == "PASS"
