# LeadTime Guardian — 10차 최종 Gate Matrix (GitHub/Studio/외부 분리)

2026-11-01 KST. PR #11: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/11
부모 PR #10 verified HEAD `74f8989a494481a71116f6ca3641d1bf01a3cdbe`.
10차 코드 검증 SHA `006805802e563c80dbbda8c466dc2e305ba3f792` CI run #41306728237 SUCCESS, Python 전체 600 PASS(독립 QA 411 포함), Ruff 2종 PASS, Archived C001/Local Integration local PASS; `overall_status=BLOCKED`.
최종 문서 SHA의 CI가 확인되면 최종 HEAD를 PR#11 상태와 사용자 최종 답변에서 기록한다.

## A. GitHub 단독 범위

| Gate | Status | Evidence / verification scope | Owner/next action |
|---|---|---|---|
| QA_CODE_GATE | PASS_AT_TESTED_SHA | 411 independent QA tests, Ruff QA pass | 팀원1. 최종 HEAD CI 확인 |
| TEAM2_ENGINE_GATE_LOCAL | PASS_LOCAL | Team2 원본 Python Safety V6 동일 소스 계약/Archived 회귀. 원본 PR #12 SHA e9b9992b593a42d427ff1bbadeb9a9866ca593bd | 팀원1+2. 최종 SHA blob 확인 |
| COMBINED_CODE_CI_GATE | PASS_AT_TESTED_SHA | 600 whole Python PASS, whole Ruff PASS, CI run #41306728237 | 팀원1. 마지막 문서 CI 확인 |
| OFFLINE_E2E_GATE | PASS_LOCAL | Archived C001 replay 및 local_checks_passed=true | 팀원1. 실제 Studio Live와 별개 |
| GITHUB_CODE_FREEZE_GATE | PENDING_FINAL_HEAD_CI | 중간 코드 HEAD에서 신규 재현 HIGH/CRITICAL 없음; Reports rollback·path alias 실패 차단 | 팀원1. 최종 HEAD CI SUCCESS 시 PASS_LOCAL_CANDIDATE |
| GITHUB_OWNED_READINESS | CONDITIONAL_100_OF_100 | 10개 체크리스트×10점, 1~8 코드 검증 통과. 9~10은 마지막 문서 포함 SHA의 CI SUCCESS와 문서 보존 필요 | 팀원1. final HEAD CI 확인 후 100/100 결정 |

## B. Studio 실제 데이터

| Gate | Status | Evidence / verification scope | Owner/next action |
|---|---|---|---|
| B0_SINGLE_JOB_GATE | SINGLE_JOB_REPORTED_XLSX | job_NCik8shwrgM93PDnNNYukT + cfg_X2xXakDtmDTHh2RoqVysvL v1 XLSX report | Studio. 실제 Native 3문서와 File IDs 확인 |
| XLSX_49_ANALYSIS_GATE | PASS_LOCAL_OOXML | 원본 SHA ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb, 22 sharedStrings[49] EMPTY_STRING | Studio. 최초 빈 문자열 생성 인접 Step 실제 조회 |
| EXTRACT_SCHEMA_GATE | FAIL_STATIC_DRAFT_CONTRACT | 보존 Draft v4 타입/nullable 설명 충돌; 실제 저장 B0 v1의 동일성은 아직 미확인 | Studio. Saved Config v1 원본 조회 |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | 실제 NCik Extract 3건/Merge/Normalize Native 원본 미제공 | Studio. 원본 JSON bytes/sha256/Step ID |
| NORMALIZE_QA_INPUT_GATE | NOT_VERIFIED | 로컬 타입 보존·SHA 비교 CI PASS, 실제 QA INPUT·Report 원본 없음 | Studio. 실제 Step Input+Report/Job 연결 |
| STUDIO_PROVENANCE_GATE | BLOCKED | PDF 원본/운영 및 QA Upload Receipt/각 File ID 미제공 | Studio/팀원2. 실제 바이트+Receipt |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | Provider Native 원본 전체 체인/Gold 없음. CI가 Studio Job을 실행한 것은 아님 | Studio. 원본 회수 후 실측 E2E |

## C. 외부 팀원·전체 프로젝트

| Gate | Status | Evidence / verification scope | Owner/next action |
|---|---|---|---|
| TEAM2_LIVE_PROVENANCE_GATE | BLOCKED | Team2 V6 엔진 PASS_LOCAL, 실측 NCik 실행 sidecar 미제공 | 윤현준. Native SHA, Python V6 결과, provenance |
| CROSS_AGENT_LIVE_GATE | BLOCKED | Cross-Agent 코드·로컬 회귀 PASS, 실제 QA Sandbox Native와 Report/Doc handoff 미제공 | Studio/구도훈. 실제 Job/Case/PDF source 연결 |
| HUMAN_GOLD_GATE | BLOCKED | Human-reviewed PDF 페이지 근거/검수자/버전/sha256 없음 | 김민주. 서명된/검토된 Gold |
| B0_E1_COMPARISON_GATE | BLOCKED_NOT_MEASURED | 로컬 B0/E1 Normalize SHA/type diff 기능 존재; 실제 E1 Job 및 Human Gold 없음 | Studio/김민주. E1 Job/Config Diff/동일 original PDFs |
| OVERALL_RELEASE_GATE | BLOCKED | GitHub 코드 동결은 제품 제출 승인 아님 | 구도훈. 실측 E2E/Gold/정식 공고·승인 이후 판단 |

## Status 및 provenance 제한

- `PASS_LOCAL`은 오프라인·보관·합성 근거이며, `PROVIDER_EXECUTION_AUTHENTICATED`를 의미하지 않음.
- Source 파일의 로컬 SHA 검사 성공은 원본 Upstage provider의 Upload Receipt와의 연계를 자동 입증하지 않음.
- 동일 Case라도 운영 Job과 QA Sandbox Job은 다를 수 있지만, 실제 PDF/문서 IDs 및 Source linkage 없이 결합해서는 안 됨.
- B0 XLSX 22개의 `49`는 sharedString 참조값이며 실제 literal 49 숫자/문자 0개. 최초 생성 원인 UNKNOWN.
- E1이 없거나 검토 Gold가 없으면 개선/악화 품질 수치를 주장하지 않고 `NOT_MEASURED`.
- 원본 PDF·XLSX·Native·Gold 업로드/수정, 신규 Studio 유료 Job 실행, 자동 PR Merge/Force Push 전부 금지.

## 다음 실행

외부 원본을 확보한 뒤 `docs/NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md` 순서로 Release Inventory → Stage Intake → Strict JSON/Operational Native → Python Safety V6 → Independent QA → Cross-Agent·PDF Provenance → B0/E1(실행된 경우) → Human Gold → Release Gate를 검증한다.

GitHub 코드 Freeze 후보 여부 및 100/100은 **최종 HEAD SHA의 CI가 SUCCESS라는 최종 확인 근거가 있을 때에만** 판정한다.
