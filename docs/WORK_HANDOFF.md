# Chrome Work checkpoint - 2026-10-30 KST (latest, supersedes historical status below)

**User requested a preservation checkpoint due to remaining usage. Stop expanding features.**

## Saved Studio workflow and actual C001 success

- Repository/branch/PR remain `dohun3540-crypto/leadtime-guardian-agent`, `feat/specs-data-engine-20261029`, PR #11. No main merge or force push.
- Starting HEAD confirmed **0d6c31d154439b3a7d5a582d0d32787a04d933af**. The final checkpoint SHA is the current PR HEAD; this file cannot contain its own SHA.
- Authenticated Studio account and workspace were visibly verified. Existing Workflow 1 was renamed **LeadTime Guardian - B+C3 V1**.
- Correct observed Agent ID: **`agt_bXRXFSAgFmBayPjZF7VqRQ`**.
- Previously supplied `agt_bXRXFSAqFmBayPjZF7VgRQ` is a different identifier (two characters differ). Do not reuse it. It likely explains the prior 404; no deleted workflow is assumed.
- Saved **config version 4**, **`cfg_SZi6qfyZ6XFoNszpXQK5xQ`**.
- Verified URL: https://studio.upstage.ai/agents/agt_bXRXFSAgFmBayPjZF7VqRQ?configVer=4
- Actual native export: **`configs/studio_native/config_v4.export.json`**. This is an actual Studio download; prior design JSON is not.
- Actual topology: Parse -> file-boundary split/Classify -> 4 document-type Extract schemas -> MergeDocuments -> NormalizeDocuments Instruct. Strict matching/validation runs in Python. Native Match/Validate nodes were not configured.
- Studio Extract supports single field types; nullable JSON-schema unions were not usable in its UI. Intermediate quotation data is a one-row table, converted by Instruct to the existing normalized quote object. Studio removes primitive-array warnings from Extract; Instruct generates the final warnings list. No arithmetic is performed by the prompt.
- Existing original C001 PDFs were uploaded together as **one 3-page case**. They were not regenerated or modified.
- Actual job **`job_gPmEYKzuJdBA6BmKhVnujs`**, final step **`63f6a860-7c86-5036-b32d-6eae38ca7677`**. It completed.
- Actual output, step downloads, screenshot, hashes and analysis: **`data/results/studio_runs/C001_20261030_v4/`**. See its README and `execution_record.json`.
- Real extracted PO1 / A / R1 / 100 EA; original 2026-11-03, revised 2026-11-08; Q1/S1 capacity 60, arrival 2026-11-04, unit price 1000.00 KRW, shipping 500 KRW.
- Python using that unchanged prediction: **baseline 0 / revised 60 / additional 60 / KRW 60,500.00**, status OK. No expected/gold values substituted.
- Native extraction ZIP uses a `gold/` directory name. These are downloaded predictions, not human-reviewed labels. All gold labels remain DRAFT; `evidence_verified_against_pdf=false`. No extraction accuracy percentage is measured.

## Saved integration and validation

- `studio_integration.py`: observed native Instruct `{content: JSON-string, metadata: {job_execution_id, step_run_id, ...}}` support, with metadata/ambiguity checks and recursive gold-wrapper rejection. Complete and successfully used for C001.
- Existing `engine.py` and `studio_adapter.py` are unchanged.
- Added **6** envelope regression cases to `tests/test_studio_integration.py`.
- Official Upstage docs rechecked: https://console.upstage.ai/docs/agents/jobs and https://console.upstage.ai/api/agents/jobs/create-job . Official client remains OpenAI SDK at `https://api.upstage.ai/v2`; files use `purpose=user_data`, job POST `/responses`, GET `/responses/{id}`, include last/all.
- Added optional `--config-id`/`config_id` pinning: Upstage's extension is sent via SDK `extra_body`. Existing config-version metadata alone does not pin a server config. Live runner still has max_retries=0.
- Installed and exercised actual **OpenAI SDK 2.54.0 / httpx 0.28.1** over a loopback **HTTP server**, not just FakeClient. **13 new tests** cover multipart bytes, purpose, auth-header presence, one grouped job, config pin, polling, preserved extra step fields, 401/429/500, upload/submit failures, unknown submit timeout/no replay, deadline and history failure. Dummy credentials only; no auth values or exception bodies stored in artifacts.
- HTTP tests are labeled **sdk_http_mock** and do not represent live Upstage inference. Historical FakeClient **13** tests remain distinct. Actual Agents API network requests: **0**; no real API key is configured.
- Latest local **Python 3.12.14: pytest 80 passed; Ruff passed**. CI now installs `requirements-agents.txt` to run actual-SDK HTTP tests on Python 3.11 as well. GitHub CI must be checked against the final checkpoint commit.
- `docs/checkpoint_20261030/validation.json` records local checks. No browser credentials, cookies or API keys were copied or persisted.

## Unexecuted extension assets already generated - preserve, do not call measured results

- Before the user requested this checkpoint, `scripts/generate_synthetic_suite.py` generated **C002-C020: 57 new PDFs**, trusted base inputs, manifests and generator-authored `extraction_gold.DRAFT.json` files.
- Together with preserved C001, there are **20 cases / 60 source PDFs**. To minimize checkpoint writes, the **57 new PDF originals are preserved byte-for-byte in `data/cases/SYN-C002-C020_DRAFT_PDFs.tar.xz`**; trusted inputs, manifests and DRAFT labels are individual Git files. From the repository root run `tar -xJf data/cases/SYN-C002-C020_DRAFT_PDFs.tar.xz` to restore their expected `data/cases/SYN-C002/...` paths. No original C001 PDF is in that archive. `case_types.csv` records C001 tested and all extensions untested; human-label review false for all.
- The new PDFs were rendered for layout review, checked as one page each with case ID text; Korean font rendered. They are DRAFT generator assets, not human-approved truth. The generator requires `--font` pointing to a Korean TTF and refuses existing case directories; it never regenerates C001.
- C013 mismatch and C017 Korean date **have NOT been uploaded or run**. Partial receipts/multiple orders, duplicates/missing/contradictory docs and the rest of the suite also remain unexecuted.
- C008 explicitly prints receipt-specific quantities (40/60), and its notice affects R2 only. Aggregate unallocated PO quantities remain unsupported by the strict importer. Confirm against actual predictions before extending it.
- `configs/studio_workflow.import.json`, `studio_classify.import.json`, `studio_extraction.import.json` are development/import artifacts; only `configs/studio_native/config_v4.export.json` is the verified saved native configuration. Use that actual export to resume, not intermediate drafts.

## Resume in another Work session

1. Read the latest PR #11 HEAD and this top checkpoint section. Preserve newer remote changes; no reset/force push. Read `data/results/studio_runs/C001_20261030_v4/README.md` and `execution_record.json`.
2. Fetch the branch, install `requirements-agents.txt`, run pytest/Ruff. Review latest CI. PDF generation additionally requires ReportLab and a Korean TTF; existing PDFs need no generation.
3. Studio login sessions do not transfer through Git. Connect/authenticate safely, verify saved config v4 and correct Agent ID from the main Agent list. Use a secure authentication handoff; never ask for secrets in chat.
4. Run C013 first, require NEEDS_REVIEW without changing its extracted PO999 to PO1. Then C017 date normalization. Then C008 partial arrivals/multiple orders and duplicate/missing/contradictory document cases. Archive raw native outputs, job IDs/config IDs and Python results separately for every run.
5. Only actual prediction cases can be evaluated. Independently human-review DRAFT gold and source evidence. Do not call ZIP packaging labels gold, empty evidence arrays or schema success independent source verification.
6. Live Agents API still needs securely configured UPSTAGE_API_KEY and network access. Do not mint or expose credentials just to continue. The verified Studio Web path already works without an API key.
7. Preserve next changes to the same PR branch. Final LMS submission, real purchases and emails were not performed. LMS submission requires user review/approval.

---

# Historical Windows handoff (preserved for context; 0-run statements below are obsolete)

# LeadTime Guardian Agent — Chrome ChatGPT Work 인계

기준일: **2026-10-30 KST**. 새 기능 개발을 중단하고 현재 결과를 보존한 인계 문서다.
새 환경에서는 코드를 다시 작성하기 전에 이 문서와 현재 PR 브랜치를 읽는다.
이 문서가 과거 상태 보고서보다 우선한다. `docs/handoff/evidence/`의 보고서는 당시의 기록이다.

## 1. 인계 대상과 Git 기준

- 저장소: https://github.com/dohun3540-crypto/leadtime-guardian-agent
- 작업 브랜치: **`feat/specs-data-engine-20261029`**
- 검토 PR: https://github.com/dohun3540-crypto/leadtime-guardian-agent/pull/11
- 최종 기능 코드 커밋: **`19df3a6468074f9e2938c416812b2a59ba2df58f`**
- 위 커밋의 파일 tree: `8beabb7bfc3bf2b0d2b87d4aa2b7070d70cb8f08`
- 이 기능 코드 이후의 인계 커밋은 문서·검증 기록·증거·목록 저장만 수행한다.
  인계 문서가 자기 자신의 commit SHA를 포함할 수는 없으므로, **인계 문서까지 포함한
  최종 SHA는 PR #11의 HEAD 및 다운로드 패키지의 `WORK_HANDOFF_RECEIPT.json`에서 확인**한다.
- `main`에는 병합하지 않았다. 계속 이 브랜치와 PR에서 검토 가능하게 작업한다.

로컬 작업 당시 `feat/c001-studio-integration-20261030`에도 동일 내용의 보존 커밋들이 있다.
앞선 로컬 커밋은 GitHub 도구가 생성한 원격 커밋과 SHA가 다르지만 tree는 일치했다.
**다른 환경의 기준은 위 GitHub 브랜치**다. 로컬 보존 브랜치를 원격에 강제 Push하지 않는다.

## 2. 완료된 기능과 실제 검증 범위

| 항목 | 완료 내용 | 검증 한계 |
|---|---|---|
| B 계산 엔진 | 재고·입고·고객 주문 납기순 배분, 견적 공급량 공유 및 운임 1회 계산 | 실제 발주·메일 전송 없음 |
| C1 | 기존/변경 입고 일정의 주문별·전체 부족량과 추가 부족량 계산 | 로컬 합성 입력 검증 |
| C2 | PO/품목/날짜/수량 충돌, 누락, 중복, 모호한 입고 연결 차단 | 원본 PDF 기반 실예측 검증은 미완료 |
| C3 | 복수·부분 입고 및 복수 고객 주문 배분, 수량 중복 사용 방지 | 엔진 테스트 통과; Studio 통합 미실행 |
| C001 | 한·영 합성 PDF 3개, 신뢰 입력, 정답 초안, manifest, 기대 계산 | 정답은 사람 검수 전 DRAFT |
| 출력 연결 | 정규화 JSON·공식 응답 envelope 검증, 원본 파일/해시/버전 기록 | 실제 native UI export 형식 미관찰 |
| Agents 실행기 | PDF들을 한 job으로 제출, 응답·입력·단계 기록, 실패·시간초과 중단 | 모의 클라이언트 계약 테스트만 수행 |

기존 `engine.py`, `studio_adapter.py`를 새로 작성하거나 변경하지 않고 연결 계층을 추가했다.
C001 전용 엄격 importer는 합산된 PO 행을 여러 입고로 자동 배분하지 않는다.
그 경우 실제 응답 구조와 명시적인 연결 규격을 확인해 확장해야 한다.

오프라인 C001 결과: **기존 부족 0개 / 변경 후 60개 / 추가 60개 / 견적 60,500.00원**.
이는 `data/sample/portfolio_case.json`의 계산 결과이며 Studio 예측 결과가 아니다.

## 3. 파일 위치와 보존 상태

| 파일/디렉터리 | 용도 |
|---|---|
| `src/leadtime_guardian/engine.py`, `analysis.py` | 기존 B+C1+C3 및 단일 주문 계산 |
| `src/leadtime_guardian/studio_adapter.py` | 기존 입고 연결 Adapter |
| `src/leadtime_guardian/studio_integration.py` | C001 정규화 입력 검증·견적 연결·엔진 호출 |
| `src/leadtime_guardian/agents_api.py` | SDK 클라이언트를 주입받는 업로드·비동기 job·기록 계층 |
| `scripts/run_studio_agent.py` | 공식 SDK 생성 및 API 실행/네트워크 없는 사전 검사 |
| `scripts/analyze_studio_export.py` | 실제 출력 보관·정규화·기존 엔진 연결 |
| `scripts/generate_c001.py` | 기존 샘플에서 PDF 3개와 정답 후보 생성 |
| `scripts/run_demo.py`, `run_portfolio_demo.py` | 기존 오프라인 데모 |
| `configs/schemas/*.json` | 정규화 문서 및 계산 출력 계약 |
| `configs/studio_prompt_spec.v1.json` | 적용 전 프롬프트 설계; native Studio export 아님 |
| `data/sample/*.json` | 기존 합성 입력 |
| `data/cases/SYN-C001/*.pdf` | 발주서·납기 변경 통보서·대체 견적서 3개 |
| `data/cases/SYN-C001/trusted_base_case.json` | 재고 40, 주문 100, 원래 입고만 포함; 예측/견적은 비어 있음 |
| `data/cases/SYN-C001/extraction_gold.DRAFT.json` | 생성 원본에서 만든 정답 후보; 실예측 아님 |
| `data/cases/SYN-C001/expected_calculation.json` | 기대 계산; 실예측 아님 |
| `data/cases/SYN-C001/local_calculation.NOT_STUDIO.json` | 오프라인 계산 결과 |
| `data/cases/SYN-C001/manifest.json`, `pdf_asset_checks.NOT_STUDIO.json` | PDF 해시·페이지·필수 텍스트 확인 |
| `tests/test_analysis.py`, `test_engine.py` | 기존 20개 회귀 테스트 |
| `tests/test_studio_integration.py` | 추가 28개 정규화/파일 보관 계약 테스트 |
| `tests/test_agents_api.py` | 추가 13개 FakeClient 수송 계약 테스트 |
| `requirements-dev.txt` | editable package, pytest, Ruff, jsonschema |
| `requirements-integration.txt` | 위 개발 의존성 + PDF 생성용 ReportLab |
| `requirements-agents.txt` | 위 개발 의존성 + 선택 OpenAI SDK |
| `docs/AGENTS_API_RUNNER.md`, `C001_INTEGRATION.md` | 상세 실행법과 개발 이력 |
| `docs/AGENT_WORKFLOW.md`, `STUDIO_HANDOFF.md`, 기타 기존 문서 | 기존 설계·요구사항·제출 체크리스트 |
| `docs/handoff/pytest-local.txt`, `ruff-local.txt`, `validation-local.json` | 이번 인계를 위한 재실행 결과 |
| `docs/handoff/evidence/` | 로컬 보고서, 사전 검사 JSON, 공개 화면, PDF 미리보기·텍스트 |
| `docs/handoff/workspace_inventory.json` | 로컬 파일 전체 목록·해시·보존 방식 |

빌드 캐시, `.pyc`, `.git` 내부 파일은 실행 산출물이 아니므로 GitHub에 추가하지 않는다.
작업 중 만들어진 pytest 임시 결과와 예전 ZIP은 별도 로컬 체크포인트에 보존한다.
다른 환경에서 개발을 이어갈 필수 파일은 저장소에 포함한다.
목록의 SHA-256은 로컬 원본 바이트 기준이다. Git의 줄바꿈 정규화 때문에 Windows
텍스트의 바이트 해시가 다른 환경과 다를 수 있으며, 최종 원격 반영은 Git tree로 별도 검증한다.

## 4. 테스트 결과와 개발환경

이번 인계 재실행:

- Windows / Python **3.13.9** / pytest **8.4.2** / Ruff **0.12.0**.
- `python -m pytest -q --basetemp=../pytest-handoff-20261030-a`: **61 passed**.
- `python -m ruff check .`: **All checks passed!**
- 현재 소스를 쓰기 위해 해당 프로세스에만 `PYTHONPATH=src`를 지정했다.
- 앞선 GitHub Python **3.11.17** CI도 **61개·Ruff 통과**:
  https://github.com/dohun3540-crypto/leadtime-guardian-agent/actions/runs/41029327631
- 인계 커밋의 최종 CI는 PR Checks 및 최종 인계 영수증에서 확인한다.
- 앞선 개발 중 Ruff 버전 차이로 실패한 CI는 각각 수정 후 재실행해 통과했다.

이 숫자는 코드 테스트 수다. **Studio 업로드 0개, 실실행 0건, 실제 예측 JSON 0개**다.

## 5. 다른 환경에서 실행

Python 3.11 이상. 설치 환경에 맞는 Python 명령을 사용한다.

```bash
git clone --branch feat/specs-data-engine-20261029 https://github.com/dohun3540-crypto/leadtime-guardian-agent.git
cd leadtime-guardian-agent
git rev-parse HEAD
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python scripts/run_portfolio_demo.py
```

기존 체크아웃이면 먼저 변경을 보존하고 `git status`, 브랜치를 확인한다.
다른 작업을 덮어쓰는 reset/force push는 사용하지 않는다.
Windows 임시 폴더 권한 오류가 발생하면 새 작업용 `--basetemp`를 지정한다.

PDF는 이미 커밋돼 있으므로 재생성이 필요 없다. 재생성하려면
`requirements-integration.txt`를 설치하고 `scripts/generate_c001.py --font 한국어_TTF_경로`를 사용한다.
기본 폰트 `C:/Windows/Fonts/malgun.ttf`는 다른 운영체제에 존재하지 않을 수 있다.

API 사전 검사(네트워크 요청 없음):

```bash
python scripts/run_studio_agent.py --agent-id agt_bXRXFSAqFmBayPjZF7VgRQ --pdf data/cases/SYN-C001/SYN-C001_purchase_order.pdf data/cases/SYN-C001/SYN-C001_delivery_notice.pdf data/cases/SYN-C001/SYN-C001_quotation.pdf --preflight
```

실제 API 및 실제 출력 계산 명령은 [AGENTS_API_RUNNER.md](AGENTS_API_RUNNER.md)를 따른다.
새 출력 디렉터리를 사용하고 실제 job ID·설정/프롬프트 버전을 기록한다.

## 6. Studio 접근 문제

- 사용자 제공 Workflow 1 주소:
  `https://studio.upstage.ai/agents/agt_bXRXFSAqFmBayPjZF7VgRQ`.
- 로컬 Work 제어 브라우저에서는 해당 주소가 Studio 자체의 **404**를 반환했다.
  워크플로우 삭제/부재인지 계정 권한 문제인지는 확정하지 못했다.
- 기존 탭 이동/새로고침에서 `browser.user is unavailable` 오류도 있었다.
- 메인 페이지로 접근한 마지막 시도에서는 ‘로그인’, ‘지금 가입하기’가 표시됐고,
  계정·워크스페이스·최근 에이전트 목록이 보이지 않았다.
- Google 및 Upstage 인증 사이트 접근은 앞선 자동 승인 검토에서 차단된 이력이 있다.
  인증 정보를 읽거나 입력하지 않았으며 우회하지 않았다.
- 사용자가 다른 창에서 로그인했다고 알려도, 제어 중인 탭에서 계정 상태가
  확인된 것으로 간주하면 안 된다. 로그인 세션은 코드나 패키지로 이전하지 않는다.
- 같은 기존 URL로 반복 접속하지 않는다. Chrome Work에서는 메인 → 계정/워크스페이스
  확인 → 최근 에이전트의 Workflow 1 클릭 → 실제 편집 URL 확인 순서를 따른다.
  기존 작업에 접근할 수 없고 생성 권한이 있으면 새 워크플로우로 전환할 수 있다.

## 7. API·SDK·모의 테스트 상태

- 공식 endpoint 및 SDK 호출 코드는 구현돼 있다. `max_retries=0`이며
  제출 시간초과는 서버가 작업을 받았을 수 있으므로 자동 재제출하지 않는다.
- API 키와 선택 SDK가 로컬 Python에 없었다. 사전 검사와 자격증명 부재 시
  중단 경로만 직접 실행했고, 실제 외부 API 요청은 **0건**이다.
- `tests/test_agents_api.py`는 **FakeClient**를 주입한다. 실제 SDK를 import하거나
  HTTP 요청을 생성하는 테스트, HTTP 모의 서버 테스트는 **아직 없다**.
- 실제 SDK + 모의 HTTP 서버 검증은 계획을 알린 단계에서 사용자 인계 지시로
  중단했다. SDK 설치·새 코드·새 테스트 파일은 만들어지지 않았다.
- `evidence_verified_against_pdf=false`를 유지한다. 정답 초안이나 기대값을
  Studio 실예측으로 대입하거나 테스트 정확도라고 보고하지 않는다.
- 비밀번호, API 키, 쿠키, OAuth 토큰은 GitHub/ZIP/채팅으로 전달하지 않는다.
  API 사용이 필요할 때 새 환경의 비밀 저장 기능 또는 로컬 환경변수로 설정한다.

## 8. 미완료와 다음 개발 순서

1. Chrome Work의 연결된 브라우저에서 실제 계정·워크스페이스와 편집 권한 확인.
2. 접근 가능한 기존 또는 신규 workflow에 Parse → Classify(케이스 내 파일 분할)
   → 유형별 Extract → Merge/Match → Validate/Instruct를 실제 UI 제약에 맞춰 구성.
3. C001 PDF 3개를 한 케이스로 업로드·실행하고 원본 예측 JSON 및 native 설정 export 저장.
4. 실제 응답 구조를 확인해 필요한 Adapter 매핑만 수정하고 기존 엔진으로 0/60/60,
   60,500원을 검증. 오류가 나면 정답에 맞춰 값을 덮어쓰지 말고 차단 원인을 수정.
5. PDF 원문 근거 및 정답 초안을 사람이 검수. C013 PO 불일치, C017 한국어 날짜,
   부분 입고/복수 주문 예외를 실제 실행. C001 성공 후에만 20케이스/60PDF 확대.
6. 실제 SDK/모의 HTTP 테스트, 오류 처리·평가 스크립트 보강. 기존 엔진 재작성은 피한다.
7. 실측 보고서·영상·발표자료·LMS 규격 확인. 실제 구매·메일 발송은 실행하지 않는다.
   LMS 최종 제출은 사용자 검토·명시적 승인 후에만 수행한다.

## 9. Chrome Work에서 바로 시작할 첫 작업

**GitHub PR #11의 최신 브랜치를 읽고 `docs/WORK_HANDOFF.md`와 검증 기록을 확인한다.**
현재 checkout SHA를 기록하고 61개 테스트·Ruff를 재현한다. 그다음 Studio 메인에서
연결된 계정과 워크스페이스가 실제로 표시되는지 확인한다. 저장된 코드·PDF는 그대로
사용하고, 404 URL 반복 접속이나 워크플로우가 이미 구성됐다는 가정으로 시작하지 않는다.
