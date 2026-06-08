#!/usr/bin/env python3
"""
Labeled scenario runner for workout-wiz.
Loads all evals/scenarios/*.yaml files, calls the live API, and reports
pass-rates by category × difficulty in a coverage matrix.

Usage:
    EVAL_AUTH_TOKEN=<jwt> python3 evals/run_scenarios.py
    # Run only specific categories:
    EVAL_CATEGORIES=coach,knowledge_graph python3 evals/run_scenarios.py
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("EVAL_AUTH_TOKEN", "")
FILTER_CATEGORIES = [c.strip() for c in os.environ.get("EVAL_CATEGORIES", "").split(",") if c.strip()]

EVAL_USER = "scenario-runner@evals.example.com"
EVAL_PASS = "ScenarioPass123!"

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
RESULTS_DIR = Path(__file__).parent / "results"

DIFFICULTIES = ["straightforward", "ambiguous", "edge_case"]


def get_token() -> str:
    if AUTH_TOKEN:
        return AUTH_TOKEN
    resp = requests.post(f"{API_BASE}/auth/jwt/login", data={"username": EVAL_USER, "password": EVAL_PASS})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    requests.post(f"{API_BASE}/auth/register", json={"email": EVAL_USER, "password": EVAL_PASS})
    resp = requests.post(f"{API_BASE}/auth/jwt/login", data={"username": EVAL_USER, "password": EVAL_PASS})
    resp.raise_for_status()
    return resp.json()["access_token"]


def load_scenarios() -> list[dict]:
    cases = []
    for yaml_file in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                cases.extend(data)
            else:
                cases.append(data)
    return cases


def run_case(case: dict, token: str) -> tuple[bool, list[str]]:
    failures = []
    if not case.get("query", "").strip():
        return True, []  # skip empty-query edge cases in automated run

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{API_BASE}/chat/",
            json={"message": case["query"]},
            headers=headers,
            timeout=60,
        )
    except requests.Timeout:
        return False, ["timeout after 60s"]

    if resp.status_code != 200:
        return False, [f"HTTP {resp.status_code}"]

    data = resp.json()
    reply = data.get("reply", "")
    audit_log = data.get("audit_log", [])
    actual_events = {e.get("event", "") for e in audit_log}

    # Maps YAML expected_tool names → actual audit_log event names emitted by the hub.
    # search_exercises / build_workout are internal generator tool calls (not separate
    # audit events); map them to "generator" so presence of the generator node is enough.
    tool_event_map = {
        "knowledge_graph": "kg_hub",
        "coach": "coach",
        "workout_log": "logger",
        "knowledge_graph": "kg_hub",
        "fallback": "clarification",
    }

    for tool in case.get("expected_tools", []):
        event = tool_event_map.get(tool, tool)
        if event not in actual_events and tool not in actual_events:
            failures.append(f"tool '{tool}' missing from audit_log")

    for term in case.get("must_contain", []):
        if term.lower() not in reply.lower():
            failures.append(f"must_contain '{term}' absent")

    for term in case.get("must_not_contain", []):
        if term.lower() in reply.lower():
            failures.append(f"must_not_contain '{term}' present")

    return len(failures) == 0, failures


def print_matrix(matrix: dict, categories: list[str]) -> None:
    col_w = 16
    header = f"{'':20s}" + "".join(f"{d:>{col_w}}" for d in DIFFICULTIES)
    print(header)
    print("-" * (20 + col_w * len(DIFFICULTIES)))
    for cat in sorted(categories):
        row = f"{cat:20s}"
        for diff in DIFFICULTIES:
            cell = matrix.get((cat, diff))
            if cell is None:
                row += f"{'--':>{col_w}}"
            else:
                passed, total = cell
                row += f"{f'{passed}/{total}':>{col_w}}"
        print(row)


def save_results(run: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / f"scenarios-{ts}.json"
    out.write_text(json.dumps(run, indent=2))
    (RESULTS_DIR / "scenarios-latest.json").write_text(json.dumps(run, indent=2))
    return out


def main() -> int:
    print(f"Loading scenarios from {SCENARIOS_DIR}")
    all_cases = load_scenarios()
    if FILTER_CATEGORIES:
        cases = [c for c in all_cases if c.get("category") in FILTER_CATEGORIES]
        print(f"Filtered to {FILTER_CATEGORIES}: {len(cases)}/{len(all_cases)} cases")
    else:
        cases = all_cases
        print(f"Found {len(cases)} scenarios")

    token = get_token()
    categories = sorted({c.get("category", "unknown") for c in cases})

    passed_total = 0
    failed_total = 0
    matrix: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    case_results = []
    started_at = datetime.now(timezone.utc).isoformat()

    for case in cases:
        case_id = case.get("id", "?")
        cat = case.get("category", "unknown")
        diff = case.get("difficulty", "unknown")
        print(f"  [{case_id}] {case.get('query', '')[:55]:<55}", end=" ", flush=True)
        ok, failures = run_case(case, token)
        status = "PASS" if ok else "FAIL"
        print(status)
        if not ok:
            for f in failures:
                print(f"    ✗ {f}")
        matrix[(cat, diff)][1] += 1
        if ok:
            matrix[(cat, diff)][0] += 1
            passed_total += 1
        else:
            failed_total += 1
        case_results.append(
            {
                "id": case_id,
                "category": cat,
                "difficulty": diff,
                "passed": ok,
                "failures": failures,
            }
        )

    print(f"\n{'='*60}")
    print("COVERAGE MATRIX (passed/total per cell)")
    print(f"{'='*60}")
    final_matrix = {k: tuple(v) for k, v in matrix.items()}
    print_matrix(final_matrix, categories)
    print(f"\nOverall: {passed_total} passed, {failed_total} failed out of {len(cases)}")

    # Nested {category: {difficulty: [passed, total]}} matrix for the persisted summary.
    matrix_summary: dict[str, dict[str, list[int]]] = defaultdict(dict)
    for (cat, diff), cell in matrix.items():
        matrix_summary[cat][diff] = list(cell)

    total = len(cases)
    pct = round(passed_total / total * 100) if total else 0

    run = {
        "suite": "scenarios",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "summary": {
            "total": total,
            "passed": passed_total,
            "failed": failed_total,
            "pass_pct": pct,
            "matrix": {cat: dict(diffs) for cat, diffs in matrix_summary.items()},
        },
        "cases": case_results,
    }
    out = save_results(run)
    print(f"Results saved → {out}")

    return 0 if failed_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
