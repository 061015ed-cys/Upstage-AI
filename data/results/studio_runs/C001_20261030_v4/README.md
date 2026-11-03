# C001 actual Studio Web run - 2026-10-30 KST

- Agent `agt_bXRXFSAgFmBayPjZF7VqRQ`, saved version **4**, config `cfg_SZi6qfyZ6XFoNszpXQK5xQ`.
- Job **`job_gPmEYKzuJdBA6BmKhVnujs`**, final step `63f6a860-7c86-5036-b32d-6eae38ca7677`.
- `parse.json`, `classify.json`, `instruct_original.json` and `extractions_native.zip` are unchanged native browser downloads. `studio_result.jpg` shows the completed run.
- The native extraction ZIP names its directory `gold/`. This is Studio's export packaging name, **not independently reviewed gold**. Files `extract-03/04/05.json` are the downloaded PO/notice/quote predictions, copied from that ZIP without edits. `native_export_manifest.yaml` came from that same ZIP.
- `analysis/studio_original.json` is an identical copy of the Instruct download. `analysis/normalized_documents.json` contains only its parsed content, without correcting facts. The sole integration change is recognizing the observed `content + metadata` envelope.
- `before_adapter/` records the real format-rejection result before that support was added. `analysis/analysis.json` is the successful rerun of Python analysis, not another Studio inference.
- Actual path: original C001 PDFs -> Studio Parse -> file-boundary Classify -> type-specific Extract -> Merge -> Instruct -> Python strict matching/validation -> existing engine.
- Actual computed result: baseline 0, revised 60, additional 60; KRW 60,500.00. No procurement or email action.
- All evidence arrays are empty. Source-PDF grounding and human-reviewed gold remain unverified, and no extraction accuracy percentage is claimed.
- SDK loopback tests are separate simulated transports; the actual C001 run used Studio Web, not the Agents API.
