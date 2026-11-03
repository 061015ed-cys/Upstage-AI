"""Offline demonstration; never label these local results as Studio predictions."""
import json
from pathlib import Path

from leadtime_guardian.engine import analyze_portfolio

if __name__ == "__main__":
    source = Path(__file__).resolve().parents[1] / "data/sample/portfolio_case.json"
    result = analyze_portfolio(json.loads(source.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
