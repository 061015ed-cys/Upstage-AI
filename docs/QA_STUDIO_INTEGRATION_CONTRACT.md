# LeadTime Guardian — Studio ↔ Python QA integration contract

**Contract type:** independent handoff adapter, version `leadtime-cross-agent/v1`  
**Status:** GitHub-side implementation and tests available; **latest QA Sandbox schema/config/export not independently observed** as of 2026-10-31.

## 1. Observed implementations vs external unknowns

| Component | Verified source | Meaning |
| --- | --- | --- |
| Operational Studio workflow | Archived `configs/studio_native/config_v4.export.json` | Operational Agent `agt_bXRXFSAgFmBayPjZF7VqRQ`, Config `cfg_SZi6qfyZ6XFoNszpXQK5xQ`, v4; **read only** |
| Archived C001 Instruct output | `data/results/studio_runs/C001_20261030_v4/analysis/studio_original.json` | `content` JSON string with `documents` and `metadata.job_execution_id`, `step_run_id`, `source_files`, `merge` |
| Python normalizer/Adapter | `studio_integration.py`, `studio_adapter.py` | `documents_from_export` → `validate_documents` → `apply_studio_extractions` |
| Python business calculation | `engine.py` | Deterministic quantities, deadline allocation, price and shipping; never external procurement |
| Independent Python QA | `qa/studio_contract.py`, `qa/portfolio.py`, `qa/replay.py`, `qa/gate.py` | Archived Native consistency, actual calculation invariants, replay and conservative merge gate |
| Separate Studio QA Sandbox | User-provided `agt_GhP9GywhbcDWquFqWTsmtq` | Config version `4` reported, but latest Config ID, Node schema, native JSON and new run IDs **NOT_VERIFIED** |

**Never conflate the operational v4 Config ID with the QA Sandbox Config ID.**

There are two distinct flows:

```text
Operational: PDF → Parse → Classify → Extract → Merge → NormalizeDocuments
             → Python Adapter → Engine → Independent Python QA

Separate QA Sandbox: PDF → Parse/Classify/Extract/Merge/NormalizeDocuments
                     → IndependentQA (Studio evaluation)
                     → saved Sandbox QA output
                     → explicit versioned QA handoff adapter
                     → Python cross-agent contract checker (read only)
```

**The independent Studio QA Node is not assumed to call the Python engine.**
A Studio document QA `PASS` does not prove that deterministic Python safety/engine verification happened.

## 2. Exact observed operational Native structure

Top level has `content: string` (UTF-8 JSON document wrapper) and `metadata: object`. The nested `content` contains `{"documents": [...]}`.

Metadata fields present in the archived operational C001 include `job_execution_id`, `step_run_id`, `occurrence_id`, `source_files`, `merge.items` with document types and file references. For the observed operational C001 archive:

- Job: `job_gPmEYKzuJdBA6BmKhVnujs` (**historical; not a new QA Sandbox run**)
- Config: `cfg_SZi6qfyZ6XFoNszpXQK5xQ` (**operational only**)
- Agent: `agt_bXRXFSAgFmBayPjZF7VqRQ` (**operational only**)

Existing Python documents schema: `configs/schemas/document_extraction.schema.json`.
Do not apply the unrelated legacy `analysis_output.schema.json` (older single-risk output) as the latest portfolio result contract.

## 3. Cross-agent handoff: a separate adapter protocol, NOT the Sandbox output schema

`src/leadtime_guardian/qa/cross_agent.py` expects a manifest with these required fields:

| Section | Required fields |
| --- | --- |
| Top level | `protocol_version="leadtime-cross-agent/v1"`, `producer="UPSTAGE_QA_SANDBOX"` |
| `studio` | `agent_id`, `config_id` (`cfg_...`), positive integer `config_version`, `job_id` (`job_...`), `step_run_id`, `execution_kind`, non-empty `input_file_ids`, `native_sha256`, `qa_report_sha256` |
| `verdict` | `document_qa_status`, `python_qa_status`, `issues: [{code,scope,severity}]` |
| `github` | `repository`, exact 40-character `head_sha`, `contract_version` |
| Supplied files | Native Instruct JSON bytes and QA report JSON bytes. SHA-256 values refer to these **exact bytes** |

A trusted adapter must create this manifest from a **real export**, recording actual field mapping and what has not been verified. The Studio Sandbox schema is not automatically presumed to match this manifest; mapping must be reviewed.

Supported `execution_kind`: `NEW_LIVE_STUDIO`, `ARCHIVED_STUDIO`, `ARCHIVED_REPLAY`, `SDK_HTTP_MOCK`, `FAKE_CLIENT_TEST`, `SYNTHETIC_FIXTURE`.

The hard-coded historical operational C001 Job ID is blocked from being relabelled as `NEW_LIVE_STUDIO`. Native and QA report digests are compared to actual file bytes. Native job/step and source file IDs are compared to manifest values.

**These checks prove an internal contract only, not that a cloud job is independently authenticated or that extracted facts match the PDF.**

## 4. Status domains and non-equivalence

| Studio document QA | Python QA | Cross-agent response | Meaning |
| --- | --- | --- | --- |
| PASS | NOT_VERIFIED / NOT_RUN / BLOCKED | BLOCKED | Document QA may pass while independent Python is unverified |
| FAIL / NEEDS_REVIEW | PASS | FAIL | Document problem remains; Python success cannot override |
| PASS | FAIL | FAIL | Deterministic Python problem blocks integration |
| PASS | PASS | NOT_VERIFIED if export/report unavailable | Self-reported PASS is not enough |
| PASS | PASS | PASS only on matching manifest + Native + report bytes for claimed new run | **Structure only**, not a live authenticity or release claim |
| N/A | N/A | FAIL on Job/Config/commit mismatch | Invalid or conflicting handoff |

If the Studio side emits issue `EXTERNAL_SAFETY_NOT_VERIFIED` scoped to `python`, this is **not** a document QA failure by itself, and must not be converted into `document_qa_status=FAIL`.

`release_or_merge_authorized` always remains `false` in this independent checker; a separate actual integration gate requires current CI, live evidence and human Gold.

## 5. Operational usage after real Studio artifacts are delivered

```bash
python scripts/qa_cross_agent_check.py \
  --manifest path/to/reviewed-handoff.json \
  --native path/to/native-instruct-export.json \
  --qa-report path/to/qa-report.json \
  --expected-config-id cfg_ACTUAL_SANDBOX_CONFIG \
  --expected-github-sha ACTUAL_40_CHARACTER_SHA \
  --require-contract

python scripts/qa_gate_check.py --root . \
  --studio-handoff path/to/reviewed-handoff.json \
  --studio-native path/to/native-instruct-export.json \
  --studio-qa-report path/to/qa-report.json \
  --expected-config-id cfg_ACTUAL_SANDBOX_CONFIG \
  --expected-github-sha ACTUAL_40_CHARACTER_SHA
```

In the second command, good handoff data still leaves `overall_status=BLOCKED` until external release requirements are independently met.

Exit codes: `qa_cross_agent_check.py` 0 if no structural FAIL (or if PASS under `--require-contract`), 1 for FAIL, and 2 when `--require-contract` is set but evidence remains BLOCKED/NOT_VERIFIED. In the integration gate, 0 means local checks passed, 1 means local check failed and 2 means unresolved overall release requirements under `--require-release`.

Do not pass a GitHub test fixture, mocked job or old operational C001 job as if it were a fresh Sandbox run. Never infer a Sandbox Config ID from `configVer=4` in its URL.
