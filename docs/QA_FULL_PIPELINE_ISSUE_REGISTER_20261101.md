# QA full-pipeline issue register — 2026-11-01

| ID | Severity | Finding | Evidence | QA-owner action | Current state |
| --- | --- | --- | --- | --- | --- |
| QA-101 | P1 | Native metadata.source_files absent did not fail closed in legacy Cross-Agent path | `qa/cross_agent.py` previous condition, negative synthetic test | Explicit reject missing/empty original source IDs | FIXED_CODE_TESTED |
| QA-102 | P1 | PDF receipt local verification could follow symbolic link outside trust root | `qa/provenance_link.py`, symlink regression | Reject symlink/resolved path escapes | FIXED_CODE_TESTED |
| QA-103 | P2 | Excel formula cached 49 indistinguishable from literal value | `scripts/qa_excel_49_audit.py` and OOXML synthetic test | `FORMULA_CACHED_49`, formula expression preserved | FIXED_CODE_TESTED |
| QA-104 | P1 | Extract null instructions vs primitive-only v5 draft schema | Original PR#12 `configs/studio_native/config_v5.user-supplied.export.json`; QA static auditor/test | QA detection implemented; Studio owner fixes config | OWNER_BLOCKED |
| QA-105 | P1 | QA copy C001 IndependentQA raw input/Normalize handoff unproven | user-observed `NORMALIZED_OUTPUT_NOT_PROVIDED`, Step source absent | `input_delivery` distinguishes UNKNOWN/local match; Studio raw input still needed | EXTERNAL_BLOCKED |
| QA-106 | P1 | QA copy C001 report provenance null and partial field checks | reported v1 C001 Job, raw report not in GitHub | Adapter fail closed; require raw report bytes/QA job | EXTERNAL_BLOCKED |
| QA-107 | P1 | Combined PR#12+QA tree not tested | separate repo/branch topology and different engine blob SHAs | integration plan+validation required | EXTERNAL_BLOCKED |
| QA-108 | P1 | Human Gold and measured extraction accuracy missing | 20 case DRAFT Gold files, no independent source review | TEAM3 source review request | EXTERNAL_BLOCKED |
| QA-109 | P2 | Excel 49 origin not established by raw Step chain | reported 22 cells, raw Extract/Merge/Normalize not supplied | XLSX audit utility ready, raw Steps pending | EXTERNAL_BLOCKED |
| QA-110 | P1 | Direct untrusted engine calls could bypass separate Studio `validate_documents` boundary | code boundary separation in team2 PR#12 | Request team2 audit all callers / contract enforcement | INTERFACE_REVIEW |
| QA-111 | P1 | Live E2E/release authorization absent | local Gate BLOCKED and no source+gold+cross-agent matching Job IDs/PDF hashes | G0-G9 and final integrated CI pending | EXTERNAL_BLOCKED |
| QA-112 | P2 | Experiment variants B0/E1/E2/E3/E4 have no matching measured saved-config/Job dataset | user experiment names, no raw matched evidence | preserve NOT_VERIFIED; require official version+input+Gold | EXTERNAL_BLOCKED |

All FIXED_CODE_TESTED items refer to **specific GitHub Actions code SHA**; Studio source and release status remain BLOCKED.
