# Ground Rules
- Main stays stable. Work in feature branches; PR review required where possible. Commit tags feat/fix/docs/data/test/chore.
- Daily status: completed, next, blockers, owner and due date. Escalate blocked issues the same day.
- Python 3.11, `pytest -q`, `ruff check .`; include tests and samples in each implementation PR.
- Shared JSON keys, units EA, KRW Decimal, ISO dates and IDs are API contracts. Amend only with a documented PR and test changes.
- Generated synthetic labels are **draft until manually source-checked**. Keep Studio predictions separate from gold; include model and run IDs in evaluation.
- No real customer records, supplier contracts, API secrets or .env files in repo. External dataset redistribution requires confirmed license.
- No autonomous purchase, no outbound email without human authorization; this MVP does not integrate a sending endpoint.
- Prioritize mandatory competition artifacts, correct calculations, traceable evidence, and reproducibility before UI.
