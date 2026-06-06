# Stage 5 — Experiments

Experiment infrastructure for A/B comparisons between a baseline config and a variant config over the workout-wiz golden set (or any subset).

Use this stage whenever you change a model, a prompt, a routing temperature, or any other config that affects response quality. It gives you a before/after delta table and a binary verdict (PASS / REGRESSION) suitable for CI gates.

---

## When to use

Run an experiment on **any model, prompt, or routing config change** — before merging to main. Examples:

- Updating the router system prompt
- Switching the underlying LLM model (e.g. Sonnet → Haiku)
- Changing router temperature or sampling settings
- Adding or removing few-shot examples
- Changing the coach sub-agent's persona instructions

---

## Defining a new experiment

Create a YAML file in `evals/experiments/`. Copy `example-experiment.yaml` as a starting point:

```yaml
name: "my-router-prompt-v2"
description: "Test updated router system prompt against baseline"

baseline:
  label: "baseline"
  env: {}       # no overrides — calls the endpoint as-is

variant:
  label: "router-prompt-v2"
  env:
    ROUTER_PROMPT_OVERRIDE: "prompts/router-v2.txt"
    # Any env vars your backend reads to activate the variant behavior.
    # The backend must read these at request time, not at startup.

test_set: "golden"    # "golden", "scenarios", or a glob like "evals/golden/gs-00*.yaml"
runs_per_case: 1      # increase to 3+ for stochastic outputs (majority vote)
```

### Spec fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | — | Unique slug — used in output filename |
| `description` | No | `""` | Human-readable summary |
| `baseline.label` | No | `"baseline"` | Label shown in delta table |
| `baseline.env` | No | `{}` | Env vars for baseline arm (usually empty) |
| `variant.label` | Yes | — | Label shown in delta table |
| `variant.env` | Yes | — | Env vars injected for variant arm |
| `test_set` | No | `"golden"` | `"golden"`, `"scenarios"`, or a glob string |
| `runs_per_case` | No | `1` | Calls per case per arm (majority vote when > 1) |

---

## Running an experiment

```bash
# Backend must be running first
cd backend && uvicorn app.main:app --reload &

# Run the experiment
backend/.venv/bin/python evals/run_experiment.py evals/experiments/my-experiment.yaml

# Point at a non-default API
API_BASE=https://staging.example.com \
  backend/.venv/bin/python evals/run_experiment.py evals/experiments/my-experiment.yaml

# Supply a pre-existing JWT (skips auto-login)
EVAL_AUTH_TOKEN=<your-jwt> \
  backend/.venv/bin/python evals/run_experiment.py evals/experiments/my-experiment.yaml
```

Auth uses the same auto-login pattern as `run_golden.py`: if `EVAL_AUTH_TOKEN` is not set, the runner auto-registers `golden-runner@evals.example.com` / `GoldenPass123!`.

---

## Interpreting results

The runner prints a delta table then a summary line:

```
================================================================
Case         Baseline    Variant     Δ Route               Δ Latency
---------    ----------  ----------  --------------------  ----------
gs-001       ✓           ✓           same                    +120ms
gs-008       ✓           ✗ (wrong r  COACH→LOG                -40ms
gs-011       ✓           ✓           same                     -20ms
...
================================================================
SUMMARY: baseline 11/11 (100.0%), variant 10/11 (90.9%), Δpass_rate=-9.1%
LATENCY:  baseline 850ms avg, variant 820ms avg, Δ=-30ms
================================================================

Verdict: REGRESSION
```

### Verdict rules

| Condition | Verdict | Exit code |
|-----------|---------|-----------|
| `variant_pass_rate >= baseline_pass_rate - 5%` | `PASS` | `0` |
| `variant_pass_rate < baseline_pass_rate - 5%` | `REGRESSION` | `1` |

A 5-percentage-point regression threshold is the default. This allows for minor LLM non-determinism without false alarms, while still catching real regressions.

### Δ Route column

- `same` — both arms routed identically
- `COACH→LOG` — baseline routed to COACH, variant routed to WORKOUT_LOG (a regression in routing)
- `LOG→same` — routing fixed relative to baseline (variant improvement)

### Reading latency deltas

Latency is measured end-to-end from the client. A variant being 100ms faster may simply reflect LLM token count differences, not a meaningful change. Focus on pass-rate delta as the primary signal; treat latency as secondary context.

---

## Result JSON

Results are saved to `evals/results/experiment-<name>-<timestamp>.json`:

```json
{
  "experiment": "my-router-prompt-v2",
  "description": "...",
  "run_at": "2026-06-06T12:34:56+00:00",
  "api_base": "http://localhost:8000",
  "test_set": "golden",
  "runs_per_case": 1,
  "baseline": {
    "label": "baseline",
    "pass_rate": 1.0,
    "passed": 15,
    "total": 15,
    "mean_latency_ms": 850,
    "cases": [...]
  },
  "variant": {
    "label": "router-prompt-v2",
    "pass_rate": 0.9333,
    "passed": 14,
    "total": 15,
    "mean_latency_ms": 820,
    "cases": [...]
  },
  "delta": {
    "pass_rate": -0.0667,
    "mean_latency_ms": -30
  },
  "verdict": "REGRESSION"
}
```

Each case entry in `cases` includes `id`, `passed`, `failures`, `route`, `confidence`, `latency_ms`, and `reply_length`.

---

## CI integration

Add to your release workflow:

```yaml
- name: Run experiment
  run: |
    backend/.venv/bin/python evals/run_experiment.py \
      evals/experiments/my-experiment.yaml
  # Exit code 1 = REGRESSION → CI fails automatically
```

The runner exits `0` on PASS and `1` on REGRESSION, making it a drop-in CI gate.
