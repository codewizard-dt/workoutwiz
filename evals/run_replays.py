#!/usr/bin/env python3
"""
Replay fixture validator for workout-wiz.
Loads saved JSON fixtures from evals/replays/fixtures/ and checks
ground_truth assertions against the captured response — no live API calls.

Usage:
    python3 evals/run_replays.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "replays" / "fixtures"
RESULTS_DIR = Path(__file__).parent / "results"


def save_results(run: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / f"replays-{ts}.json"
    out.write_text(json.dumps(run, indent=2))
    (RESULTS_DIR / "replays-latest.json").write_text(json.dumps(run, indent=2))
    return out


def check_fixture(path: Path) -> tuple[bool, list[str]]:
    with open(path) as f:
        data = json.load(f)

    ground_truth = data.get("ground_truth", {})
    response = data.get("response", {})
    reply = response.get("reply", "")
    actual_route = response.get("route", "")

    failures = []

    # Route check
    expected_route = ground_truth.get("expected_route")
    if expected_route and actual_route != expected_route:
        failures.append(f"route: expected '{expected_route}', got '{actual_route}'")

    # must_contain
    for term in ground_truth.get("must_contain", []):
        if term.lower() not in reply.lower():
            failures.append(f"must_contain '{term}' absent from reply")

    # must_not_contain
    for term in ground_truth.get("must_not_contain", []):
        if term.lower() in reply.lower():
            failures.append(f"must_not_contain '{term}' found in reply")

    return len(failures) == 0, failures


def main() -> int:
    if not FIXTURES_DIR.exists():
        print(f"No fixtures directory at {FIXTURES_DIR}")
        return 0

    fixtures = sorted(FIXTURES_DIR.glob("*.json"))
    if not fixtures:
        print("No fixture files found.")
        return 0

    print(f"Validating {len(fixtures)} fixtures from {FIXTURES_DIR}\n")
    passed = 0
    failed = 0
    case_results = []
    started_at = datetime.now(timezone.utc).isoformat()

    for path in fixtures:
        print(f"  [{path.stem}]", end=" ", flush=True)
        ok, failures = check_fixture(path)
        if ok:
            print("PASS")
            passed += 1
        else:
            print("FAIL")
            for f in failures:
                print(f"    x {f}")
            failed += 1
        case_results.append({"id": path.stem, "passed": ok, "failures": failures})

    total = len(fixtures)
    pct = round(passed / total * 100) if total else 0

    print(f"\nResults: {passed} passed, {failed} failed out of {total}")

    run = {
        "suite": "replays",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "summary": {"total": total, "passed": passed, "failed": failed, "pass_pct": pct},
        "cases": case_results,
    }
    out = save_results(run)
    print(f"Results saved → {out}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
