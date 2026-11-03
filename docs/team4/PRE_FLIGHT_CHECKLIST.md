# 제출 패키지 사전 점검

현재 상태: **BLOCKED**. 이 목록은 실제 ZIP 또는 업로드가 완료됐다는 기록이 아니다.

## 파일과 재현

- [ ] 포털 필수 제출칸, 확장자, 크기, 영상 길이와 최종 마감 확인
- [ ] 팀원 1이 포함 자료와 공개 범위, 최종 Gate를 승인
- [ ] 최종 Git SHA와 동일한 소스·README·설치 명령 사용
- [ ] PDF/Native/Gold는 제출 허용 범위만 포함하고 원본 SHA-256 기록
- [ ] `CONFIG_DRAFT`, `ARCHIVED_NATIVE`, `LOCAL_REPLAY`, `LIVE_NATIVE`, `HUMAN_GOLD`를 분리 표기
- [ ] `.env`, 토큰, 개인키, 실제 기업·개인정보와 불필요 로그 제외
- [ ] License와 3자 자료의 재배포 조건 확인
- [ ] ZIP을 새 Windows 경로에서 해제해 파일 수, 상대 경로, SHA-256 검증
- [ ] README 명령을 깨끗한 가상환경에서 실행하고 종료코드 기록
- [ ] C001과 C013의 실제 영상 캡처가 원본 Job·Config·PDF SHA와 일치하는지 확인
- [ ] 영상 재생, 발표 PDF 열림, 링크 viewer 권한과 심사자 접근 확인
- [ ] 제출 승인 후 포털 접수 번호, 화면, KST 시각 보존

Manifest 항목은 `relative_path`, `bytes`, `sha256`, `evidence_tier`, `case_id`, `owner`, `share_approved`로 기록한다. 누락되거나 미승인인 필수 자료는 ZIP에 가상의 빈 파일로 채우지 않고 `BLOCKED`로 보고한다.
