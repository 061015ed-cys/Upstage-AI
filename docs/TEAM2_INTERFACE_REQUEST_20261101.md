# TEAM2_INTERFACE_REQUEST — operational Studio and Python boundary

To: Team 2 (Python engine / Studio Adapter owner). This is a technical handoff request, **not a request to change ownership**.

Please return for C001 first, then C013/C017/C008:

1. Latest original repository PR #12 HEAD Git SHA and CI URL; whether the engine/Adapter changed since `e9b9992b593a42d427ff1bbadeb9a9866ca593bd`.
2. Actual **saved** operational Studio Agent, Config ID, saved version, Step/Job IDs and timestamps. Distinguish user-supplied `studio.workflow-config-draft` v5 from real published/used job Config and from V4 archived C001.
3. Original unchanged operating Native JSON bytes + SHA-256, `studio-provenance/1` sidecar, Python input documents, execution status, output analysis JSON, validation issues and Git SHA. If output is a replay, label `ARCHIVED_REPLAY`, not new LIVE.
4. Operating job's actual PDF upload receipt: `{case_id,files:[{filename,file_id,sha256,hash_origin}]}`, complete 3-file set, SHA from original bytes, plus traceable job-file linkage. Actual independent QA Job uses different file IDs; compare original PDF SHA/case_id, not Job ID equality.
5. Confirm that untrusted Studio document inputs always pass `studio_integration.validate_documents`, not a bypass through `engine.analyze_portfolio`; clarify where document quantity/receipt/PO validation executes. Operative `studio_adapter.apply_studio_extractions` and `strict_json` versions should be documented.
6. Review v5 Extract schema: selected `po_id`/`supplier_id`/date descriptions permit null, but the schema declares only primitive types. Please fix under Studio ownership only after backing up Config and report before/after diff and actual saved Config/Job run.
7. Document the C008 R1=40/R2=60 receipt-level logic, C013 PO999 fail-closed, C017 Korean-date source-evidence handling. Return validated results including nulls/flags, not manually repaired predicted values.
8. Source-PDF verification status and Human Gold remain distinct; `evidence_verified_against_pdf=false` in a sidecar is not a defect and does not prove Python QA PASS.

Do not merge or change a running production workflow as part of this request. Provide explicit UNAVAILABLE/BLOCKED for missing files.

## 3차 실측 통합 후속 (추가)

별도 QA 사본 Draft PR #4에서 귀하의 PR #12 `e9b9992b` **원본 6개 핵심 Python Blob을 변경 없이 보존**한 상태로 QA 코드·테스트를 실제 결합했습니다. 315 QA/504 전체 Python 테스트와 Ruff가 성공했습니다(동일 HEAD `bdcdac48`). 이는 Studio 실측이 아닌 코드 호환성 PASS입니다.

이번에 귀하께 추가로 요청할 핵심 항목: (1) 팀원 2의 최신 Python 엔진/Adapter 브랜치가 `e9b9992b` 이후 변경되면 정확한 신규 HEAD·함수 계약·Blob SHA, (2) 실측 operating V5 Agent/Config/Job/Step과 해당 Native **원본 바이트**, 원본 source 3 PDF의 실제 SHA와 upload file ID, (3) 실행된 Python 분석 JSON, `studio-provenance/1` sidecar, Git SHA 및 실제 실행 결과가 보관 리플레이인지 신규 실행인지, (4) 외부 입력이 `analyze_studio_documents`의 엄격한 Match/Validate를 거치지 않고 `engine.analyze_portfolio`로 직접 통과하는 엔트리포인트가 있는지, (5) Extract nullable schema에 대한 실제 **saved** Config 검증 및 팀원 2 승인 변경 diff. 데이터가 없다면 NOT_VERIFIED로 반환하세요. 운영 저장소 수정·PR merge는 요청하지 않습니다.


## 4차 신규 요청 — B0 실행 단위 오류 및 실제 Provenance 수신

QA Sandbox의 신규 B0-C001에서 3 PDF가 독립 Job 3개로 완료돼 단일 통합 기준선이 무효였습니다. 팀원2의 PR#12 Python V6 구현은 변경하지 않았습니다.
운영 Python의 최신 native + actual Python output + studio-provenance/1 Sidecar의 원본 바이트, 실제 Job ID, Step/Config version, Git SHA를 구분하여 보존해 주세요. 이때 original Native SHA는 Sidecar export_sha256과 일치해야 하며, 원본 Native metadata.source_files의 (file_id, file_name)은 운영 PDF upload receipt의 (file_id, filename)과 1:1로 일치해야 합니다.
운영 Studio가 C001 발주서·납기통보서·견적서를 한 Job으로 처리했는지 먼저 확인하고, 파일별 Job이어서 분리된 경우 별도 출처로 유지해 주세요. 업로드 PDF 각각의 실제 바이트 SHA-256 및 PDF 파일 ID, saved Config/Step을 요청합니다. QA Job과 운영 Job의 ID가 다르다는 것만으로 출처 mismatch라고 판단하지 않습니다.
외부에서 검증되지 않은 Native가 analyze_portfolio로 직접 전달되는 공개 경로가 있다면 그 엔트리포인트/재현 입력을 반환해 주세요. 기존 안전 경계 analyze_studio_documents를 우회하는지 확인하는 목적이며 운영 코드를 무단 수정하라는 요청이 아닙니다. 새로운 실측이 없다면 NOT_VERIFIED.
