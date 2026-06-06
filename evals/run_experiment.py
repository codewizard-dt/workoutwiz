#!/usr/bin/env python3
"""
Stage 5 experiment runner for workout-wiz.
Runs an A/B comparison between a baseline config and a variant config over
the golden set (or an optional subset), then emits a delta table and saves
a structured result JSON.

Usage:
    backend/.venv/bin/python evals/run_experiment.py evals/experiments/my-experiment.yaml
    API_BASE=http://localhost:8000 backend/.venv/bin/python evals/run_experiment.py evals/experiments/my-experiment.yaml

Exit codes:
    0 — variant pass-rate is within 5% of baseline (acceptable)
    1 — variant regressed more than 5 percentage points vs baseline
    2 — bad arguments / unreadable spec
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("EVAL_AUTH_TOKEN", "")

EVAL_USER = "golden-runner@evals.example.com"
EVAL_PASS = "GoldenPass123!"

EVALS_DIR = Path(__file__).parent
GOLDEN_DIR = EVALS_DIR / "golden"
SCENARIOS_DIR = EVALS_DIR / "scenarios"
RESULTS_DIR = EVALS_DIR / "results"

# Map tool names used in YAML → audit_log event names returned by the API
TOOL_EVENT_MAP = {
    "workout_gen": "generator",
    "search_exercises": "generator",
    "build_workout": "generator",
    "coach": "coach",
    "workout_log": "logger",
    "knowledge_graph": "kg_hub",
    "fallback": "clarification",
    "clarification": "clarification",
}

# Maximum regression allowed before exit(1)
REGRESSION_THRESHOLD = 0.05  # 5 percentage points


# ---------------------------------------------------------------------------
# Auth (identical pattern to run_golden.py)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

def _load_yaml_file(path: Path) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, list) else [data]


def load_cases(test_set: str) -> list[dict]:
    """
    Load test cases according to test_set value:
      "golden"    → evals/golden/*.yaml
      "scenarios" → evals/scenarios/*.yaml
      glob string → treated as a glob pattern relative to cwd
    """
    if test_set == "golden":
        yaml_files = sorted(GOLDEN_DIR.glob("*.yaml"))
    elif test_set == "scenarios":
        yaml_files = sorted(SCENARIOS_DIR.glob("*.yaml"))
    else:
        # Treat as a glob pattern
        yaml_files = sorted(Path(".").glob(test_set))
        if not yaml_files:
            # Try relative to the evals dir
            yaml_files = sorted(EVALS_DIR.glob(test_set))

    if not yaml_files:
        raise FileNotFoundError(f"No YAML files matched test_set={test_set!r}")

    cases = []
    for f in yaml_files:
        cases.extend(_load_yaml_file(f))
    return cases


# ---------------------------------------------------------------------------
# Single-case runner
# ---------------------------------------------------------------------------

def run_case(case: dict, token: str) -> dict:
    """
    Call /chat/ for a single case. Returns a result dict with:
      passed, failures, route, confidence, latency_ms, reply_length
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    failures = []
    route = None
    confidence = None
    latency_ms = None
    reply_length = 0

    t0 = time.monotonic()
    try:
        resp = requests.post(
            f"{API_BASE}/chat/",
            json={"message": case["query"]},
            headers=headers,
            timeout=60,
        )
        latency_ms = round((time.monotonic() - t0) * 1000)
    except requests.RequestException as e:
        latency_ms = round((time.monotonic() - t0) * 1000)
        return {
            "id": case.get("id", "?"),
            "passed": False,
            "failures": [f"request error: {e}"],
            "route": None,
            "confidence": None,
            "latency_ms": latency_ms,
            "reply_length": 0,
        }

    if resp.status_code != 200:
        return {
            "id": case.get("id", "?"),
            "passed": False,
            "failures": [f"HTTP {resp.status_code}: {resp.text[:200]}"],
            "route": None,
            "confidence": None,
            "latency_ms": latency_ms,
            "reply_length": 0,
        }

    data = resp.json()
    reply = data.get("reply", "")
    route = data.get("route")
    confidence = data.get("confidence")
    reply_length = len(reply)
    actual_events = {e.get("event", "") for e in data.get("audit_log", [])}

    for expected_tool in case.get("expected_tools", []):
        event_name = TOOL_EVENT_MAP.get(expected_tool, expected_tool)
        if event_name not in actual_events and expected_tool not in actual_events:
            failures.append(
                f"expected_tool '{expected_tool}' not in audit_log events: {sorted(actual_events)}"
            )

    for term in case.get("must_contain", []):
        if term.lower() not in reply.lower():
            failures.append(f"must_contain '{term}' not found in reply")

    for term in case.get("must_not_contain", []):
        if term.lower() in reply.lower():
            failures.append(f"must_not_contain '{term}' found in reply")

    return {
        "id": case.get("id", "?"),
        "passed": len(failures) == 0,
        "failures": failures,
        "route": route,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "reply_length": reply_length,
    }


# ---------------------------------------------------------------------------
# Arm runner (runs all cases under a given env context)
# ---------------------------------------------------------------------------

def run_arm(label: str, cases: list[dict], token: str, env_overrides: dict, runs_per_case: int) -> dict:
    """
    Run all cases for one arm (baseline or variant).
    env_overrides are temporarily applied to os.environ for the duration.
    Returns a result dict ready for the JSON output schema.
    """
    # Apply env overrides
    original_env = {}
    for k, v in env_overrides.items():
        original_env[k] = os.environ.get(k)
        os.environ[k] = str(v)

    print(f"\n{'='*60}")
    print(f"Running arm: {label}")
    if env_overrides:
        for k, v in env_overrides.items():
            print(f"  ENV: {k}={v}")
    print(f"{'='*60}")

    case_results = []
    for case in cases:
        case_id = case.get("id", "?")
        # For runs_per_case > 1 we take the majority vote on pass/fail
        # and average latency. For runs_per_case == 1 it's trivial.
        run_results = []
        for run_idx in range(runs_per_case):
            suffix = f" (run {run_idx+1}/{runs_per_case})" if runs_per_case > 1 else ""
            print(f"  [{case_id}]{suffix} {case.get('query', '')[:55]}...", end=" ", flush=True)
            result = run_case(case, token)
            print("PASS" if result["passed"] else "FAIL")
            if not result["passed"]:
                for f in result["failures"]:
                    print(f"    ✗ {f}")
            run_results.append(result)

        # Aggregate across runs
        passes = sum(1 for r in run_results if r["passed"])
        passed = passes >= (runs_per_case / 2)  # majority vote
        all_failures = [f for r in run_results for f in r["failures"]]
        avg_latency = round(sum(r["latency_ms"] for r in run_results) / len(run_results))
        last = run_results[-1]

        case_results.append({
            "id": case_id,
            "passed": passed,
            "failures": all_failures,
            "route": last["route"],
            "confidence": last["confidence"],
            "latency_ms": avg_latency,
            "reply_length": last["reply_length"],
            "runs": runs_per_case,
            "pass_count": passes,
        })

    # Restore original env
    for k, original_v in original_env.items():
        if original_v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = original_v

    total = len(case_results)
    passed_count = sum(1 for r in case_results if r["passed"])
    pass_rate = round(passed_count / total, 4) if total else 0.0
    latencies = [r["latency_ms"] for r in case_results if r["latency_ms"] is not None]
    mean_latency = round(sum(latencies) / len(latencies)) if latencies else None

    return {
        "label": label,
        "pass_rate": pass_rate,
        "passed": passed_count,
        "total": total,
        "mean_latency_ms": mean_latency,
        "cases": case_results,
    }


# ---------------------------------------------------------------------------
# Delta table printer
# ---------------------------------------------------------------------------

def _route_delta(baseline_route, variant_route) -> str:
    if baseline_route is None and variant_route is None:
        return "same"
    if baseline_route == variant_route:
        return "same"
    b = baseline_route or "?"
    v = variant_route or "?"
    return f"{b}→{v}"


def print_delta_table(baseline: dict, variant: dict) -> None:
    b_cases = {r["id"]: r for r in baseline["cases"]}
    v_cases = {r["id"]: r for r in variant["cases"]}
    all_ids = sorted(set(b_cases) | set(v_cases))

    col_id = max(len("Case"), max((len(i) for i in all_ids), default=4))
    print(f"\n{'='*80}")
    print(
        f"{'Case':<{col_id}}  {'Baseline':^10}  {'Variant':^10}  "
        f"{'Δ Route':<20}  {'Δ Latency':>10}"
    )
    print(f"{'-'*col_id}  {'-'*10}  {'-'*10}  {'-'*20}  {'-'*10}")

    for cid in all_ids:
        b = b_cases.get(cid)
        v = v_cases.get(cid)

        b_pass = ("✓" if b["passed"] else "✗") if b else "N/A"
        if b and not b["passed"] and b["failures"]:
            b_pass += f" ({b['failures'][0][:20]})"

        v_pass = ("✓" if v["passed"] else "✗") if v else "N/A"
        if v and not v["passed"] and v["failures"]:
            v_pass += f" ({v['failures'][0][:20]})"

        route_d = _route_delta(b["route"] if b else None, v["route"] if v else None)

        if b and v and b["latency_ms"] is not None and v["latency_ms"] is not None:
            delta_lat = v["latency_ms"] - b["latency_ms"]
            lat_str = f"+{delta_lat}ms" if delta_lat >= 0 else f"{delta_lat}ms"
        else:
            lat_str = "N/A"

        print(
            f"{cid:<{col_id}}  {b_pass:<10}  {v_pass:<10}  "
            f"{route_d:<20}  {lat_str:>10}"
        )

    print(f"{'='*80}")
    b_pct = round(baseline["pass_rate"] * 100, 1)
    v_pct = round(variant["pass_rate"] * 100, 1)
    delta_pct = round((variant["pass_rate"] - baseline["pass_rate"]) * 100, 1)
    sign = "+" if delta_pct >= 0 else ""
    print(
        f"SUMMARY: baseline {baseline['passed']}/{baseline['total']} ({b_pct}%), "
        f"variant {variant['passed']}/{variant['total']} ({v_pct}%), "
        f"Δpass_rate={sign}{delta_pct}%"
    )
    if baseline["mean_latency_ms"] and variant["mean_latency_ms"]:
        lat_delta = variant["mean_latency_ms"] - baseline["mean_latency_ms"]
        lat_sign = "+" if lat_delta >= 0 else ""
        print(
            f"LATENCY:  baseline {baseline['mean_latency_ms']}ms avg, "
            f"variant {variant['mean_latency_ms']}ms avg, "
            f"Δ={lat_sign}{lat_delta}ms"
        )
    print(f"{'='*80}\n")


# ---------------------------------------------------------------------------
# Result persistence
# ---------------------------------------------------------------------------

def save_results(experiment_name: str, result: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = experiment_name.replace(" ", "-").replace("/", "-")
    out = RESULTS_DIR / f"experiment-{slug}-{ts}.json"
    out.write_text(json.dumps(result, indent=2))
    return out


# ---------------------------------------------------------------------------
# Spec loading
# ---------------------------------------------------------------------------

def load_spec(spec_path: Path) -> dict:
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    # Validate required keys
    required = {"name", "baseline", "variant"}
    missing = required - set(spec.keys())
    if missing:
        raise ValueError(f"Experiment spec missing required keys: {missing}")

    spec.setdefault("test_set", "golden")
    spec.setdefault("runs_per_case", 1)
    spec["baseline"].setdefault("label", "baseline")
    spec["baseline"].setdefault("env", {})
    spec["variant"].setdefault("env", {})

    return spec


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run_experiment.py <experiment-spec.yaml>", file=sys.stderr)
        return 2

    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"Spec file not found: {spec_path}", file=sys.stderr)
        return 2

    try:
        spec = load_spec(spec_path)
    except (ValueError, KeyError) as e:
        print(f"Invalid experiment spec: {e}", file=sys.stderr)
        return 2

    name = spec["name"]
    description = spec.get("description", "")
    test_set = spec["test_set"]
    runs_per_case = int(spec.get("runs_per_case", 1))

    print(f"Experiment: {name}")
    if description:
        print(f"Description: {description}")
    print(f"Test set: {test_set}  |  runs_per_case: {runs_per_case}")

    # Load cases
    try:
        cases = load_cases(test_set)
    except FileNotFoundError as e:
        print(f"Error loading cases: {e}", file=sys.stderr)
        return 2
    print(f"Loaded {len(cases)} cases")

    # Auth
    print(f"\nAuthenticating against {API_BASE}...")
    try:
        token = get_token()
    except Exception as e:
        print(f"Auth failed: {e}", file=sys.stderr)
        return 2
    print("Authenticated.")

    run_at = datetime.now(timezone.utc).isoformat()

    # Run baseline
    baseline_arm = spec["baseline"]
    baseline = run_arm(
        label=baseline_arm["label"],
        cases=cases,
        token=token,
        env_overrides=baseline_arm.get("env", {}),
        runs_per_case=runs_per_case,
    )

    # Run variant
    variant_arm = spec["variant"]
    variant = run_arm(
        label=variant_arm["label"],
        cases=cases,
        token=token,
        env_overrides=variant_arm.get("env", {}),
        runs_per_case=runs_per_case,
    )

    # Delta table
    print_delta_table(baseline, variant)

    # Verdict
    delta_pass_rate = variant["pass_rate"] - baseline["pass_rate"]
    verdict = "PASS" if delta_pass_rate >= -REGRESSION_THRESHOLD else "REGRESSION"
    print(f"Verdict: {verdict}")
    if verdict == "REGRESSION":
        print(
            f"  Variant regressed {abs(round(delta_pass_rate * 100, 1))}% "
            f"(threshold: {round(REGRESSION_THRESHOLD * 100)}%)"
        )

    # Build result document
    result = {
        "experiment": name,
        "description": description,
        "spec": str(spec_path),
        "run_at": run_at,
        "api_base": API_BASE,
        "test_set": test_set,
        "runs_per_case": runs_per_case,
        "baseline": baseline,
        "variant": variant,
        "delta": {
            "pass_rate": round(delta_pass_rate, 4),
            "mean_latency_ms": (
                variant["mean_latency_ms"] - baseline["mean_latency_ms"]
                if baseline["mean_latency_ms"] is not None and variant["mean_latency_ms"] is not None
                else None
            ),
        },
        "verdict": verdict,
    }

    out = save_results(name, result)
    print(f"Results saved → {out}")

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
