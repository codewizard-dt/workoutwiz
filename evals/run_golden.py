#!/usr/bin/env python3
"""
Golden set runner for workout-wiz.
Loads all evals/golden/*.yaml files, calls the live API, and checks assertions.
Persists each run to evals/results/golden-<timestamp>.json.

Usage:
    backend/.venv/bin/python evals/run_golden.py
    API_BASE=http://localhost:8000 backend/.venv/bin/python evals/run_golden.py
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("EVAL_AUTH_TOKEN", "")

EVAL_USER = "golden-runner@evals.example.com"
EVAL_PASS = "GoldenPass123!"

GOLDEN_DIR = Path(__file__).parent / "golden"
RESULTS_DIR = Path(__file__).parent / "results"

tool_event_map = {
    "knowledge_graph": "kg_hub",
    "coach": "coach",
    "workout_log": "logger",
    "knowledge_graph": "kg_hub",
    "fallback": "clarification",
    "clarification": "clarification",
}


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


def load_cases() -> list[dict]:
    cases = []
    for yaml_file in sorted(GOLDEN_DIR.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            cases.extend(data if isinstance(data, list) else [data])
    return cases


def run_case(case: dict, token: str) -> tuple[bool, list[str]]:
    failures = []
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{API_BASE}/chat/", json={"message": case["query"]}, headers=headers, timeout=60)
    except requests.RequestException as e:
        return False, [f"request error: {e}"]

    if resp.status_code != 200:
        return False, [f"HTTP {resp.status_code}: {resp.text[:200]}"]

    data = resp.json()
    reply = data.get("reply", "")
    actual_events = {e.get("event", "") for e in data.get("audit_log", [])}

    for expected_tool in case.get("expected_tools", []):
        event_name = tool_event_map.get(expected_tool, expected_tool)
        if event_name not in actual_events and expected_tool not in actual_events:
            failures.append(f"expected_tool '{expected_tool}' not in audit_log events: {sorted(actual_events)}")

    for term in case.get("must_contain", []):
        if term.lower() not in reply.lower():
            failures.append(f"must_contain '{term}' not found in reply")

    for term in case.get("must_not_contain", []):
        if term.lower() in reply.lower():
            failures.append(f"must_not_contain '{term}' found in reply")

    return len(failures) == 0, failures


def save_results(run: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / f"golden-{ts}.json"
    out.write_text(json.dumps(run, indent=2))
    (RESULTS_DIR / "golden-latest.json").write_text(json.dumps(run, indent=2))
    return out


def main() -> int:
    print(f"Loading golden cases from {GOLDEN_DIR}")
    cases = load_cases()
    print(f"Found {len(cases)} cases\n")

    token = get_token()
    passed = failed = 0
    case_results = []
    started_at = datetime.now(timezone.utc).isoformat()

    for case in cases:
        case_id = case.get("id", "?")
        print(f"  [{case_id}] {case.get('query', '')[:60]}...", end=" ", flush=True)
        ok, failures = run_case(case, token)
        print("PASS" if ok else "FAIL")
        if not ok:
            for f in failures:
                print(f"    ✗ {f}")
        if ok:
            passed += 1
        else:
            failed += 1
        case_results.append({"id": case_id, "passed": ok, "failures": failures})

    total = len(cases)
    pct = round(passed / total * 100) if total else 0

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed ({pct}%)")
    print(f"{'='*50}")

    run = {
        "suite": "golden",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "summary": {"total": total, "passed": passed, "failed": failed, "pass_pct": pct},
        "cases": case_results,
    }
    out = save_results(run)
    print(f"Results saved → {out}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())