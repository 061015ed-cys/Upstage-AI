# LeadTime Guardian — 9차 제출 준비도 및 누락 증거 보고

## GitHub 검증 준비
- PR #10: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/10
- 개발 측 코드 경로: 원본 Stage Intake → Strict JSON 및 Native 문서 검증 → Python Safety V6 → Independent QA → Cross-Agent/Provenance → B0/E1 비교(실측 존재 시) → Release Gate.
- 기존 Python V6 엔진, QA Input 타입 보존, B0/E1 원본 SHA 연결, PDF Source File ID/Receipt/Sidecar 체인은 재사용한다.
- 9차 추가: NEW_LIVE_STUDIO 지정 시 필수 증거 없으면 Python V6 실행 전 BLOCKED/NOT_RUN; release-evidence/v1 로컬 원본 목록·SHA·불일치·다음 조치 JSON/Markdown.
- CI 코드 검증: #41304643210, whole Python 597 PASS (QA 408 포함), Ruff PASS. 최종 Checkpoint HEAD 기준 CI는 별도 확인.
- 이 성공은 프로그램 자체의 로컬 통합·보관 데이터 안정성이다. 실측 업로드/문서 정확도 인증을 의미하지 않는다.

## Studio·Team 2·Team 3 실제 자료
- C001 XLSX 한 Job/Extract3 기록은 SINGLE_JOB_REPORTED_XLSX만 가능. Native 3문서 실측 검증 NOT_VERIFIED.
- Extract3 분기, Merge, Normalize, IndependentQA 실제 INPUT와 Report 원본 JSON 및 각 Job/Step/Config/SHA: NOT_PROVIDED.
- 원본 발주서/납기통보서/견적서 PDF 바이트 SHA 및 운영/QA Upload Receipt: NOT_PROVIDED.
- Team2 Python V6 실제 sidecar/provenance 및 최신 Job 실행 결과: NOT_PROVIDED.
- Team3 Human-reviewed PDF 페이지 근거 Gold: NOT_PROVIDED.
- E1 원본 Job 및 Config diff: NOT_RUN 또는 NOT_PROVIDED; 실제 비교 NOT_MEASURED.

## 한 번에 누락 목록 확인
    python scripts/qa_release_evidence_check.py --manifest /private/evidence/release_evidence.json --json-report /private/results/missing_evidence.json --markdown-report /private/results/missing_evidence.md

입력 파일이 부족할수록 missing_inputs와 next_required_action으로 정확히 다음 담당 원본을 보여준다. 입력 경로 문제·SHA 충돌은 invalid_inputs, FAIL로 구분한다. 모든 파일을 수집해도 이 단계 결과는 BLOCKED이며, Python/QA/Studio Live 인증은 별도 검증이 필요하다.

## 100% 제출 준비에 필요한 실제 단계
1. Studio 담당자가 현재 NCik 실행 결과의 Extract/Merge/Normalize/QA Input/Report 원본을 데이터·SHA·Step IDs와 함께 보존·회수.
2. 실제 3개 PDF 원본 SHA, 동일 운영/QA 업로드 Receipt, 팀원 2 V6 Sidecar 및 Python 결과를 연결.
3. 팀원 3의 Human-reviewed PDF 근거 Gold와 QA 오류 목록 교차 검증.
4. Stage Intake → Python V6 → Independent QA → Cross-Agent → Provenance Gate를 실제 동일 Case/Job/Config/Step 증거로 실행.
5. E1 실제 실험이 있는 경우 동일 원본 PDF 바이트를 보장하고 B0/E1 필드·타입 변화와 Gold 기반 정확도 비교. E1 실행 승인 전 자동 유료 Job 금지.
6. 최종 Commit의 GitHub CI SUCCESS, 별도 릴리스 승인/공식 제출 요구사항을 확인한 뒤 최종 결정.

현재 실제 Studio E2E·Human Gold·Overall Release는 BLOCKED. GitHub의 CI나 추정 완성도 백분율만으로 PASS 승격 불가.
