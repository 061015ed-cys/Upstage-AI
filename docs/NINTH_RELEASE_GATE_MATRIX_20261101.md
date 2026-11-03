# LeadTime Guardian — 9차 최종 Release Gate Matrix

Date: 2026-11-01. PR #10: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/10
Base PR #9 SHA b4c01ecddbd00bc33bca1ae8c1735ac768eea20f.
코드 검증 SHA 9e15fcfed44190e71863f7c5a8f1a73d26ed2d1a, CI #41304643210 SUCCESS: 전체 597 PASS(독립 QA 408 포함), Ruff PASS, Archived C001/Local Integration PASS_LOCAL; 전체 Release BLOCKED. 최종 문서 SHA의 CI는 별도 확인.

| Gate | 상태 | 원본 증거 / 범위 | BLOCKER 및 다음 담당/입력 |
|---|---|---|---|
| QA_CODE_GATE | PASS_AT_TESTED_SHA | GitHub QA pytest 408, Ruff | 최종 문서 SHA CI, 팀원1 |
| COMBINED_CODE_CI_GATE | PASS_AT_TESTED_SHA | Python 전체 pytest 597, Ruff, CI #41304112310 | 최종 HEAD CI, 팀원1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | 원본 Team2 V6 코드의 통합 및 보관 회귀. 운영 PR#12 원본 무수정 | 실제 NCik 원본 실행/sidecar, 팀원2 |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS_LOCAL | Studio Adapter/Strict JSON/V6/QA/Provenance 코드 연결 및 런타임 회귀 | 실제 원본 실행·승인, 팀원1+2 |
| OFFLINE_E2E_GATE | PASS_LOCAL | 기존 C001 Archived Replay 및 로컬 합성 음성 테스트 | 신규 Studio 실제 E2E 대체 불가 |
| XLSX_49_ANALYSIS_GATE | PASS_LOCAL_OOXML | 원본 SHA ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb, sharedStrings[49] 빈 문자열 22개 | 빈 문자열 최초 생성 Step 미확인, Studio |
| EXTRACT_SCHEMA_GATE | FAIL_STATIC_DRAFT_CONTRACT | 보존된 Draft v4의 null type/description 충돌, saved B0 v1과 동등성 미확인 | 실제 Config v1 및 nullable UI 확인, Studio |
| B0_SINGLE_JOB_GATE | SINGLE_JOB_REPORTED_XLSX | NCik 하나의 Job·Extract 세 행 보고 | Normalize Native 문서 3개·File IDs 실제 검증, Studio |
| STUDIO_DOCUMENT_GATE | NOT_VERIFIED | 신규 Native raw JSON 부재 | original NormalizeDocuments/Extract3/Merge raw+Step SHA, Studio |
| NORMALIZE_QA_INPUT_GATE | NOT_VERIFIED | 로컬 타입 보존·서로 다른 Job 차단 회귀 PASS | 실제 IndependentQA INPUT 원본과 Report, Studio |
| B0_E1_COMPARISON_GATE | BLOCKED | SHA/필드·타입 비교 계약 로컬 PASS, E1 Live 미회수 | E1 Job·Config Diff·동일 PDF SHA·Gold, Studio/팀원3 |
| STUDIO_PROVENANCE_GATE | BLOCKED | 로컬 원본 PDF SHA/Upload Receipt/Sidecar 검증기 보존 | 실제 PDF bytes, 운영·QA Receipt, Team2 Sidecar, Studio/팀원2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL | V6 기존 C001/C013/C017/C008 및 신규 NEW_LIVE 사전 차단 테스트 | 실제 NCik Python 실행 검증, 팀원2 |
| CROSS_AGENT_GATE | BLOCKED | HandOff/Provenance/QA 계약 로컬 회귀 PASS | 실제 QA Native·QA Report·실행 출처 결합, Studio/팀원1 |
| HUMAN_GOLD_GATE | BLOCKED | Human-reviewed Gold 누락 | PDF 페이지 근거와 검토자·SHA, 팀원3 |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | Studio 원본 전체 체인 미회수 | Stage Original→V6→QA→Cross Agent→PDF SHA, Studio/팀원1/2 |
| OVERALL_RELEASE_GATE | BLOCKED | GitHub CI 성공은 제출 승인 아님 | Live 증거·Gold·명시적 승인 및 공식 제출 규정 확인, 팀원1 |

## 9차 신규 보완: Release 증거 inventory

- 새로운 leadtime-release-evidence/v1 로컬 manifest는 운영 Native, Stage manifest/Extract3, QA Native/Report, Team2 Provenance, 양측 Upload Receipts, PDF 3개, Human Gold가 실제로 수신됐는지 확인.
- source file 실제 바이트 SHA 계산. 신고 SHA와 다르면 FAIL; 누락은 BLOCKED. 서로 다른 Case/Job/Config를 묶으면 FAIL. Python V6/QA/Live 자동 실행이나 PASS 승격 없음.
- 명시적으로 NEW_LIVE_STUDIO 모드인 Combined E2E는 required Stage/QA/Provenance/PDF 경로가 없을 때 python_safety_status NOT_RUN 및 BLOCKED 반환. 보관 오프라인 계산 경로는 기존처럼 가능.
- E1 미실행 또는 실제 Gold 미확보에서는 추출 품질 변화 수치 NOT_MEASURED, 일부 값 변경만으로 IMPROVED 판정 금지.

## 원본 보호와 다음 순서
1. Studio: B0 NCik Job/cfg_X2xXakDtmDTHh2RoqVysvL v1 보존. Extract3/Merge/Normalize/QA Input+Report raw와 Upload Receipts 회수. 유료 재실행 금지.
2. 팀원2: 원본 V6 엔진 무수정, actual Python output·sidecar와 PDF Source IDs/Hash 인계.
3. 팀원3: 원본 PDF 페이지 기반 Human-reviewed Gold.
4. 팀원1: stage/release manifest 작성 → qa_release_evidence_check.py → qa_stage_intake_check.py → Combined V6/QA/Provenance → 필요 시 E1 비교 → Gold → 별도 제출 승인.
5. 최종 GitHub SHA의 CI를 확인한 뒤에도 원본 실측/Gold 누락 시 Release BLOCKED 유지.
