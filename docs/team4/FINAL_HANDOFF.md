# 팀원 4 최종 통합 검수 및 제출 준비 인계

작성: 2026-11-03 KST. 검수 대상: private `061015ed-cys/Upstage-AI` main `575745bd8c6a8f00627197de6e6bb8530bcec6bb`. 팀원 4 실명과 권한은 미확정이다. 이 문서는 검수 결과이며 팀원 1의 Release 승인이나 포털 접수 증명이 아니다.

## 단계별 판정

| 단계 | 완료·증거 | 미완료·추가 작업 | 승인 |
| --- | --- | --- | --- |
| ① 코드·증거 확인 | 실제 main HEAD와 폴더·코드 확인. Python V6, Studio Adapter, Independent QA, Cross-Agent 구현 파일 존재. [동일 HEAD CI](https://github.com/061015ed-cys/Upstage-AI/actions/runs/41571014481) 성공 | 신규 V6 Studio Native와 실제 QA Input/Report 미수신 | 조회에는 불필요 |
| ② DOCX 대비 분석 | 01/05/09/10 요구·RACI 확인. 팀원 4 문서·시연 산출물 초안 작성 | 포털 필수칸·팀원 4 이름·등록 명단 미확인 | 팀원 1 지정 필요 |
| ③ 실행·테스트·보안 | Windows Python 3.12.10 로컬 Ruff PASS, 두 데모 CLI 실행, C001 archive check PASS, local gate overall BLOCKED. 전체 pytest 결과는 아래 기록 | Studio Live·Gold·현재 Config 실제 QA 연결 미확인 | 신규 유료 실행은 팀원 1·2 승인 필요 |
| ④ 최소 수정안 | README clone 주소, 통합 설치 명령, 없는 생성 스크립트·Gold 경로를 고침. 엔진·PDF·Gold는 변경하지 않음 | Studio 설정 변경안은 팀원 1·2 소유 | Git 반영 전 팀 검토 |
| ⑤ 담당 산출물 | 제출 요건표, 재현 Runbook, 데모·발표 대본, 인계 보고 | 영상·슬라이드 파일·실제 제출 ZIP·영수증 없음 | 대외 공유 범위·제출 승인 필요 |
| ⑥ 최종 검수 | 코드 검수와 Release 판정 분리 | G0~G9 필수 외부 증거 충족 전 Release BLOCKED | 팀원 1 최종 Gate 승인 |

## 통합 코드 상태와 증거 한계

`src/leadtime_guardian/engine.py`, `studio_adapter.py`, `studio_integration.py`, `qa/studio_qa_adapter.py`, `qa/cross_agent.py`, `qa/provenance_link.py`, `qa/integration.py`를 확인했다. `qa.integration`은 원본 bytes를 읽어 V6와 QA 도구를 잇고, 후보 일치가 Gold 승인이 아님을 코드로 표시한다. 저장된 `data/results/studio_runs/C001_20261030_v4/`는 2026-10-30 V4 보관 기록이다. `configs/studio_native/config_v4.export.json`은 Config export이며 신규 Job 결과가 아니다.

CI 워크플로는 Python 3.11에서 전체 Ruff, pytest, 보관 C001 replay, PDF inventory를 실행한다. 동일 HEAD의 Actions 결론은 SUCCESS이고 해당 Job 로그에 `739 passed`가 기록돼 있다. 이는 현재 Studio Native E2E, 실제 IndependentQA Input/Report, 사람 승인 Gold를 증명하지 않는다. 11월 2일 통합 보고서의 별도 CI 수치를 현재 HEAD의 증거로 전용하지 않았다.

Windows 로컬 첫 pytest 실행은 `733 passed, 5 skipped, 1 failed`였다. 실패는 `test_qa_ninth_release_evidence.py`가 UTF-8 보고서를 cp949 기본 인코딩으로 읽는 환경 차이였다. CI의 `PYTHONUTF8=1` 조건으로 전체 재실행한 결과 `734 passed, 5 skipped`였다. Windows 건너뜀 5개는 동일 HEAD의 Ubuntu CI에서 실행돼 `739 passed`로 기록됐다.

## 보안 및 제출 패키지 상태

`.gitignore`는 `.env`와 `.env.*`를 제외하고 `.env.example`만 허용한다. 추적 파일명에서 `.env`, 개인키, credentials 파일은 발견되지 않았다. 텍스트에 대한 고정형 키·개인키 패턴 검색에서는 후보가 발견되지 않았다. 이는 자동 패턴 검사 범위이며, PDF/이미지/압축 내부와 모든 비밀 형식을 완전 감사한 판정은 아니다. PDF, Native, Gold의 대외 공유 허용 범위와 3자 라이선스는 **NOT_VERIFIED**. `LICENSE` 파일은 저장소에 없다.

제출 ZIP은 **NOT_CREATED**. 실제 포털 규격, 공개 권한, 민감 자료 범위, Live 증거, 승인 Gold가 미확정이므로 완성 패키지로 표기하지 않는다. 계획 구조는 `00_ORIGINAL_PDF`(승인 시), `01_STUDIO_CONFIG_DRAFT`, `02_STUDIO_NATIVE_RAW`, `03_PYTHON_V6`, `04_QA_SANDBOX`, `05_HUMAN_GOLD`, `06_SOURCE_GIT`, `07_DEMO_SUBMISSION`, `08_RELEASE_GATES`다. 포함 파일마다 상대 경로, SHA-256, bytes, 증거 등급, 소유자, 공개 가능 여부를 manifest에 기록한다. 실제 ZIP 제작 뒤 새 경로에서 해제, 경로 길이, 파일 수·SHA, README 링크, CLI, 영상 재생, 심사자 viewer 권한을 검사한다.

## G0~G9 및 다음 인계

| Gate | 상태 | 다음 증거와 소유자 |
| --- | --- | --- |
| G0 제출 규격 | BLOCKED | 포털 입력칸·팀 등록 명단, 팀원 1·4 |
| G1 Studio Native | BLOCKED | 단일 C001 Job/Step, PDF3 SHA와 raw 단계, 팀원 2 |
| G2 Python V6 Live | BLOCKED | 실제 Native 기반 출력과 Sidecar, 팀원 2 |
| G3 Independent QA | BLOCKED | 실제 QA Input/Report와 QA Job, 팀원 1 |
| G4 Provenance | BLOCKED | PDF upload receipt, 원본 SHA, Cross-Agent 바인딩, 팀원 1·2 |
| G5 Human Gold | BLOCKED | 페이지별 사람 승인과 지표 분모, 팀원 3 |
| G6 안전 회귀 | PASS_LOCAL / LIVE_NOT_VERIFIED | C001/C013/C017/C008 신규 실측, 팀원 1·2·3 |
| G7 원본 통합 | CODE_CI_PASS / RELEASE_BLOCKED | 단일 HEAD 증거와 팀원 1 승인 |
| G8 시연·제출 | BLOCKED | 영상·슬라이드·포털 규격에 맞춘 ZIP, 팀원 4 |
| G9 인계·접수 | BLOCKED | 팀원 1 서명, 승인 후 접수 영수증, 팀원 1·4 |

우선 순서: (1) 팀원 1이 팀원 4 담당자와 포털 접근·제출 범위를 정한다. (2) 팀원 2가 원본 Native/Sidecar/PDF receipt를, 팀원 1이 QA Input/Report와 Gate를, 팀원 3이 승인 Gold를 인계한다. (3) 팀원 4가 실제 결과로 영상·슬라이드·ZIP을 완성하고 preflight를 수행한다. (4) 팀원 1의 명시적 승인 후에만 최종 제출하고 영수증을 보존한다.

`UPLOAD_AUTHORIZATION=NOT_GRANTED`, `SUBMISSION_RECEIPT=NOT_AVAILABLE`, `OVERALL_RELEASE=BLOCKED`.
