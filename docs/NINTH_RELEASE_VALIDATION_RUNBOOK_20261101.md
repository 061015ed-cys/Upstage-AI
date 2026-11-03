# LeadTime Guardian — 9차 원본 증거 수신 및 릴리스 검증 Runbook

2026-11-01. 이 문서는 GitHub 독립 QA 측의 재현 가능한 로컬 절차이다. 공식 대회 제출 규격을 대변하지 않는다. 실제 Studio Native·PDF·Gold가 오기 전에는 Release=BLOCKED이다.

## 1. 기준선 고정

- QA 복사본: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy
- QA 9차 Draft PR #10: https://github.com/dohun3540-crypto/leadtime-guardian-agent.copy/pull/10
- 부모 PR #9 SHA: b4c01ecddbd00bc33bca1ae8c1735ac768eea20f
- 이 문서를 포함한 현재 PR #10의 **최종 HEAD SHA**와 해당 SHA의 GitHub Actions를 다시 조회해야 한다. 테스트 로그의 중간 SHA를 최종 SHA 성공이라고 기록하지 않는다.
- 의존성·테스트 실행 명령은 기존 GitHub Actions workflow를 따른다. Python 3.11 가상환경에서 requirements-agents.txt 설치를 확인한다.
- Team2 V6 핵심 모듈, 운영 PR#11/12, 기존 QA PR#4~#9, 원본 PDF/XLSX/Native/Gold는 변경하지 않는다.

## 2. 필요한 원본 종류 및 최소 폴더 구조

실제 제출에 필요한 자료와 GitHub 검증기가 필요로 하는 원본 목록은 반드시 별도 구분한다. 아래는 **GitHub QA 자체 검증용 목록**이며 공식 대회 제출물 목록은 아니다.

- Release evidence manifest: leadtime-release-evidence/v1, Case C001, 운영 Job 및 Saved Config 명시.
- Stage manifest: leadtime-stage-intake/v1, 같은 Case·운영 Job·Config ID/Version, 각 원본 Stage의 SHA256/Step ID.
- Operational Native raw JSON: Normalize 3문서의 실제 저장 결과.
- Extract 발주서/납기통보서/견적서 원본 JSON 3개(원본 개별 Step ID), MergeDocuments 원본 JSON, NormalizeDocuments 원본 JSON.
- IndependentQA 실제 INPUT raw JSON과 QA Report raw JSON (QA Sandbox Job과 운영 Job은 다를 수 있다).
- Original source PDF 3개와 출처 SHA 및 운영/QA Upload Receipt.
- Team2 원본 Python V6 Provenance Sidecar, 본 실행 결과.
- Team3 Human-reviewed Gold: PDF 근거 페이지·reviewer·검토 상태.
- 실제 E1 Job이 생성된 경우에만 E1의 독립 Job/Config/Step, 원본 PDF SHA, Normalize 및 QA 원본, Config Diff.

모든 원본은 비공개 로컬 폴더에 보관하고 GitHub에 업로드하지 않는다. PDF byte SHA는 실제 파일을 읽어서 계산한다. 동일한 PDF 이름과 self-reported SHA 값만으로 Upstage 서비스의 업로드 사실을 인증하지 않는다.

## 3. Release manifest 작성

예시 파일명: release_evidence.json. 아래 JSON의 경로는 설명용 예시이며 **실제 파일이 생성되었거나 확보됐다는 증거가 아니다**. 없는 항목은 해당 sources key를 누락하면 된다. 이전 GPT가 쓴 가짜 Native/Gold는 입력하지 않는다.

    {
      "schema_version": "leadtime-release-evidence/v1",
      "case_id": "C001",
      "operational_job_id": "job_NCik8shwrgM93PDnNNYukT",
      "config_id": "cfg_X2xXakDtmDTHh2RoqVysvL",
      "config_version": 1,
      "sources": {
        "stage_manifest": "stage_manifest.json",
        "operational_native": "operational_native_original.json",
        "qa_native": "qa_native_original.json",
        "qa_report": "qa_report_original.json",
        "team2_provenance": "team2_sidecar.json",
        "operational_pdf_receipt": "operational_upload_receipt.json",
        "qa_pdf_receipt": "qa_upload_receipt.json",
        "human_gold": "team3_human_reviewed_gold.json",
        "source_pdfs": {
          "purchase_order": "SYN-C001_purchase_order.pdf",
          "delivery_notice": "SYN-C001_delivery_notice.pdf",
          "quotation": "SYN-C001_quotation.pdf"
        }
      }
    }

파일 해시를 신고하려면 sources의 항목 값을 {"path":"...","sha256":"실제로 계산한 64자리 hex"} 형태로 바꾼다. 선언된 SHA와 실제 원본 바이트가 다르면 FAIL. 상대 경로는 release manifest가 놓인 폴더 내부여야 한다. 폴더 밖으로 향하는 심볼릭 링크도 FAIL. manifest가 없으면 FAIL + 필요한 원본/작업을 안내한다.

## 4. 원본 수신 Preflight

    python scripts/qa_release_evidence_check.py --manifest /private/evidence/release_evidence.json --json-report /private/results/missing_evidence.json --markdown-report /private/results/missing_evidence.md

표시 필드: status, checked_inputs, missing_inputs, invalid_inputs, evidence_sha256, blocking_issues, next_required_action, source_authentication_status, python_safety_status, local_stage_status, release_authorized.
- 증거 파일 부족: BLOCKED, 종료코드 2, missing_inputs에 원본의 **정확한 명칭** 포함.
- 형식·해시·경로·Case/Job/Config 충돌: FAIL, 종료코드 1.
- 모든 로컬 파일이 존재하는 경우에도 source_authentication_status=NOT_AUTHENTICATED, release_authorized=false. 이 inventory 도구는 Python 계산·Studio 실행을 하지 않는다.
- 두 결과 보고서는 새 파일로만 생성한다. --json-report 또는 --markdown-report가 이미 존재하는 경로를 가리키면 FAIL로 차단하며 원본 Manifest/PDF/Native 바이트를 덮어쓰지 않는다. 결과를 다시 실행하려면 새로운 보고서 파일명을 지정한다.

## 5. 기존 Stage/안전 검증기 순서대로 실행

원본이 확보된 후 반드시 다음 순서로 실행한다.

    python scripts/qa_stage_intake_check.py --manifest /private/evidence/stage_manifest.json

    python scripts/qa_combined_e2e_check.py --operational-native /private/evidence/operational_native_original.json --trusted-base data/cases/SYN-C001/trusted_base_case.json --schema configs/schemas/document_extraction.schema.json --operational-job-id job_NCik8shwrgM93PDnNNYukT --case-id C001 --github-sha CURRENT_TESTED_GIT_SHA --stage-intake-manifest /private/evidence/stage_manifest.json --execution-kind NEW_LIVE_STUDIO --qa-native /private/evidence/qa_native_original.json --qa-report /private/evidence/qa_report_original.json --qa-agent-id ACTUAL_QA_AGENT_ID --qa-config-id ACTUAL_QA_CONFIG_ID --qa-config-version ACTUAL_QA_CONFIG_VERSION --team2-provenance /private/evidence/team2_sidecar.json --qa-pdf-receipt /private/evidence/qa_upload_receipt.json --operational-pdf-receipt /private/evidence/operational_upload_receipt.json --pdf-root /private/evidence/

직접 원본이 없는 경우에는 위의 예시 경로를 실행하거나 가짜 파일로 채우지 않는다. 9차 NEW_LIVE 경계는 Stage + QA Native/Report + Team2 Sidecar + 양쪽 Upload Receipt + PDF Root + QA Config 식별자가 빠지면 Python V6 자체를 NOT_RUN으로 보존한다. 모든 Stage가 존재하지 않는 경우도 실제 Live 계산을 실행하지 않는다.

각 CLI의 exit code 2는 **BLOCKED**를 의미하고 Live 검증 PASS가 아니다. Stage raw local SHA 비교는 바이트 무결성의 로컬 확인일 뿐 Studio 제공자 인증은 별도다. Archive C001 또는 Synthetic fixture를 NEW_LIVE 결과로 표기하지 않는다.

## 6. E1 조건이 충족되는 경우에만 비교

    python scripts/qa_b0_e1_compare_check.py --b0 /private/evidence/B0_manifest.json --e1 /private/evidence/E1_manifest.json --b0-normalize /private/evidence/B0_normalize_original.json --e1-normalize /private/evidence/E1_normalize_original.json

각 Normalize 원본 JSON의 바이트 SHA와 Step Manifest SHA를 확인한 뒤 값과 JSON 타입 차이를 검토한다. 동일 원본 PDF 실제 바이트 SHA, 각 Job·Saved Config·Step ID, E1 Config Diff와 Human-reviewed Gold가 없으면 개선 판정은 NOT_MEASURED이다. Empty String 변화만으로 개선을 주장하지 않는다.

## 7. 팀별 최종 인계

- Studio: B0 NCik Job과 Config v1 그대로 보존, Extract 3종/Merge/Normalize/IndependentQA actual INPUT·Report 및 운영/QA PDF Upload Receipt 원본 회수. 재실행하지 않는다.
- Team2: 기존 엔진 무수정. 신규 Job 실행 sidecar, 원본 Native SHA, Python Safety 산출물 제공.
- Team3: 원본 PDF SHA와 페이지에 대응하는 Human-reviewed Gold 검토 완료.
- Team1 QA: Release inventory → Stage → Python V6/IndependentQA → Cross-Agent/Provenance → E1 비교 → Human Gold 확인 → 명시적 Release 결재. 코드 CI 성공과 실제 제출 승인은 별개.

## 8. 실측 확보 전 릴리스 상태

QA code/local CI PASS는 실측 인증이 아니다. 2026-11-01 기준 신규 NCik Native 3문서, QA actual Input/Report, PDF SHA Upload Receipt, Team2 Live Sidecar, Human-reviewed Gold, E1 actual 비교 결과가 확보되지 않았으므로 모든 관련 Gate BLOCKED/NOT_VERIFIED. Overall Release BLOCKED.
