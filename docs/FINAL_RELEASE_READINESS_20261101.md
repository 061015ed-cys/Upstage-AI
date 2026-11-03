# LeadTime Guardian — Final release readiness (Team 1, 2026-11-01)

**OVERALL RELEASE GATE: BLOCKED; merge/submit not authorized.** Code CI PASS at one QA SHA does not imply Studio or combined branches are verified.

## Gate matrix

| Gate | Evidence available | Current assessment |
| --- | --- | --- |
| Local Code/Contract | QA unit tests, Ruff and offline replay, full QA tree CI | PASS at specific CI SHA |
| Parse/Classify/Extract/Merge/Normalize | Operational Studio v5 draft; V4 archived Native C001 | VERIFIED_ARCHIVED / live v5 NOT_VERIFIED |
| Studio Document QA | QA copy user-observed C001 NOT_VERIFIED, PARTIAL; raw QA report not saved in PR | BLOCKED |
| Python Safety | PR#12 engine/Adapter CI and previous archived C001 replay | PASS on separate PR#12 code only; live integrated NOT_VERIFIED |
| Cross-Agent | Original SHA/IDs/adapter code implemented; synthetic local QA test | BLOCKED pending raw QA Job file |
| Offline E2E | `tests/test_qa_full_offline_e2e.py` Python replay + synthetic QA+Gate | LOCAL CODE PASS, release BLOCKED |
| Actual Studio E2E | Latest two Studio jobs + PDF receipts + raw report + Python run | NOT_RUN / BLOCKED |
| Human Gold | 20-case DRAFT documents, no reviewer-verified record | BLOCKED |
| Combined PR#12+QA CI | No integrated single SHA | NOT_RUN |
| Release Approval | Owner review/demo/submission evidence | BLOCKED |

## G0-G9 project-level checks

- **G0:** official current LMS, API/Studio/n8n requirements, submission format NOT_VERIFIED.
- **G1:** saved Studio/QA Config and source PDF SHA bound to current Job/Step BLOCKED.
- **G2:** new operating C001 Studio → Python actual Job NOT_VERIFIED; archived replay exists.
- **G3:** C013/C017/C008 actual fail-closed jobs NOT_VERIFIED.
- **G4:** human-verified Gold, exclusion policy and source page evidence BLOCKED.
- **G5:** independent QA Sandbox source Native/report and explicit manifest BLOCKED.
- **G6:** combined final GitHub SHA/full pytest/Ruff/QA/E2E CI NOT_RUN, separate branch CI PASS.
- **G7:** actual demo and troubleshooting script with reproducible live evidence NOT_VERIFIED.
- **G8:** design/architecture, dataset limitations, license/privacy and submission package PARTIAL.
- **G9:** final accountable human reviewer and submission authorization NOT_GRANTED.

## Evidence tiers

- E0: draft config, planning text, synthetic Gold / expected only (not live).
- E1: local unit/synthetic fixture regression.
- E2: archived genuine operation V4 C001/explicitly offline Replay.
- E3: downloaded original Studio QA copy Job/step/report bytes matched to source PDFs and saved Config, independently hashed. **NOT_VERIFIED**.
- E4: latest Team2 operational Job and QA copy matched to same PDF original SHA plus current Python QA, person-reviewed Gold and final integrated CI. **BLOCKED**.

## High-priority tasks

1. Studio AI: recover unchanged QA copy Normalize output + IndependentQA input/report and Job/Step evidence. Investigate `NORMALIZED_OUTPUT_NOT_PROVIDED`, source provenance null and Excel 49 in actual Step bytes. Distinguish v1 from any v2+ Config.
2. Team2: provide original operational v5 current Job, saved Config, exact PDF receipt and `studio-provenance/1` + Python output/Git SHA. Review v5 Extract nullable schema mismatch and full validation entrypoint.
3. Team3: provide human-reviewed Gold records with version, source PDF per-field/page evidence and explicitly excluded fields.
4. Team1: only after original files arrive, run SHA/ID comparisons, local artifact mapping, source-PDF linkage, merged tree CI and actual controlled Studio E2E.
5. Explicit owner sign-off; no force push, branch merge, paid API, procurement, emails or external submission in this work.

**Release/merge authorized: FALSE.**
