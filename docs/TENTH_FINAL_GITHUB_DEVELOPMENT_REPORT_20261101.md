# LeadTime Guardian — 10차 최종 GitHub 개발 및 코드 동결 후보

Date: 2026-11-01 KST. Scope: GitHub QA/오프라인 통합 검증. Studio 유료 Job, 실제 PDF 원본 업로드, 운영 PR 병합 없음.

## 1. 코드 출처

- 원본 QA 저장소: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy
- 9차 기준 Draft PR #10: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/10
- 9차 최종 HEAD: `74f8989a494481a71116f6ca3641d1bf01a3cdbe`
- 9차 HEAD의 CI: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41304821054 (597 Python, 408 QA, Ruff PASS).
- 10차 독립 브랜치: `feat/qa-tenth-final-code-freeze-20261101`.
- 10차 신규 Draft PR #11: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/11
- 10차 코드 테스트 SHA: `006805802e563c80dbbda8c466dc2e305ba3f792`.
- 10차 코드 CI run: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41306728237 — SUCCESS.
- 코드 CI: 전체 Python 600 PASS, QA 411 PASS (전체에 포함), QA Ruff PASS, 전체 Ruff PASS, Archived C001 Replay PASS_LOCAL, Local Integration local_checks_passed=true, overall_status=BLOCKED.
- **문서까지 포함한 최종 HEAD/CI는 자기참조로 checkpoint에 삽입하지 않는다. GitHub PR #11 최신 head SHA와 그 SHA에 연결된 Actions SUCCESS를 최종 보고에서 확인한다.**

## 2. 실제 확인한 최종 결함: MEDIUM

### 9차의 보고서 부분 생성 (partial artifact) 위험

이전 `scripts/qa_release_evidence_check.py`는 `--json-report`와 `--markdown-report`를 순차적으로 `open("x")`로 생성했다. 기존 파일 덮어쓰기는 이미 방지했으나, 첫 번째 JSON 생성이 성공하고 두 번째 Markdown 생성이 실패하면 전체 명령은 FAIL이어도 처음 생성된 JSON이 남았다. 따라서 오래되거나 부분적으로만 완료된 보고서를 정상 결과로 오해할 가능성이 있었다. 또한 두 출력이 같은 파일 경로 또는 부모 심볼릭 링크로 같은 파일을 가리킬 수 있었다.

수정:
- `_write_reports_exclusively(reports)`로 두 출력 경로의 해석된 위치 중복 사전 차단.
- 두 출력 모두 기존 파일 존재 시 exclusive-create 실패; 사용자 소유 원본 덮어쓰기 금지.
- 생성 중 실패하면 **이번 실행에서 새로 만든 파일만 역순으로 정리**하고 FAIL 반환.
- PDF, Release Manifest 및 외부 원본 자료는 변경하지 않음.
- 추가 음성 회귀: 출력 두 경로 동일, 두 번째 파일이 이미 존재하는 경우 첫 번째 제거 및 기존 원본 바이트 보존, 심볼릭 링크 부모를 거친 출력 경로 중복.

## 3. 수정 파일

- `scripts/qa_release_evidence_check.py`
- `tests/test_qa_ninth_release_evidence.py`
- 10차 개발·회귀 보고서, GITHUB_100_PERCENT_COMPLETION_CHECKLIST, FINAL_STUDIO_HANDOFF, Release Gate Matrix, Code Freeze Checkpoint.

## 4. 독립 QA 코드 및 통합 시스템 감사

기존 7~9차 코드를 재구현하지 않음:
- `qa_combined_e2e_check.py`: NEW_LIVE_STUDIO에서 Stage/QA Native/Report/Team2 Provenance/PDF Upload Receipts/QA Config 누락 시 Python V6 NOT_RUN, 합성 보관 실행 분리.
- `qa_release_evidence_check.py` 및 `release_inventory.py`: 실제 로컬 증거 바이트 SHA, 누락 원본 및 경로 충돌 목록, JSON/Markdown 보고서, Cloud 인증 미확보 표시.
- `qa_stage_intake_check.py` 및 `stage_trace.py`: 원본 Extract/Merge/Normalize/QA Step 파일 SHA 및 Job/Case/Config/Step/문서 비교, null·empty·0 타입 구분.
- `qa_b0_e1_compare_check.py` 및 `experiment_compare.py`: B0/E1 Manifest·Normalize 원본 SHA 연계, Field diff, 원본 동일성 및 Gold 없는 개선 판정 차단.
- `input_delivery.py`, `cross_agent.py`, Python Safety V6/Studio Adapter/Strict JSON: 기존 정적·오프라인 계약 유지.
- 팀원 2 원본 핵심 모듈 6개(`engine.py`, `studio_adapter.py`, `studio_integration.py`, `strict_json.py`, `provenance.py`, `agents_api.py`)는 운영 PR #12의 확인 SHA `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`와 Blob SHA 동등성 최종 대조 대상이며 원본을 변경하지 않음.

## 5. 최종 코드 동결 판단 조건

- 신규 **재현된 미수정 CRITICAL/HIGH 결함 없음**. 모든 결함 부재를 수학적으로 증명한 것은 아님.
- 전체 pytest 및 Ruff, 보관 C001, Local E2E, 10차 부정 회귀 PASS.
- Studio 신규 C001 실제 Live/Native와 Human-reviewed Gold가 없는 점은 GitHub 코드 동결 허용 범위에 속하지만 제품 Release PASS와 별개.
- PR #11 최종 문서 SHA CI SUCCESS 시 `GITHUB_CODE_FREEZE_GATE=PASS_LOCAL_CANDIDATE`, 불일치 시 PENDING/FAIL로 유지.
- `GITHUB_OWNED_READINESS`는 별도 문서의 10항목 100점 채점 기준에 따름. 이 보고서의 테스트 PASS 수가 정량적 기능 완성도 100%를 의미하지 않음.

## 6. 실제 Studio 증거 현황

- C001 B0 단일 Job이 XLSX에 보고됨: `job_NCik8shwrgM93PDnNNYukT`, `cfg_X2xXakDtmDTHh2RoqVysvL` v1.
- XLSX 원본 SHA `ad338d318f48c566dce3bf92e6b46c2cff49cd429dba90a79ea2941703ff82eb`. 공유 문자열 인덱스 49를 참조하는 22개 셀은 실제 EMPTY_STRING(숫자/문자 literal49 = 0)으로 분석됨. 최초 생성 Step UNKNOWN.
- 신규 NCik 원본 Extract 3건·Merge·Normalize·IndependentQA INPUT/REPORT 및 Native·PDF 업로드 영수증, Team2 실제 V6 Sidecar, Team3 Human Gold, E1 Live 파일은 여전히 NOT_PROVIDED/NOT_VERIFIED.
- 최종 `ACTUAL_STUDIO_E2E_GATE=BLOCKED`, `OVERALL_RELEASE_GATE=BLOCKED`.

세부 실행 절차는 기존 `docs/NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md`를 재사용하고, 마지막 인계는 `docs/FINAL_STUDIO_HANDOFF_20261101.txt` 참조.
