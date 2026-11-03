# Upstage Studio 연동 계획

- 교육(11/02)과 실제 Studio 권한 확보 후 노드 구현.
- Parse → Classify → Extract → Instruct 흐름을 기본 가설로 사용하되, Studio에서 지원하는 조건/노드/입출력 제약에 맞게 수정.
- Agent 워크플로우 설정 JSON은 실제 Studio에서 내보내어 제출.
- 문서별 추출 결과(JSON)와 정답지를 같은 필드로 평가.
- Python 엔진과의 연결은 공식 Agents API의 실제 요청/응답 확인 후 구현.
- 인증정보는 로컬 .env / GitHub Secrets에만 저장.
- API 오류/시간초과/누락 입력 시 needs_review로 처리하고 오프라인 데모용 fallback은 반드시 구분하여 표기.
