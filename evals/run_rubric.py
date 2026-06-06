#!/usr/bin/env python3
"""
Stage 4 LLM-as-judge rubric runner for workout-wiz.
Loads replay fixtures, calls the live API for a fresh response, and scores each
response against the workout-wiz rubric using Claude as the judge.
Persists results to evals/results/rubric-<timestamp>.json and rubric-latest.json.

Usage:
    backend/.venv/bin/python evals/run_rubric.py
    API_BASE=http://localhost:8000 backend/.venv/bin/python evals/run_rubric.py
    ANTHROPIC_API_KEY=sk-... backend/.venv/bin/python evals/run_rubric.py

Required env vars:
    ANTHROPIC_API_KEY — API key for the LLM judge calls

Optional env vars:
    API_BASE         — default http://localhost:8000
    EVAL_AUTH_TOKEN  — pre-minted JWT; if set, auto-login is skipped
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("EVAL_AUTH_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

JUDGE_MODEL = "claude-haiku-4-5-20251001"

EVAL_USER = "golden-runner@evals.example.com"
EVAL_PASS = "GoldenPass123!"

FIXTURES_DIR = Path(__file__).parent / "replays" / "fixtures"
RUBRIC_PATH = Path(__file__).parent / "rubrics" / "workout-wiz.yaml"
RESULTS_DIR = Path(__file__).parent / "results"

# Quality band boundaries (from rubric thresholds)
QUALITY_BANDS = [
    (4.5, "Excellent"),
    (3.5, "Good"),
    (2.5, "Acceptable"),
    (1.5, "Poor"),
    (0.0, "Critical"),
]

GOOD_THRESHOLD = 3.5
POOR_THRESHOLD = 2.5


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def get_token() -> str:
    if AUTH_TOKEN:
        return AUTH_TOKEN
    resp = requests.post(
        f"{API_BASE}/auth/jwt/login",
        data={"username": EVAL_USER, "password": EVAL_PASS},
    )
    if resp.status_code == 200:
        return resp.json()["access_token"]
    # Auto-register then login
    requests.post(
        f"{API_BASE}/auth/register",
        json={"email": EVAL_USER, "password": EVAL_PASS},
    )
    resp = requests.post(
        f"{API_BASE}/auth/jwt/login",
        data={"username": EVAL_USER, "password": EVAL_PASS},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Rubric loading
# ---------------------------------------------------------------------------
def load_rubric() -> dict:
    with open(RUBRIC_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------
def load_fixtures() -> list[dict]:
    fixtures = []
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
            data["_slug"] = path.stem
        fixtures.append(data)
    return fixtures


# ---------------------------------------------------------------------------
# Live API call
# ---------------------------------------------------------------------------
def call_api(query: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(
        f"{API_BASE}/chat/",
        json={"message": query},
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# not_applicable_when evaluation
# ---------------------------------------------------------------------------
def is_applicable(dimension_cfg: dict, route: str) -> bool:
    """Return True if this dimension should be scored for the given route."""
    rules = dimension_cfg.get("not_applicable_when", [])
    for rule in rules:
        rule = rule.strip()
        if "==" in rule:
            lhs, rhs = [s.strip() for s in rule.split("==", 1)]
            if lhs == "route" and route == rhs:
                return False
        elif "!=" in rule:
            lhs, rhs = [s.strip() for s in rule.split("!=", 1)]
            if lhs == "route" and route != rhs:
                return False
    return True


# ---------------------------------------------------------------------------
# LLM judge call
# ---------------------------------------------------------------------------
def score_dimension(
    client: Anthropic,
    dim_name: str,
    dim_cfg: dict,
    query: str,
    route: str,
    confidence: float,
    reply: str,
    audit_log: list,
    workout_draft,
    kg_result,
) -> dict:
    """Ask the LLM judge to score one dimension. Returns {score, rationale}."""
    # Build score anchors block
    scores_block = "\n".join(
        f"  {score}: {desc}" for score, desc in sorted(dim_cfg["scores"].items())
    )

    # Summarize audit_log events for context
    events = [e.get("event", "") for e in (audit_log or []) if e.get("event")]
    audit_summary = ", ".join(events) if events else "(none)"

    prompt = f"""You are an objective quality judge for a fitness coaching AI system.

Score the following AI response on ONE dimension. Respond with ONLY a JSON object — no markdown, no explanation outside the JSON.

## Dimension: {dim_name}
{dim_cfg['description']}

## Score Anchors (0–5):
{scores_block}

## Request being evaluated:
Query: {query}
Route: {route}
Confidence: {confidence}
Audit log events: {audit_summary}
Workout draft: {json.dumps(workout_draft)}
KG result: {json.dumps(kg_result)}

## AI Response:
{reply}

Respond with this exact JSON (no other text):
{{"dimension": "{dim_name}", "score": <integer 0-5>, "rationale": "<one or two sentences>"}}"""

    message = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    parsed = json.loads(raw)
    return {
        "score": int(parsed["score"]),
        "rationale": str(parsed.get("rationale", "")),
    }


# ---------------------------------------------------------------------------
# Quality band
# ---------------------------------------------------------------------------
def quality_band(score: float) -> str:
    for threshold, label in QUALITY_BANDS:
        if score >= threshold:
            return label
    return "Critical"


# ---------------------------------------------------------------------------
# Per-fixture evaluation
# ---------------------------------------------------------------------------
def evaluate_fixture(
    fixture: dict,
    rubric: dict,
    token: str,
    client: Anthropic,
) -> dict:
    slug = fixture["_slug"]
    query = fixture["query"]

    # Call live API for a fresh response
    api_response = call_api(query, token)

    route = api_response.get("route", "UNKNOWN")
    confidence = api_response.get("confidence", 0.0)
    reply = api_response.get("reply", "")
    audit_log = api_response.get("audit_log", [])
    workout_draft = api_response.get("workout_draft")
    kg_result = api_response.get("kg_result")

    dimensions = rubric["dimensions"]

    # Determine which dimensions are applicable
    applicable_dims = {
        name: cfg
        for name, cfg in dimensions.items()
        if is_applicable(cfg, route)
    }

    # Score each applicable dimension
    dimension_scores = {}
    for dim_name, dim_cfg in applicable_dims.items():
        result = score_dimension(
            client=client,
            dim_name=dim_name,
            dim_cfg=dim_cfg,
            query=query,
            route=route,
            confidence=confidence,
            reply=reply,
            audit_log=audit_log,
            workout_draft=workout_draft,
            kg_result=kg_result,
        )
        dimension_scores[dim_name] = {
            "score": result["score"],
            "rationale": result["rationale"],
            "weight": dim_cfg["weight"],
        }

    # Compute weighted average using only applicable dimensions
    # Normalize weights so they sum to 1.0 for the applicable subset
    total_weight = sum(cfg["weight"] for cfg in applicable_dims.values())
    if total_weight > 0 and dimension_scores:
        overall = sum(
            dimension_scores[name]["score"] * (applicable_dims[name]["weight"] / total_weight)
            for name in dimension_scores
        )
    else:
        overall = 0.0

    overall = round(overall, 2)
    band = quality_band(overall)

    return {
        "fixture": slug,
        "query": query,
        "route": route,
        "confidence": confidence,
        "dimension_scores": dimension_scores,
        "overall_score": overall,
        "quality_band": band,
    }


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------
def save_results(run: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / f"rubric-{ts}.json"
    out.write_text(json.dumps(run, indent=2))
    (RESULTS_DIR / "rubric-latest.json").write_text(json.dumps(run, indent=2))
    return out


# ---------------------------------------------------------------------------
# Formatted print
# ---------------------------------------------------------------------------
def print_fixture_row(result: dict) -> None:
    slug = result["fixture"]
    route = result["route"]
    overall = result["overall_score"]
    band = result["quality_band"]
    ds = result["dimension_scores"]

    # Build per-dimension snippets for the two always-present dims
    routing = ds.get("routing_accuracy", {}).get("score", "N/A")
    clarity = ds.get("response_clarity", {}).get("score", "N/A")

    routing_str = f"{routing}/5" if isinstance(routing, int) else "N/A"
    clarity_str = f"{clarity}/5" if isinstance(clarity, int) else "N/A"

    print(
        f"[{slug}] route={route}  routing={routing_str}  clarity={clarity_str}  "
        f"overall={overall}/5 → {band}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is required for LLM judge calls.", file=sys.stderr)
        print("Set it via: export ANTHROPIC_API_KEY=sk-...", file=sys.stderr)
        return 1

    print(f"Loading rubric from {RUBRIC_PATH}")
    rubric = load_rubric()
    rubric_name = rubric.get("name", "workout-wiz-v1")
    print(f"Rubric: {rubric_name} ({len(rubric['dimensions'])} dimensions)")

    print(f"\nLoading fixtures from {FIXTURES_DIR}")
    fixtures = load_fixtures()
    if not fixtures:
        print("ERROR: No fixtures found in evals/replays/fixtures/", file=sys.stderr)
        return 1
    print(f"Found {len(fixtures)} fixture(s)\n")

    print("Authenticating...")
    token = get_token()
    print(f"Authenticated as {EVAL_USER}\n")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    run_at = datetime.now(timezone.utc).isoformat()
    results = []
    any_poor = False

    for fixture in fixtures:
        slug = fixture["_slug"]
        print(f"  Evaluating [{slug}]...", flush=True)
        try:
            result = evaluate_fixture(fixture, rubric, token, client)
            results.append(result)
            print_fixture_row(result)
            if result["overall_score"] < POOR_THRESHOLD:
                any_poor = True
        except requests.HTTPError as e:
            print(f"  ERROR [{slug}]: API call failed — {e}", file=sys.stderr)
            results.append({
                "fixture": slug,
                "query": fixture.get("query", ""),
                "route": "ERROR",
                "confidence": 0.0,
                "dimension_scores": {},
                "overall_score": 0.0,
                "quality_band": "Critical",
                "error": str(e),
            })
            any_poor = True
        except json.JSONDecodeError as e:
            print(f"  ERROR [{slug}]: Judge returned invalid JSON — {e}", file=sys.stderr)
            results.append({
                "fixture": slug,
                "query": fixture.get("query", ""),
                "route": "ERROR",
                "confidence": 0.0,
                "dimension_scores": {},
                "overall_score": 0.0,
                "quality_band": "Critical",
                "error": f"JSON parse error: {e}",
            })
            any_poor = True

    # Summary statistics
    scored = [r for r in results if r["route"] != "ERROR"]
    if scored:
        overall_scores = [r["overall_score"] for r in scored]
        mean_overall = round(sum(overall_scores) / len(overall_scores), 2)
        min_overall = round(min(overall_scores), 2)
    else:
        mean_overall = 0.0
        min_overall = 0.0

    all_good = all(r["overall_score"] >= GOOD_THRESHOLD for r in results)

    print(f"\n{'='*60}")
    print(f"Rubric evaluation complete — {len(results)} fixture(s)")
    print(f"Mean overall: {mean_overall}/5  |  Min overall: {min_overall}/5")
    print(f"{'='*60}")

    run = {
        "run_at": run_at,
        "model_judge": JUDGE_MODEL,
        "rubric": rubric_name,
        "results": results,
        "summary": {
            "mean_overall": mean_overall,
            "min_overall": min_overall,
            "fixtures_evaluated": len(results),
        },
    }
    out = save_results(run)
    print(f"Results saved → {out}")

    # Exit codes:
    #   0 — all fixtures >= 3.5 (Good or better)
    #   1 — any fixture < 2.5 (Poor or worse)
    if any_poor:
        return 1
    if not all_good:
        return 0  # Some in Acceptable range — not a hard failure
    return 0


if __name__ == "__main__":
    sys.exit(main())
