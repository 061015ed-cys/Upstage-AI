# LeadTime Guardian — ChatGPT ↔ Upstage Studio cross-agent handoff

**GitHub QA code owns:** `src/leadtime_guardian/qa/`, `tests/test_qa_*.py`, QA scripts, QA CI, QA docs.  
**Studio QA Sandbox owns:** Studio `IndependentQA` Node, QA Instruct settings, QA-output schema, Native Config Export and actual Studio jobs.  
**Protected collaborators:** team 2 engine + adapter; team 3 source PDFs + Gold.  
**Operational Studio:** `agt_bXRXFSAgFmBayPjZF7VqRQ` read-only; not the QA Sandbox.

## 1. Verifiable latest GitHub checkpoint

Copy: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy  
Branch: `feat/qa-source-restore-20261031`  
Draft PR #2: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/2

A previous verified GitHub code checkpoint was `7b9eb232aa8b4e21d345a585bdc731bb58cee773` with 263 full and 183 independent QA tests passing. **Fetch the actual live HEAD and Actions after every new commit; do not reuse prior test counts as fresh evidence.**

## 2. QA Sandbox status (reported, NOT independently verified)

- Reported Agent: `agt_GhP9GywhbcDWquFqWTsmtq`
- User link: https://studio.upstage.ai/agents/agt_GhP9GywhbcDWquFqWTsmtq?configVer=4
- Reported v4, NormalizeDocuments → IndependentQA, C001/C013 input files and saved workflow
- **Actual latest Config ID:** UNKNOWN
- **Actual latest Config Version:** NOT_VERIFIED (URL v4 does not prove latest)
- **Actual current QA Node schema:** NOT_VERIFIED
- **Latest Sandbox Job IDs, Step Run IDs:** NOT_VERIFIED
- **Actual Sandbox Native/QA exports:** NOT_AVAILABLE in connected GitHub copy
- **New C013 Studio execution:** NOT_VERIFIED, do not treat prior planned/run claims as fact

The connected tools available to this QA session cannot authenticate into Studio; the private QA agent URL is not readable through general page retrieval. **Do not edit or redeploy either Studio workflow using GitHub-only access.**

## 3. What the Studio AI should export for an independently testable handoff

1. QA Sandbox Agent ID, latest Config ID and Config Version; exact QA Node version/settings; export timestamp.
2. C001/C013 (or newer) **actual** Job ID, Step Run ID, run date/time, source File IDs and file-name mapping.
3. Native output **unmodified byte-for-byte**, plus an exported Studio QA report **unmodified byte-for-byte**; provide SHA-256 of each.
4. Document QA status and exact Issue codes/severities and source scope (document vs python vs provenance).
5. Explicit Python verification status; if Python engine was not executed, mark NOT_VERIFIED. Do not infer PASS from Studio QA alone.
6. Distinguish newly run Studio inference, archived run, local replay, mocks and draft/human-verified Gold.
7. Independent schema-to-handoff adapter mapping; do not silently rename Studio node fields as though they are Python engine fields.
8. Actual effective GitHub QA SHA used for compatibility checks.

Do not invent missing values or silently reuse historical C001 operational Job `job_gPmEYKzuJdBA6BmKhVnujs` as a new Sandbox job.

## 4. Versioned manifest schema: HANDOFF ONLY (not Studio-native)

Here is an example with **placeholders**; it is a format template and NOT a real Studio execution:

```json
{
  "protocol_version": "leadtime-cross-agent/v1",
  "producer": "UPSTAGE_QA_SANDBOX",
  "studio": {
    "agent_id": "agt_GhP9GywhbcDWquFqWTsmtq",
    "config_id": "cfg_REPLACE_WITH_ACTUAL_SANDBOX_ID",
    "config_version": 4,
    "job_id": "job_REPLACE_WITH_ACTUAL_NEW_JOB",
    "step_run_id": "REPLACE_WITH_ACTUAL_STEP_ID",
    "execution_kind": "NEW_LIVE_STUDIO",
    "input_file_ids": ["file_REPLACE_WITH_ACTUAL_FILE_ID"],
    "native_sha256": "REPLACE_WITH_ACTUAL_64_CHARACTER_SHA256",
    "qa_report_sha256": "REPLACE_WITH_ACTUAL_64_CHARACTER_SHA256"
  },
  "verdict": {
    "document_qa_status": "PASS",
    "python_qa_status": "NOT_VERIFIED",
    "issues": [
      {
        "code": "EXTERNAL_SAFETY_NOT_VERIFIED",
        "scope": "python",
        "severity": "INFO"
      }
    ]
  },
  "github": {
    "repository": "dohun3540-crypto/leadtime-guardian-agent.copy",
    "head_sha": "REPLACE_WITH_ACTUAL_40_CHARACTER_SHA",
    "contract_version": "leadtime-cross-agent/v1"
  }
}
```

All placeholders **must be replaced with actual verified values** before validation. A link or text summary alone is not a Native Export.

## 5. Strict ownership / collision procedures

- **File collision:** never overwrite the other person's branch or source files; isolate changes in QA branch and compare Git SHAs.
- **Contract collision:** compare *real* source JSON field names, nullability and enum meanings; create mapping adapter or explicit review issue. Never change Studio live Node or Python engine to satisfy unobserved output.
- **Meaning collision:** `document PASS` and `python NOT_VERIFIED` must lead to overall `BLOCKED`, not automatic `FAIL` document QA or `PASS` release.
- **Version collision:** if observed Config ID or Git commit differs from expected, fail the handoff integrity check. A different version is not automatically incompatible until the actual schema is compared.
- **Evidence collision:** a matching content hash prevents accidental mixing, but does not independently authenticate Studio cloud run or validate extracted facts against PDF.
- **Gold separation:** DRAFT Gold cannot prove extraction accuracy. Neither side may promote it to HUMAN_VERIFIED without independent manual PDF review.

## 6. Cross-agent tool commands

Use `scripts/qa_cross_agent_check.py` on the actual manifest + unmodified Native bytes + QA report bytes. To include this in the conservative release gate, pass `--studio-handoff`, `--studio-native`, `--studio-qa-report` to `scripts/qa_gate_check.py`.

See `docs/QA_STUDIO_INTEGRATION_CONTRACT.md` for exact commands and exit-code semantics.

Until actual Sandbox exports are present, do not claim the two AI agents have communicated, auto-synchronized or achieved live end-to-end integration.

## 7. Next session handoff

Record the last *observed remote HEAD*, matching Python CI and Independent QA CI links, source PDF hashes, Studio latest IDs, status of Config/Job exports, collision findings and unresolved team 2/3 dependencies in `docs/QA_CONTINUATION_HANDOFF.md`. Keep Draft PR #2 open.
