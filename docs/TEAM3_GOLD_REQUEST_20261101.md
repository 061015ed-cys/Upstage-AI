# TEAM3_GOLD_REQUEST — PDF source and independently reviewed Gold

To: Team 3 (PDF/Human Gold owner). Existing `data/cases/SYN-C001..SYN-C020/extraction_gold.DRAFT.json` records are generator-origin DRAFT, **not source-verified Gold**.

Please provide per case:

- Original source PDFs (3 per case when applicable), unchanged bytes, filename, SHA-256, source/storage path and checksum method; PDF generation versions when relevant. Compare embedded case manifests to original file bytes.
- Stable `case_id`, `document_id`, `document_type`, PO, supplier, SKU, receipt, quantity/unit, original/revised ETA, quotation quantity/arrival/cost/currency and all applicable multiple-row/partial-receipt details.
- Evidence trace for each gold field: source PDF SHA, document ID, page number, exact source text/span or visual location when available, reviewer decision and ambiguity/nil/exclusion status. Do not invent unsupported values.
- Human reviewer identity/role, review date, reviewed Gold version, exact file SHA, double-review/adjudication of ambiguous fields if performed.
- Proper distinction of literal null, missing field, empty string, string "null", empty list and numerical zero.
- C001 full positive example; C013 PO1 vs PO999 expected reject; C017 original Korean-date expression plus justified or unresolvable ISO normalization; C008 R1=40/R2=60 and R2-only notice.
- Complete 20-case table of labels: document class, field support/ambiguity, expected safe block, human review status and excluded comparison items.

Return three categories distinctly: `DRAFT`, `HUMAN_VERIFIED_GOLD`, `NOT_VERIFIED`. No accuracy metric should include non-human-verified fields. The QA code and Studio generated outputs must not be edited to match Gold.

## 3차 통합 후보와 Gold 검수 상태

QA PR #4는 C001 보관 Native, C013·C017·C008 DRAFT fixture를 팀원 2 엔진과 QA 참조 계산기로 실제 회귀 검증했습니다. 결과 315 QA/504 전체 Python PASS는 **PDF 추출 정확도 검증이 아닙니다**. C013 PO999 차단, C017 한글 날짜 근거 여부, C008 R1/R2 분리 배분을 독립적으로 정확도 측정할 수 있도록 원본 3 PDF SHA, field-level page/evidence, human review/version/date/adjudication status를 사례별로 전달해 주세요. 현재 Human Gold Gate는 BLOCKED입니다.


## 4차 Human Gold 인계 — 실측 증거 분리

B0-C001 신규 Studio 실행은 파일 3개가 서로 다른 Job에 분리되어, 단일 C001 Extract/Normalize의 정확도를 평가할 수 없습니다. 기존 C001/C013/C017/C008의 Python DRAFT 회귀 결과는 PDF 원문 인식 정확도나 사람이 확정한 Gold가 아닙니다.
현재 DRAFT 파일의 human_reviewed:false를 유지하고, **별도 버전의 Human-reviewed Gold**에 (1) Case ID와 원본 PDF 파일명/버전/SHA-256, (2) 문서 페이지/필드, (3) 사람이 원문을 읽고 확인한 정답값/원문 표현, (4) 검수자/검수 일시/검수 버전, (5) 모호·제외 필드 및 사유, (6) 변경 이력을 기록해 주세요. C013의 PO1 vs PO999, C017 한국어 날짜의 원문, C008 R1/R2 receipt 분리와 C001 견적 수량·금액을 우선 검수해 주세요. 같은 Case ID만으로 서로 다른 PDF 버전을 동일 Gold로 묶지 마세요.
Human Gold 검수가 완료되기 전 성능 향상률·정확도 수치와 release PASS를 주장할 수 없습니다.
