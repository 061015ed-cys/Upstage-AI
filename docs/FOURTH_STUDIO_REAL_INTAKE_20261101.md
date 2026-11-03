# LeadTime Guardian — 4차 Studio B0 실측 수신 및 Cross-Agent End-to-End 개선

기록일: 2026-11-01 KST. 작업: 팀원 1 QA 통합. 운영 저장소/팀원2 소스/기존 PR/Studio/Gold 변경 없음.

## CURRENT_GITHUB_BASELINE / PR4_INTEGRATION_STATUS
- 운영 PR #11: f196c694917f2d9e5f4ec228c752bd3f2a4eb882
- 팀원2 PR #12: e9b9992b593a42d427ff1bbadeb9a9866ca593bd
- QA PR #3: f2aeb848eed0d72893073896898fcaa7154b52a1
- 결합 PR #4: 9d032d883c49df03657931ea88e97a0bd713043f, 기존 CI SUCCESS (QA 315, full Python 504, Ruff PASS)
- **4차 실제 작업:** QA copy Draft PR #5, branch feat/qa-studio-intake-b0-20261101; base is PR #4. 기존 운영/QA 브랜치에는 Commit하지 않았음.

## ACTUAL_STUDIO_INTAKE_READINESS / B0-C001 신규 관측

사용자가 제공한 Studio AI 실행 보고서에서 3개 PDF는 각각 **독립 Job 3개**로 생성되어 완료되었다. 이는 새로운 Upstage 원본 JSON을 이 저장소에서 직접 읽어 인증한 기록이 아니라, USER_REPORTED_STUDIO_AI_SUMMARY라는 관측 자료이다.

| PDF | 신규 Job | 실행 상태 |
| --- | --- | --- |
| SYN-C001_purchase_order.pdf | job_DUdK8NzKasoTvDxGEW9XRY | COMPLETED |
| SYN-C001_delivery_notice.pdf | job_5LX7RWd8SfSUADEfq5MCDL | COMPLETED |
| SYN-C001_quotation.pdf | job_9osC3yrPWtTt2oDjJuSdde | COMPLETED |

- Config cfg_X2xXakDtmDTHh2RoqVysvL / Version 1, batchRunCount 3, 플랫폼 실행 실패 0.
- 실제 Merge/Normalize 본문과 IndependentQA Report 조회 불가 (selectedSplitResultMatched:false), QA status UNKNOWN. 단계 COMPLETED는 QA 판정이 아님.
- PDF 원본 바이트/SHA, 실제 Native 원본, Upload Receipts, 실제 QA 입력/Report 및 Python Job 결과 미확보.
- **B0 single-case 기준선 INVALID, E1 NOT_RUN, B0/E1 개선 비교 NOT_MEASURED**. 독립 Job 3개를 하나의 새 단일 C001 Job으로 합치거나 보관 Job과 혼합하지 말 것.
- 보고된 세 신규 Job은 과거 QA Job job_9DmRWeQsSShHgWUugkELtk 및 C001 V4 보관 Job job_gPmEYKzuJdBA6BmKhVnujs와 서로 다름.
- 이 사실은 data/observations/B0_C001_20261101_USER_REPORTED_STUDIO_AI.json에 원본 실행 파일이 아니라는 출처 라벨과 함께 기록됨.

## ACTUAL_CODE_CHANGES / INTAKE

1. src/leadtime_guardian/qa/studio_batch.py: Case/Config/Job/원본 PDF명/문서 종류/배치 실행 건수 계약 검사. 여러 Job은 INVALID_SPLIT_JOBS로 판정하여 E1 비교 금지. 단일 Job이라는 보고도 원본 Native 없으면 REPORTED_SINGLE_JOB_UNAUTHENTICATED / BLOCKED.
2. scripts/qa_studio_batch_check.py: 유료 Studio 실행 없이 B0 보고서를 읽고 실험 단위 오류와 누락 증거 출력.
3. 기존 scripts/qa_combined_e2e_check.py에 --studio-batch-report 옵션 추가. Split Job 보고를 받은 경우 Python V6 계산 전에 BLOCKED, 기존 Archive와 잘못 연결된 계산값/통합 PASS 출력 금지.
4. C001의 운영 Native와 QA Native는 단일 Job에 purchase_order + delivery_notice + quotation 3문서 및 source_files 3개를 요구하는 차단 검사 추가.
5. 기존 실행기에 --team2-provenance, --qa-pdf-receipt, --operational-pdf-receipt, --pdf-root 옵션 추가. 팀원2 sidecar의 raw export SHA-256, Job ID, Native의 (file_id, file_name)과 receipt의 (file_id, filename), QA manifest, 동일 로컬 원본 PDF 바이트를 결합 검증.
6. 오류 있는 ID/SHA/파일명 또는 원본 증거 부족은 FAIL/BLOCKED. Local source bytes match가 Studio 서버 업로드 인증을 의미하지 않음.
7. tests/test_qa_studio_batch.py, tests/test_qa_combined_e2e_cli.py: B0 3 Job, wrong case/config/job, 한 Job에 한 PDF만 있는 위장 C001, 잘못된 PDF File ID/파일명, native-sidecar SHA 불일치, synthetic receipts, 미완성 증거 테스트.
8. 원본 PDF 또는 Gold, 운영 PR #11/#12, QA PR #3/#4, Studio 설정, 신규 유료 Job에는 아무 변경 없음.

## OPERATION_QA_JOB_LINKAGE / SOURCE_PDF_PROVENANCE

Studio 운영 Job과 QA Sandbox Job의 ID가 다른 것은 정상. **두 Job 각각의 실제 원본 PDF SHA-256 및 Source File ID의 매핑 증거**가 있어야 같은 문서 집합이라고 판정할 수 있음. 이름·Case ID·Config ID가 같아도 동일 원본 PDF를 의미하지 않음. QA Native, QA Report, QA input, 운영 Native, Team2 sidecar, original PDF upload receipts, 실제 saved Config/Job/Step 모두 분리 보관.

## C001_E2E_VALIDATION

기존 V4 Archived C001만 Python V6와 QA local numeric audit에서 원래 부족 0 → 변경 후 60 EA, 대체 견적 60 EA, 60,500 KRW PASS_LOCAL. 신규 B0의 3개 Job을 해당 V4 기록 또는 단일 C001 실측으로 대체하지 않음. 새로운 live B0 = INVALID_SPLIT_JOBS.

## C013_C017_C008_SAFETY_VALIDATION

기존 결합 로컬 DRAFT regression: C013 PO1/PO999 자동 연결 금지, C017 DRAFT ISO 날짜는 통과하지만 원문 한국어 날짜 OCR 성공 여부는 NOT_VERIFIED, C008 R1=40 R2=60 독립 allocation 및 추가 부족 40/비용 40,500 KRW. 실제 새로운 Studio Job으로 재측정한 데이터가 아님.

## STUDIO_EXPERIMENT_COMPARISON / null / Excel 49

B0는 실험 단위 실패이고 E1 NOT_RUN. B0/E1/E2/E3/E4의 실측 성능·정확도·소요시간 개선 수치 생성 불가. Extract/Merge/Normalize/Excel의 원본 단계 값 미회수로 Excel 49 최초 생성 원인 UNKNOWN. V5 Extract nullable primitive schema 정적 충돌은 존재하나 신규 saved Config 개선 여부는 미확인. 검증된 숫자/날짜를 생성해서 누락을 보정하지 않음.

## HUMAN_GOLD_READINESS

현재 DRAFT Human Gold만 존재하고 human_reviewed=true로 확정된 field/page-level evidence 없음. 팀원3에게 C001, C013, C017, C008 각 PDF SHA, 페이지/필드, 검수자/검수일, 정답값, 모호성 사유, 변경 이력 및 파일 버전 요청. DRAFT를 성능 지표의 기준으로 승격하지 않음.

## STUDIO INTAKE COMMANDS

사전 B0 구조 판정: python scripts/qa_studio_batch_check.py --report data/observations/B0_C001_20261101_USER_REPORTED_STUDIO_AI.json --case-id C001 --config-id cfg_X2xXakDtmDTHh2RoqVysvL --config-version 1

실제 **새 단일 케이스 실행**에서 모든 원본이 확보되면:
python scripts/qa_combined_e2e_check.py --operational-native ACTUAL_OP_NATIVE.json --trusted-base CASE_TRUSTED_BASE.json --operational-job-id ACTUAL_OP_JOB_ID --case-id C001 --github-sha CURRENT_FULL_GIT_SHA --qa-native ACTUAL_QA_NATIVE.json --qa-report ACTUAL_QA_REPORT.json --qa-agent-id agt_HdtUJPQPXir9rGKgPWSyZG --qa-config-id cfg_X2xXakDtmDTHh2RoqVysvL --qa-config-version 1 --execution-kind NEW_LIVE_STUDIO --team2-provenance TEAM2_SIDECAR.json --qa-pdf-receipt QA_UPLOAD_RECEIPT.json --operational-pdf-receipt OP_UPLOAD_RECEIPT.json --pdf-root ORIGINAL_PDF_DIRECTORY

Above filenames are placeholders, **not files confirmed currently available**. New QA config v2+ needs explicit allow-list review; do not reuse fixed v1. Do not attach the old split B0 report to a new unrelated job. The CLI never independently authenticates cloud execution or authorizes release.

## CURRENT_RELEASE_GATES (pre-final-HEAD)

| Gate | State | Evidence / owner |
| --- | --- | --- |
| QA_CODE_GATE | RECHECK_FINAL_CI | PR#5 current HEAD QA pytest/Ruff / 팀원1 |
| TEAM2_ENGINE_GATE | PASS_LOCAL | PR#12 source V6 unchanged / 팀원2 |
| COMBINED_SOURCE_COMPATIBILITY_GATE | PASS_PRIOR_BASELINE | exact PR#4 original Team2 source blobs / 팀원1 |
| COMBINED_CODE_CI_GATE | RECHECK_FINAL_CI | PR#5 final SHA GitHub Actions / 팀원1 |
| OFFLINE_E2E_GATE | RECHECK_FINAL_CI | archived V4 and synthetic regressions / 팀원1 |
| STUDIO_DOCUMENT_GATE | UNKNOWN | new QA body inaccessible / Studio AI |
| STUDIO_PROVENANCE_GATE | BLOCKED | actual original PDF SHA/receipts missing / Studio AI + 팀원2 |
| PYTHON_SAFETY_GATE | PASS_LOCAL_PRIOR | actual current Python job not authenticated / 팀원2 |
| CROSS_AGENT_GATE | BLOCKED | real QA native+report not available / 팀원1 |
| HUMAN_GOLD_GATE | BLOCKED | DRAFT only / 팀원3 |
| ACTUAL_STUDIO_E2E_GATE | BLOCKED | split B0, E1 NOT_RUN / Studio AI |
| OVERALL_RELEASE_GATE | BLOCKED | real Studio provenance, Gold, sign-off absent |

## NEXT_STUDIO_AI_PROMPT / TEAM2_EVIDENCE_REQUEST / TEAM3_GOLD_REQUEST

See appended fourth-pass instructions in docs/NEXT_STUDIO_AI_PROMPT_RAW_ADAPTER_20261101.txt, docs/TEAM2_INTERFACE_REQUEST_20261101.md, docs/TEAM3_GOLD_REQUEST_20261101.md. Important: do not repeat known failed PDF-per-Job use_agent route or selectedSplitResultMatched:false retrieval. First configure a single C001 case with all three PDFs, verify execution grouping **before** further B0/E1 paid comparison. Preserve new individual jobs.

## FINAL_CHECKPOINT

Keep release BLOCKED. Review latest PR#5 HEAD and exact CI before restarting; do not borrow CI result from PR#4 or earlier PR#5 SHA. When raw Upstage Native/QA Report, saved Config, two PDF receipts and original PDF bytes are available, re-run both grouping and combined raw E2E; verify Job/Case/PDF SHA and independently Human Gold before any release decision.
