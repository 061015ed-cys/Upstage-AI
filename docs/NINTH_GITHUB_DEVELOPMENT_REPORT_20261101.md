# LeadTime Guardian — 9차 GitHub 집중 개발 보고서

2026-11-01. 원본 운영 저장소와 기존 PR은 수정하지 않음.

## 기준선 및 PR 구조
- QA 저장소: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy
- 시작 기준: 8차 Draft PR #9, HEAD b4c01ecddbd00bc33bca1ae8c1735ac768eea20f, CI #41302756219 SUCCESS, full Python 583 PASS / QA 394 PASS.
- 신규 9차 Draft PR #10: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/10
- 격리 브랜치: feat/qa-ninth-release-readiness-20261101; Base = feat/qa-eighth-release-hardening-20261101.
- 최신 9차 코드 검증 run #41304643210: full Python 597 PASS, independent QA 408 PASS, QA Ruff PASS, 전체 Ruff PASS, Archived C001/local checks local_checks_passed=true, overall_status=BLOCKED.
- 전체 Python 테스트 수에는 QA 테스트가 포함됨. Final docs/checkpoint HEAD의 CI는 별도 재확인.
- PR #4~#9 모두 Draft/미병합 상태이며 단계별 직전 QA 브랜치가 Base다. PR#10도 Draft이며 자동 Merge/Force Push 없음.
- 운영 팀원 2 PR #12는 e9b9992b593a42d427ff1bbadeb9a9866ca593bd. 핵심 Python V6 6모듈 내용 불변이 보존 목표.

## 9차 발견한 실제 결함 및 최소 수정
### HIGH — NEW_LIVE_STUDIO에 Stage 증거가 없어도 계산 수행 가능
8차 scripts/qa_combined_e2e_check.py는 --execution-kind NEW_LIVE_STUDIO이어도 --stage-intake-manifest가 선택 사항이라 보관 Replay와 동일한 Python V6 로컬 계산 경로가 열려 있었다. Release가 자동 승인되는 것은 아니었지만 Python PASS_LOCAL 결과를 Live 실행처럼 해석할 위험이 남았다.

수정: NEW_LIVE_STUDIO는 실제 원본 Stage manifest, QA Native/Report 원본, QA Sandbox Agent/Config ID/Version, Team2 provenance, 운영/QA Upload Receipt, PDF Root가 없으면 status BLOCKED, python_safety_status NOT_RUN, release_authorized false를 반환한다. 일부 Stage 원본이 빠져도 Python V6를 실행하지 않는다. ARCHIVED_STUDIO/ARCHIVED_REPLAY의 기존 로컬 경로는 유지했다.

### MEDIUM — BLOCKED 외에 빠진 파일과 원본 SHA를 한 번에 파악하기 어려움
기존 scripts/qa_stage_intake_check.py와 scripts/qa_combined_e2e_check.py는 결측 Stage를 보고하지만 실제 3개 원본 PDF·Team2 Sidecar·Human Gold·QA Input/Report를 일괄 확인하는 로컬 Inventory가 없었다.

수정: src/leadtime_guardian/qa/release_inventory.py 및 scripts/qa_release_evidence_check.py. 독립 로컬 메타데이터 계약 leadtime-release-evidence/v1을 읽어서 정확히 누락된 원본, 각 로컬 파일의 SHA256, 경로/파일 크기, 선언 SHA 일치, 잘못된 증거와 요구되는 다음 행동을 출력한다. Stage 검사는 기존 Inspect 함수를 그대로 재사용. 어떤 경우에도 Studio Cloud 인증/Gold 정확도/Release PASS로 승격하지 않는다. JSON·Markdown 보고서 생성 가능. 상대 경로, 디렉터리 외부 심볼릭 링크, 잘못된 JSON, 선언 SHA 불일치 차단.

### HIGH — 보고서 출력 경로가 기존 증거 파일을 덮어쓸 수 있음
기존 9차 초안 scripts/qa_release_evidence_check.py가 Path.write_text로 결과를 저장해 --json-report/--markdown-report를 원본 Manifest/PDF 경로로 잘못 지정하면 파일을 손상할 수 있었다. 원본 보호를 위해 exclusive create (open mode x)로 수정했고 파일이 이미 존재할 때 FAIL/REPORT_OUTPUT_NOT_WRITABLE을 반환한다. 원본 파일 바이트 보존 부정 테스트를 추가했다.

### LOW — Stage manifest 없이도 Extract3/하위 Step의 누락 항목이 구체적이지 않음
9차 Release Inventory는 Stage manifest 자체가 없는 경우에도 Extract 발주서·통보서·견적서, Merge, Normalize, IndependentQA INPUT/Report를 개별 missing_inputs로 표시하도록 개선했다.

## 변경 범위
- scripts/qa_combined_e2e_check.py
- src/leadtime_guardian/qa/release_inventory.py (신규)
- scripts/qa_release_evidence_check.py (신규)
- tests/test_qa_ninth_live_preflight.py (신규)
- tests/test_qa_ninth_release_evidence.py (신규)
- docs/NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md
- 본 보고서 및 나머지 9차 Readiness/Regression/Studio Delta/Gate/Checkpoint

## 원본 데이터와 현장 실행 한계
- 신규 B0 C001: XLSX에 job_NCik8shwrgM93PDnNNYukT, cfg_X2xXakDtmDTHh2RoqVysvL v1, PDF 3건 Extract 분기가 보고됨. 원본 Native 3문서와 실제 QA Step Input/Report 없음.
- XLSX SHA: ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb. 22개 XML 공유 문자열 인덱스49의 실제 값은 EMPTY_STRING; 문자/숫자 literal49는 0. 어느 Studio Step이 빈 문자열을 생성했는지는 UNKNOWN.
- 원본 PDF Upload Receipts, Team2 Live Sidecar, Team3 Human-reviewed Gold, 실제 E1 Job 미제공.
- Live Studio Job 재실행, 유료 Job, 원본 PDF/XLSX/Native/Gold 업로드·변조, main/PR merge 모두 없음.
- 로컬 파일명과 SHA가 일치하는 사실은 클라우드 제공자 인증이나 품질 향상 증거가 아니다.

## 기술 준비도 판단
- GitHub QA 코드·CI: 높은 수준으로 검증됨 (597 전체 Python/408 QA, Ruff PASS).
- '코드 98~99%' 또는 '담당 제출 준비 96~97%'는 과거의 주관적 추정치이며 테스트에서 측정된 객관적 성취율이 아니다.
- 9차에서는 신규 Live 사전 차단과 누락 원본 패키지 탐지를 실제 테스트로 추가했으나, 분모가 정의된 기능 완성도 측정치가 없으므로 새로운 확정 백분율을 주장하지 않는다.
- 실제 제출 가능: BLOCKED. 실제 Native→Python V6→QA→PDF provenance→Gold→Release 전체 확인 전까지 100% 준비 상태는 아님.

자세한 재현 절차: docs/NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md
