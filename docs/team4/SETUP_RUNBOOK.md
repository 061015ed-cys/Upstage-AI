# LeadTime Guardian 재현 및 장애 대응

기준: `061015ed-cys/Upstage-AI` main `575745bd8c6a8f00627197de6e6bb8530bcec6bb`, Python 3.11 이상. 로컬 실행은 Studio 신규 실행 또는 Release 승인을 뜻하지 않는다.

## 설치와 오프라인 확인

```powershell
git clone https://github.com/061015ed-cys/Upstage-AI.git
Set-Location Upstage-AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-validation.txt
.\.venv\Scripts\python.exe scripts/run_demo.py
.\.venv\Scripts\python.exe scripts/run_portfolio_demo.py
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts/qa_archive_check.py --root .
.\.venv\Scripts\python.exe scripts/qa_gate_check.py --root .
```

PowerShell에서 가상환경 활성화는 필수가 아니다. 모든 명령을 저장소 루트에서 실행한다. Linux/macOS는 `.venv/bin/python`을 사용한다. `requirements-validation.txt`가 엔진, Independent QA, 팀원 3 도구와 테스트 의존성을 설치한다. Windows 기본 cp949 환경에서는 한 테스트가 UTF-8 보고서를 기본 인코딩으로 읽어 실패할 수 있으므로 CI와 동일하게 `PYTHONUTF8=1`을 지정한다.

보관된 C002~C020 합성 PDF 인벤토리를 복원할 때만 `tar -xJf data/cases/SYN-C002-C020_DRAFT_PDFs.tar.xz`를 사용한다. C001 원본은 다시 생성하지 않는다. 복원 전후 원본 SHA는 `python -m qa.inventory --root . --out <검수용 출력 폴더>`로 확인한다. 인벤토리 PASS는 사람 검수 Gold를 뜻하지 않는다.

## Studio 경로

`scripts/run_studio_agent.py --help`와 `docs/AGENTS_API_RUNNER.md`를 참고한다. `--preflight`는 파일 및 환경 점검만 수행하고 네트워크 요청과 Studio Job 실행은 0이다. 실제 실행에는 팀원 1·2의 승인, Agent/Config ID, 로컬 환경 변수 `UPSTAGE_API_KEY`, 출력 경로가 필요하다. 키 값을 문서·인자·로그·영상에 기록하지 않는다. 현재 승인 전 신규 유료 Job 실행은 BLOCKED.

실제 E2E 인계에는 동일 케이스 PDF 3개 원본 SHA, upload receipt/file ID, Studio Agent/Config/Version, 단일 Job 및 Step ID, raw Native, Python V6 출력/Sidecar, IndependentQA Input/Report, Cross-Agent 판정, 팀원 3의 페이지별 Human Gold를 각각 원본 바이트 SHA와 함께 전달받는다. 설정 Draft와 보관 V4 결과를 신규 V6 실행으로 표기하지 않는다.

## 장애 대응

| 증상 | 확인과 복구 |
| --- | --- |
| `ModuleNotFoundError` | 저장소 루트와 `.venv` Python 사용 여부, validation 설치 종료코드 확인 |
| PDF 파일 없음 | 압축 보관 57개 복원 여부 확인. C001 파일은 재생성하지 않고 원본을 다시 받음 |
| API 키/권한 없음 | 오프라인 경로로만 검수. 담당자에게 접근 권한 요청 |
| Studio Job 실패/타임아웃 | 원 Job/Step ID와 원본 응답 보존. 자동 재실행 금지, 팀원 2에게 인계 |
| SHA 불일치 | 출처 연결 중단. PDF/Native/Gold를 보정하지 않고 원본 제공자에게 재확인 |
| QA 또는 Gold 없음 | `BLOCKED`/`NOT_VERIFIED` 유지. 오프라인 결과를 실측으로 승격하지 않음 |

지원 범위: 로컬 CLI, Python 3.11 이상. Windows Python 3.12.10 검수 결과는 팀원 4 인계 보고에 기록한다. License 및 3자 자료의 대외 배포 권한은 별도 확인 전 미확정이다.
