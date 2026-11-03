"""Offline demonstration: no Upstage API key required."""
import json
from pathlib import Path

from leadtime_guardian.analysis import analyze_case


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "data/sample/demo_case.json"
    case = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(analyze_case(case), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
