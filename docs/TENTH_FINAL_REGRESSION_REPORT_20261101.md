# LeadTime Guardian — 10차 최종 GitHub 전체 회귀 보고

## Verified code checkpoint

- 10차 코드 SHA: `006805802e563c80dbbda8c466dc2e305ba3f792`
- GitHub Actions code run #41306728237: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41306728237
- Job conclusion **SUCCESS** / failures **0**.
- Independent QA: **411 passed** (CI: `PYTHONPATH=src python -m pytest -q tests/test_qa_*.py`).
- Full Python: **600 passed** (QA 411 포함, 합계 1011개가 아님).
- QA Ruff: **All checks passed**.
- Whole repository Ruff: **All checks passed**.
- Archived C001 Replay: GitHub CI step success, offline archived data only.
- Local integration: `local_checks_passed:true`, `overall_status:"BLOCKED"` — 실제 Studio/Gold 미확보로 의도적 차단.
- 위 검증은 문서·Checkpoint 작성 전 코드 commit에 묶여 있으므로, **최종 HEAD의 Actions SUCCESS 확인은 별도 필수**.

## Last changed-code regressions

| 오류/위험 | 검증 | 통과 기준 |
|---|---|---|
| JSON/Markdown 출력 경로 완전 동일 | 새 부정 테스트 | 사전 FAIL, 출력 미생성 |
| 부모 심볼릭 링크로 출력 경로 별칭 동일 | 새 부정 테스트 | 사전 FAIL, 출력 미생성 |
| JSON 출력 생성 뒤 Markdown 기존 원본과 충돌 | 새 부정 테스트 | 출력 전체 FAIL, JSON 새 파일 롤백, 기존 원본 Byte 보존 |
| Manifest/PDF를 output 경로로 지정 | 기존 9차 회귀 보존 | 기존 원본 덮어쓰기 FAIL |
| 증거 SHA가 사후 변경됨 | 기존 9차 회귀 보존 | FAIL, 실제 원본 SHA 재계산 |
| NEW_LIVE_STUDIO에서 Stage/QA/PDF Evidence 누락 | 기존 9차 회귀 | BLOCKED + Python V6 NOT_RUN |
| Archive C001 정상 경로 | 기존 CI 회귀 | Python V6 PASS_LOCAL, Release BLOCKED |
| Stage 원본의 잘못된 Job/Case/Config/Step | 6~9차 테스트 유지 | FAIL/차단 |
| Boolean false vs numeric 0, true vs 1 | 8차 테스트 유지 | 잘못된 동등 판단 거부 |
| B0/E1 Normalize raw SHA 미일치 | 7~8차 비교 회귀 유지 | diff BLOCKED, accuracy NOT_MEASURED |
| QA Step Input/Report 다른 Job 및 잘못된 원본 | 기존 QA 테스트 유지 | 실측 성공으로 승격 금지 |
| Human Gold/실제 E1 없음 | 기존 Gate | Release BLOCKED, 개선 NOT_MEASURED |

## 기존 Python/QA 회귀 (로컬 범위)

- Strict JSON, Studio Adapter, Stage Intake, Release Inventory.
- Document Match/Validate, Python Safety V6, Quantity/Receipt/Quote and Partial Delivery Allocation.
- Normalize→IndependentQA Input (exact typed JSON content), IndependentQA Report, Cross-Agent/Provenance.
- Original PDF SHA/Upload Receipt/Step ID strict validation.
- C001: 발주·변경 납기·견적 `original_shortage=0 EA`, `revised_shortage=60 EA`, `extra_supply=60 EA`, `quote_total=60500 KRW`는 기존 보관·합성 검증 기준이며 신규 NCik Live 결과가 아님.
- C013: PO1/PO999 불일치 차단. C017: 한국어 날짜와 원문 근거 처리. C008: 분할 입고 및 이중 수량 배정 방지.
- XLSX `sharedStrings[49]` 실제 empty 22개; literal 49 = 0. 과거 환각 원인 추정은 사실로 취급하지 않음.
- Draft Extract null/type 충돌은 saved B0 v1과 동일 설정이라는 검증이 없어 `FAIL_STATIC_DRAFT_CONTRACT`, Studio 실제 값 `NOT_VERIFIED`.

## Reproducibility & limits

1. 개발 기준 `pip install -r requirements-agents.txt` (실제 CI requirements check 후 설치).
2. `PYTHONPATH=src python -m pytest -q tests/test_qa_*.py`.
3. `python -m pytest -q`.
4. `python -m ruff check src/leadtime_guardian/qa scripts/qa_*.py tests/test_qa_*.py`.
5. `python -m ruff check .`.
6. 기존 Runbook: `docs/NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md`에 Stage/Release/Combined E2E/B0-E1 CLI 입력 및 종료코드 상세.
7. NEW_LIVE_STUDIO/Team2 실제 Job/Gold는 자료 미확보로 수행하지 않았음. 합성 검증 성공은 제공자 Job 성공 증거가 아님.

GitHub PR #11 최신 최종 문서 SHA는 실행 로그에 있는 커밋을 다시 조회해 검증한다. GitHub CI SUCCESS와 프로젝트 `OVERALL_RELEASE_GATE=BLOCKED`는 모순이 아니다.
