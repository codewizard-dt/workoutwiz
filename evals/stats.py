#!/usr/bin/env python3
"""
Eval stats viewer for workout-wiz.
Reads persisted run results from evals/results/ and shows latest pass rates
and historical trends per suite.

Usage:
    backend/.venv/bin/python evals/stats.py
"""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def load_runs() -> dict[str, list[dict]]:
    runs = defaultdict(list)
    if not RESULTS_DIR.exists():
        return runs
    for f in sorted(RESULTS_DIR.glob("*.json")):
        if f.stem.endswith("-latest"):
            continue
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        runs[data.get("suite", "unknown")].append(data)
    return runs


def fmt_time(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return iso or "?"


def sparkline(pcts: list[float]) -> str:
    bars = "▁▂▃▄▅▆▇█"
    if not pcts:
        return ""
    out = ""
    for p in pcts:
        idx = min(len(bars) - 1, int(p / 100 * (len(bars) - 1)))
        out += bars[idx]
    return out


def main() -> int:
    runs = load_runs()
    if not runs:
        print("No eval runs recorded yet. Run: make eval-golden")
        return 0

    total_runs = sum(len(v) for v in runs.values())
    print(f"\n{'='*60}")
    print(f"  workout-wiz eval stats — {total_runs} run(s) recorded")
    print(f"{'='*60}\n")

    for suite in ["golden", "scenarios", "replays"]:
        suite_runs = runs.get(suite, [])
        if not suite_runs:
            continue
        suite_runs.sort(key=lambda r: r.get("started_at", ""))
        latest = suite_runs[-1]
        s = latest.get("summary", {})
        passed = s.get("passed", 0)
        total = s.get("total", 0)
        pct = s.get("pass_pct", 0)
        print(f"  {suite.upper()}")
        print(f"    Latest: {passed}/{total} passed ({pct}%) — {fmt_time(latest.get('started_at',''))}")
        trend = [r.get("summary", {}).get("pass_pct", 0) for r in suite_runs[-20:]]
        print(f"    Trend ({len(trend)} runs): {sparkline(trend)} {trend[0]}%→{trend[-1]}%")
        failing = [c["id"] for c in latest.get("cases", []) if not c.get("passed")]
        if failing:
            print(f"    Failing now: {', '.join(failing)}")
        print()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
