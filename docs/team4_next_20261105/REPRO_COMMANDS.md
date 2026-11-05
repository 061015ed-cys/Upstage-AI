# Reproduction commands

From the Team 4 checkout, create the validation environment once:

```powershell
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements-validation.txt
$env:PYTHONUTF8 = '1'
```

Current missing-input result, without original bytes:

```powershell
.venv/Scripts/python.exe -m qa.intake_preflight --manifest docs/team4_next_20261105/intake_manifest.json
```

For private originals, create the manifest described in `INTAKE_GUIDE.md` within the evidence directory. Verify each source SHA from its actual bytes and keep the independently reviewed trust manifest outside that directory. Then run:

```powershell
.venv/Scripts/python.exe -m qa.intake_preflight --manifest C:/private/evidence/intake.json --trusted-manifest C:/private/review/trust.json
.venv/Scripts/python.exe scripts/qa_release_evidence_check.py --manifest C:/private/evidence/release_evidence.json
.venv/Scripts/python.exe scripts/qa_stage_intake_check.py --manifest C:/private/evidence/stage_manifest.json
```

After those pass their own gates, use the exact identity and actual file paths in `docs/NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md` for `scripts/qa_combined_e2e_check.py`. Only after the official output keys, units, and normalization rule are confirmed and the same-case originals pass the required gates, run:

```powershell
.venv/Scripts/python.exe -m qa.gold_metrics --gold C:/private/evidence/frozen_gold.json --prediction C:/private/evidence/v6_prediction.json --binding C:/private/evidence/native_binding.json --out C:/private/results/official_gold_eval.json
```

The output path must be new. Record both numerator and denominator, excluded fields, source SHA and exact command. A locally measured result is not a release decision. For a designated submission candidate and its private manifest:

```powershell
.venv/Scripts/python.exe -m qa.submission_preflight --candidate C:/private/submission/candidate.zip --manifest C:/private/submission/manifest.json
```

The latter returns `PRECHECK_ONLY` even when all integrity checks pass. To repeat the targeted regression from this branch:

```powershell
.venv/Scripts/python.exe -m pytest tests/qa/test_gold_metrics.py tests/qa/test_next_preflight.py -q
.venv/Scripts/python.exe -m ruff check qa/gold_metrics.py qa/intake_preflight.py qa/submission_preflight.py tests/qa/test_gold_metrics.py tests/qa/test_next_preflight.py
```
