# C001 integration checkpoint - 2026-10-30 KST

## Observed state

Latest attempt: the user supplied the workflow's direct URL; the connected in-app
browser returned Studio's `Error code: 404`. The optional API transport is now
implemented with fake-client tests; see [Agents runner](AGENTS_API_RUNNER.md).
The environment has no API key or optional SDK, so actual Studio/API executions
remain 0. Earlier observations below are retained as history.

- Source: PR #11, commit `540f9f3b40269b3e668fe95cfee4ee09f30221c2`.
- The existing engine and adapter are reused unchanged.
- Chrome exposes a native Studio window, but there is no connected Chrome tab provider.
- A controllable in-app browser reached Studio. Its separate session was logged out.
- Clicking Studio login redirected to Google Accounts. Automatic approval review denied access to that origin. User authentication is pending; do not automate or inspect Google credentials.
- No native workflow node configuration, execution, or prediction has been verified yet.

## Files and provenance

`scripts/generate_c001.py` generates three bilingual synthetic, one-page PDFs from the
repository sample. The case ID, document IDs and receipt R1 are visibly printed.
Use `--font` for a Korean TTF on non-Windows systems.

`trusted_base_case.json` contains trusted inventory/orders/original inbound facts,
an empty documents list and no prefabricated replacement quotes. Its current ETA
starts at the original date. The revised date and quote must come from Studio.

`extraction_gold.DRAFT.json` is generator-authored, not human reviewed, and never a
Studio prediction. `expected_calculation.json` is only an expected fixture.

`configs/studio_prompt_spec.v1.json` is a design specification, **not a native
Studio configuration export**. The current screen must be inspected before applying it.

## Run locally

```powershell
python -m pip install -r requirements-integration.txt
python scripts/generate_c001.py --output data/cases/SYN-C001
pytest -q
ruff check .
```

After obtaining a real output whose final JSON contains `documents`, use:

```powershell
python scripts/analyze_studio_export.py --export ACTUAL_STUDIO_EXPORT.json --base data/cases/SYN-C001/trusted_base_case.json --output data/results/studio_runs/RUN_ID --run-id RUN_ID --config-version ACTUAL_CONFIG_VERSION --prompt-version c001-v1
```

The runner creates a new output directory, archives the source bytes and SHA-256,
and records the run ID and configuration/prompt versions. It supports the official
Agents API's single-final-message `output_text` envelope as a **contract test**.
Native UI node exports may have another format; unsupported or ambiguous formats
are rejected until an actual export is inspected. API transport is implemented
separately, but no successful live execution is claimed.
The runner cannot authenticate the provenance of an arbitrary local JSON file.

The boundary blocks schema errors, PO/product mismatch, unresolvable receipts,
conflicting/duplicate notices, changed PO quantities, unsupported units/currency,
missing/invalid quote facts, and quote conflicts with existing trusted data.
Quotation fields stay nested under `quote`. Supplier risk `UNKNOWN` is policy
metadata, not a PDF inference. This strict path targets C001: aggregate PO rows
covering multiple partial receipts need an observed, explicit allocation contract.
Existing partial-receipt engine tests remain separate from this importer.

## C001 expected arithmetic (not measured Studio output)

- Original receipt November 3 precedes customer due date November 5: shortage 0.
- Revised receipt November 8 misses the due date: 100 required - 40 stock = 60.
- Additional shortage: 60 - 0 = 60.
- Replacement quote: 60 x KRW 1,000 + one KRW 500 shipping charge = KRW 60,500.

`evidence_verified_against_pdf` stays false. Schema/identifier agreement and local
text checks do not prove that a live prediction is grounded in the PDF.
Human-reviewed gold and actual prediction accuracy remain pending.

## Local validation observed

- Baseline before changes: 20 pytest tests passed, Ruff passed.
- With importer regressions: 48 pytest tests passed, Ruff passed, Python 3.13.9.
- The workspace used `PYTHONPATH=src` rather than modifying the user's Python install.
- One test attempt had 47 passes and one setup error because the Windows temporary
  folder could not be created. Rerunning with a new `--basetemp` under `work/` passed.
- The three PDFs were rendered and visually inspected; each is one page and all
  required source tokens and manifest hashes matched. This is local asset QA.
- Offline repository sample computed 0 / 60 / 60 and KRW 60,500.00.
- Actual Studio runs: 0. Actual Studio prediction accuracy: not measured.
- First GitHub Python 3.11 CI attempt failed at Ruff 0.17.3 on an unused lint
  suppression and the older `timezone.utc` spelling; pytest was skipped on that
  attempt. Removed the suppression and adopted `datetime.UTC`; rerun is required.

## Official references checked

- [Studio nodes](https://console.upstage.ai/ko/docs/studio/key-features): Classify-only
  treats a case as one document; split-then-classify supports multi-file cases, and
  Merge rejoins split branches before cross-document checks.
- [Agents API](https://console.upstage.ai/docs/agents): multiple `input_file` objects
  can be supplied in one job; the completed response can expose final output text.

These are documented capabilities, not proof that this workflow has been configured.
