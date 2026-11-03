# 검증 근거 기반 데모와 발표 준비

## 시연 경로

| 경로 | 지금 보여줄 수 있는 것 | 아직 필요한 것 |
| --- | --- | --- |
| C001 정상 | `scripts/run_portfolio_demo.py`의 합성 오프라인 계산: 원래 부족 0, 변경 후 60, 추가 60 EA, 대체비용 60,500 KRW. 2026-10-30 V4 보관 Studio 실행과 로컬 replay는 별도 근거다. | 현재 V6 Native 단일 Job, PDF 3개 원본 SHA와 receipt, 실제 QA Input/Report, Human Gold |
| C013 PO 불일치 | 테스트와 합성 DRAFT에서 PO1/PO999 불일치를 차단하는 로컬 계약 | 신규 Studio Native에서 `NEEDS_REVIEW` 실측 및 원본 근거 |
| C017 한글 날짜 | 로컬 입력 검증/차단 회귀 | 원문 페이지→추출→정규화 실측 |
| C008 부분 입고 | 로컬 합성 시나리오 R1 40, R2 60 중 R2 변경 시 부족 40, 비용 40,500 KRW | 실제 Native 및 중복 배분 방지 증거 |

## 3분 발표 대본 초안

0:00–0:30: 공급업체 납기 변경이 고객 주문에 주는 영향을 설명한다. 주문과 입고를 자동 승인하지 않고 구매 담당자가 최종 결정한다.

0:30–1:10: 발주서, 납기 변경 통보서, 대체 견적서의 출처를 보여준다. 현재 보유 자료는 합성 PDF이며, 설정 JSON은 실행 기록이 아니다. Studio 보관 V4 화면을 사용하면 화면에 보관 실행 날짜, Job/Config ID와 `ARCHIVED` 표시를 넣는다.

1:10–1:55: C001의 오프라인 Python 결과를 실행해 부족 0→60 EA와 60,500 KRW를 보여준다. 자막에 `LOCAL_REPLAY / SYNTHETIC / PDF_GROUNDING_NOT_VERIFIED`를 표시한다. Independent QA는 코드의 별도 검사로 설명하고, 실제 Input/Report가 들어오기 전에는 Live QA 통과라고 말하지 않는다.

1:55–2:30: C013의 PO1/PO999 불일치가 자동 연결이나 구매 추천으로 이어지지 않아야 함을 보여준다. 현재는 로컬 안전 회귀이며 신규 Studio 결과는 미확인이라고 밝힌다.

2:30–3:00: 원본 SHA, Step/Job, Sidecar, QA, 사람 검수 Gold가 연결될 때 Release Gate를 통과하는 구조를 설명한다. 현재 상태는 코드 검수와 CI 통과, 전체 Release는 BLOCKED다.

실제 화면 캡처마다 `CASE_ID / EXECUTION_KIND / JOB_ID / CONFIG_ID_VERSION / PDF_SHA256`를 표시한다. 알 수 없는 필드는 `NOT_VERIFIED`로 표기한다. 정확도와 개선율 그래프는 사람 승인 Gold와 분모를 받은 뒤에만 추가한다. 현재 데모 영상 파일은 **NOT_PRODUCED**.

## 슬라이드 순서

1. 문제와 사용자 결정 지점
2. 문서 3종과 출처·합성 데이터 범위
3. Studio → Python V6 → Independent QA → Cross-Agent → Human Gold 구조
4. C001 오프라인 계산과 보관 V4 화면의 실행 종류 구분
5. C013 안전 차단의 로컬 회귀와 Live 검증 대기
6. G0~G9 상태, 남은 증거와 한계

## 파이널 운영과 질의응답

발표자 1~2명 이름·기기·HDMI·네트워크·오프라인 영상 백업은 선정 후 지정한다. 예상 질문과 답변은 다음과 같다.

1. 실제 기업 데이터인가? 현재 공개 예시는 합성 데이터다.
2. Gold 정확도는? 사람 승인 Gold와 분모가 없어 아직 측정하지 않았다.
3. C001 수치가 실측인가? Python 오프라인 계산이며, 보관 V4 Studio 실행과 구분한다.
4. 새 V6 Studio E2E는 성공했나? 현재 원본 Native가 없어 미확인이다.
5. 충돌하는 PO는? 자동 치환하지 않고 검토 대상으로 차단한다.
6. QA가 계산을 승인하나? 문서 QA와 Python 계산, Gold, Release Gate는 서로 다른 검사다.
7. 부분입고 중복은? 로컬 회귀에 포함되며 실제 Native 검증은 남아 있다.
8. API 연결 없이 재현 가능한가? 로컬 합성 데모와 보관 기록 검사는 가능하다.
9. 실제 발주가 실행되나? MVP는 승인 초안까지만 만든다.
10. 배포 준비는 끝났나? 코드 CI는 통과했지만 전체 Release는 BLOCKED다.
