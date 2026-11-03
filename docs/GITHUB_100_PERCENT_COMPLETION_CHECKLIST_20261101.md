# LeadTime Guardian — GitHub GPT 담당 업무 100점 완료 체크리스트

2026-11-01 KST. **이 체크리스트는 GitHub 담당 독립 개발·검증·인계 범위에만 적용**하며 전체 프로젝트의 대회 제출/Studio Live/Gold는 포함하지 않는다. 10개 항목 × 10점, 실제 GitHub 증거 없으면 해당 항목은 PASS 처리하지 않는다.

| # | GitHub 담당 완료 조건 | 배점 | 판정 기준 및 직접 증거 |
|---|---|---:|---|
| 1 | 최종 코드 감사 및 미해결 Critical/High 결함 없음 | 10 | PR#10 최종 소스 확인, 10차 새 중간 출력 충돌 MEDIUM 해결, 600개 전체 회귀·Ruff 실패 0; 별도 신규 CRITICAL/HIGH 확인되지 않음 |
| 2 | Studio Intake 계약 준비 | 10 | `qa_stage_intake_check.py`·`stage_trace.py`: original SHA/Job/Config/Case/Step/3-doc, missing vs FAIL; 7~10차 회귀 |
| 3 | Python Safety V6 통합 | 10 | 원본 Team2 V6 6모듈 무수정, archived C001/replay와 C013/C017/C008의 정상·음성 pytest; `qa_combined_e2e_check.py` NEW_LIVE missing input → NOT_RUN |
| 4 | Independent QA 통합 | 10 | `input_delivery.py` Typed JSON false≠0, QA Report/Job/Document ID 및 null/empty/string 검증, 411 QA regressions |
| 5 | Cross-Agent 및 Provenance 준비 | 10 | `cross_agent.py`·PDF Upload Receipt·Team2 Sidecar/Job linkage 관련 로컬 검증기와 음성 회귀, actual provider 미인증 표기 |
| 6 | B0/E1 비교기 준비 | 10 | `qa_b0_e1_compare_check.py`·`experiment_compare.py` original Normalize raw SHA, Job/Config, same source PDF claims, JSON diff, absent Gold NOT_MEASURED |
| 7 | Release Evidence Inventory 완료 | 10 | `release_inventory.py`·`qa_release_evidence_check.py`; missing_inputs, invalid_inputs, 실제 SHA, 소스 읽기만 수행, 출력 두 경로 충돌·부분 생성 롤백 테스트 |
| 8 | 전체 회귀 검증 완료 | 10 | 10차 코드 HEAD `006805802e563c80dbbda8c466dc2e305ba3f792` CI run #41306728237; Python 600 PASS, QA 411 PASS, QA+전체 Ruff PASS, Archived C001/Local Integration PASS_LOCAL |
| 9 | GitHub 최종 저장 및 최종 HEAD CI | 10 | 신규 격리 Branch `feat/qa-tenth-final-code-freeze-20261101`, Draft PR #11, 실제 Commit·Push; **최종 문서/Checkpoint 포함 HEAD의 GitHub Actions SUCCESS로 이 항목을 최종 확정** |
| 10 | 문서/재현/인계/동결 후보 준비 | 10 | `NINTH_RELEASE_VALIDATION_RUNBOOK_20261101.md` 재사용; 10차 Final Report, Regression, 본 Checklist, FINAL_STUDIO_HANDOFF, Gate Matrix, FINAL_CODE_FREEZE_CHECKPOINT 및 Owner별 후속 의존성 |

## 판정 원칙

- 항목 1~8은 위 코드 SHA의 실제 GitHub Actions 회귀와 10차 코드 감사·테스트로 충족됨.
- 항목 9~10은 Draft PR #11의 **최신 최종 HEAD에 모든 문서가 저장되고 그 HEAD의 Actions가 SUCCESS**로 확인되는 순간에만 최종 PASS로 확정됨.
- 모든 조건 완료 시 `GITHUB_OWNED_READINESS=100/100 (100%)`. 최종 SHA의 CI가 아직 PENDING/FAIL일 때는 이 문서만으로 100점을 주장하지 말 것.
- **`GITHUB_CODE_COMPLETENESS`**: 코드 기능 퍼센트를 객관적으로 측정할 분모가 없으므로 임의로 99/100 같은 숫자를 확정하지 않음; 회귀 및 감사 완료로 CODE FREEZE 후보 판정 가능.
- **`EXTERNAL_EVIDENCE_READINESS`**: 실제 NCik Native 3문서·Extract3/Merge/Normalize·IndependentQA Input/Report·원본 PDF Upload Receipt·Team2 live sidecar·Team3 Human-reviewed Gold·실제 E1 모두 `NOT_PROVIDED / NOT_VERIFIED`; 일부 XLSX의 single Job 행 존재는 Full Evidence가 아님.
- **`OVERALL_RELEASE_GATE`**: 반드시 `BLOCKED` 유지. GitHub 범위 100점은 Upstage Studio 실제 Live/E2E 성공이나 대회 최종 승인 100%와 무관.

## 최종 확인

최종 SHA·CI 확인 방법:

1. PR #11 `https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/11`의 최신 `head_sha` 조회.
2. 동일 SHA의 GitHub Actions workflow run/Job 결론 `SUCCESS` 확인; 전체 pytest 600, 독립 QA 411 (또는 최신 실측 수), Ruff 두 종류 PASS/Archived C001/Local Gate 확인.
3. 팀원 2 PR #12 원본 6모듈 SHA 동일성 확인; 기존 PR #4~#10 및 main 미변경 확인.
4. 위 1~3이 완료되면 본 Checklist의 항목 9~10을 PASS로 최종 판정하고 사용자에게 `GITHUB_OWNED_READINESS=100%`라고 **GitHub 단독 영역에 한해** 보고.
