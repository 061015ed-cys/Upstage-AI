# LeadTime Guardian — 9차 전체 회귀 검증 보고

## 검증된 코드 SHA 및 실행 로그
- 8차 기준 HEAD: b4c01ecddbd00bc33bca1ae8c1735ac768eea20f (full Python 583/independent QA 394).
- 9차 코드 수정 SHA: 9e15fcfed44190e71863f7c5a8f1a73d26ed2d1a.
- GitHub Actions: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/actions/runs/41304643210 — **SUCCESS**.
- 독립 QA 전체: **408 passed**.
- 전체 Python: **597 passed** (QA 408 포함; 합산하지 않음).
- QA Ruff, 전체 저장소 Ruff: **All checks passed**.
- Archived C001 original replay: CI step success, offline-only.
- Local Integration Gate: local_checks_passed=true; overall_status=BLOCKED.
- 전체 실패: 0. 모든 수치는 중간 코드 HEAD이며 최종 문서·체크포인트 SHA의 CI를 재확인해야 함.

## 이번에 직접 추가한 부정 테스트
- NEW_LIVE_STUDIO에서 Stage manifest가 없으면 status BLOCKED, python_safety_status NOT_RUN, no python_summary.
- QA Native/Report가 있더라도 Team2 Sidecar/Upload Receipt·원본 QA Config 등이 누락되면 실행 차단.
- 기존 ARCHIVED_STUDIO 로컬 C001 계산은 후방 호환: status BLOCKED, python_safety_status PASS_LOCAL.
- Release Evidence Manifest에 원본이 없으면 3개 Extract 분기를 포함한 정확한 missing_inputs 보고.
- 실제 읽은 로컬 파일 SHA256은 계산해 기록하되 Studio 클라우드 실행 인증은 NOT_AUTHENTICATED.
- 파일이 SHA 선언 이후 변경되면 FAIL; 문서 겉의 SHA만 믿지 않음.
- 증거 폴더 외부로 탈출하는 심볼릭 링크 거부, 중복 JSON Key 입력 거부, Stage manifest Case/Job/Config 충돌 거부.
- 로컬 원본 목록으로 JSON 및 Markdown 보고서를 생성하고 source raw 바이트 변경 없이 보존.
- 보고서 출력 경로가 원본 Release Manifest 또는 기존 PDF 파일과 동일하면 exclusive create로 쓰기를 거부하고 FAIL; 기존 Manifest/PDF의 byte-for-byte SHA 보존 회귀 테스트 두 개 추가. 정확한 최종 pytest 개수는 최종 HEAD CI를 확인해야 함.

## 기존 회귀 테스트 지속 보존
- Strict JSON/Studio Adapter/Team2 Python Safety V6 및 Document Match/Validate.
- Normalize↔QA 타입 보존(false≠0, true≠1), QA Input/Report Cross Job 차단.
- Extract/Merge/Normalize Stage SHAs, Step/Job IDs, 중복 Document IDs, Native 의미 기반 내용 해시.
- B0/E1 manifest 동일 원본 PDF SHA 선언, Normalize 원본 실제 바이트 SHA 대응, JSON 필드·타입 차이 시 CHANGED_UNVERIFIED.
- Cross-Agent handoff, Team2 sidecar, PDF Source File ID/Upload Receipt 로컬 계약 테스트.
- XLSX Shared String 49 인덱스 22개가 EMPTY_STRING이라는 6차 회귀.
- C001 보관 정상/변경 납기/견적 비용 기준, C013 PO1·PO999 불일치, C017 한국어 날짜 근거, C008 분할 입고/수량 중복 방지.
- CI 전체 pytest와 QA 전용 pytest는 위 모듈들을 포함하지만 모든 부문을 실제 Live로 다시 돌린 것은 아님.

## Final CI 원칙
Run #41304112310은 중간 코드 SHA에 묶인 SUCCESS 증거임. 이 문서 이후 체크포인트/최종 문서 Commit까지 포함된 마지막 HEAD에 대해서는 별도의 GitHub Actions SUCCESS와 로그의 실제 QA/전체 pytest·Ruff를 확인해야 한다. 새 Live Studio 실행/Gold 결과 없이 Overall Release PASS는 금지.
