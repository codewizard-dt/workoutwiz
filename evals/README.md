# Eval Suite — workout-wiz

Evaluation infrastructure for the workout-wiz fitness coaching multi-agent system. Covers routing correctness, response quality, exercise relevance, injury safety, and source faithfulness across the three routing intents: `COACH`, `WORKOUT_LOG`, and `KNOWLEDGE_GRAPH` (which handles all workout generation).

---

## Overview

The suite is structured around the 5-Stage Eval Framework (see `.docs/guides/evals-framework.md`). Each stage builds on the last:

| Stage | What it answers | Status |
|-------|----------------|--------|
| 1 — Golden Sets | "Does it work?" | **Active** — 15 cases, `run_golden.py` |
| 2 — Labeled Scenarios | "Does it work for all types?" | **Active** — 43 cases across 5 scenario files |
| 3 — Replay Harnesses | "Can we reproduce and score without live calls?" | **Active** — 7 fixtures (5 recorded, 2 stubs) |
| 4 — Rubrics | "How good is it, multi-dimensionally?" | **Defined** — runner available (`run_rubric.py`), calibration not started |
| 5 — Experiments | "Is this change actually better?" | **Scaffolded** — `run_experiment.py` + spec format in `evals/experiments/` |

**For CI purposes, Stages 1 and 2 are deterministic and free** — they assert over API responses and `audit_log` fields without calling a separate LLM judge.

---

## Directory Structure

```
evals/
├── README.md                          # this file
├── run_golden.py                      # Stage 1 runner
│
├── golden/                            # Stage 1 — canonical correctness cases
│   ├── gs-001.yaml … gs-015.yaml
│
├── scenarios/                         # Stage 2 — coverage matrix cases
│   ├── sc-coach.yaml                  # 9 coaching cases (3 per difficulty)
│   ├── sc-fallback.yaml               # 7 fallback / off-topic cases
│   ├── sc-knowledge-graph.yaml        # 9 KG / injury-routing cases
│   ├── sc-workout-gen.yaml            # 9 workout generation cases
│   └── sc-workout-log.yaml            # 9 workout log cases
│
├── replays/                           # Stage 3 — frozen session fixtures
│   └── fixtures/
│       ├── workout-log-bench-press.json
│       ├── fallback-off-topic.json
│       ├── kg-knee-injury.json
│       ├── coach-rest-days.json
│       ├── workout-gen-upper-body.json
│       ├── coach-progressive-overload.json   # stub
│       └── workout-gen-lower-body.json       # stub
│
└── rubrics/                           # Stage 4 — LLM-as-judge rubric
    └── workout-wiz.yaml
```

---

## Running the Golden Set

`run_golden.py` loads all `evals/golden/*.yaml` files, calls the live `/chat/` endpoint, and asserts tool selection, `must_contain`, and `must_not_contain` over the response.

### Prerequisites

```bash
# The backend must be running
cd backend && uvicorn app.main:app --reload
```

### Run

```bash
# Authenticate automatically (registers + logs in a dedicated eval user)
python3 evals/run_golden.py

# Point at a non-default environment
API_BASE=https://staging.workout-wiz.example.com python3 evals/run_golden.py

# Supply a pre-existing JWT (skips auto-login)
EVAL_AUTH_TOKEN=<your-jwt> python3 evals/run_golden.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE` | `http://localhost:8000` | Base URL of the FastAPI backend |
| `EVAL_AUTH_TOKEN` | *(empty)* | Pre-minted JWT. If set, auto-login is skipped. |

When `EVAL_AUTH_TOKEN` is not set the runner auto-registers `golden-runner@evals.example.com` / `GoldenPass123!` and obtains a token. The dedicated eval user keeps golden runs isolated from real user data.

### Output

```
Loading golden cases from evals/golden
Found 15 cases

Authenticated as golden-runner@evals.example.com

  [gs-001] Create a 30-minute upper body workout for me... PASS
  [gs-002] How many rest days should I take between leg... PASS
  ...
==================================================
Results: 15 passed, 0 failed out of 15 total
==================================================
```

Exit code `0` on full pass, `1` on any failure.

---

## Golden Cases — gs-001 through gs-015

All 15 cases assert **tool selection** (via `audit_log` events), **content validation** (`must_contain`), and **negative validation** (`must_not_contain`).

| ID | Query (truncated) | Expected Intent | Expected Tools |
|----|------------------|-----------------|----------------|
| gs-001 | "Create a 30-minute upper body workout for me" | `KNOWLEDGE_GRAPH` | `knowledge_graph` |
| gs-002 | "How many rest days should I take between leg workouts?" | `COACH` | `coach` |
| gs-003 | "I just finished 3 sets of 10 bench press at 135 lbs" | `WORKOUT_LOG` | `workout_log` |
| gs-004 | "I have a bad knee. Can you build me a workout that avoids aggravating it?" | `KNOWLEDGE_GRAPH` | `knowledge_graph` |
| gs-005 | "My shoulder has been bothering me lately. What workout can I do without overhead movements?" | `KNOWLEDGE_GRAPH` | `knowledge_graph` |
| gs-006 | "What's the capital of France?" | `FALLBACK` | `fallback` |
| gs-007 | "I only have dumbbells at home. Give me a 20-minute full body workout." | `KNOWLEDGE_GRAPH` | `knowledge_graph` |
| gs-008 | "I just did 4 sets of 8 benchpress at 185 pounds" *(misspelling)* | `WORKOUT_LOG` | `workout_log` |
| gs-009 | "What should I do for my workout tomorrow?" *(ambiguous)* | `COACH` | `coach` |
| gs-010 | "Recommend exercises for someone with a lower back injury who prefers cardio" | `KNOWLEDGE_GRAPH` | `knowledge_graph` |
| gs-011 | "I completed 5 sets of 5 squats at 225 lbs today" | `WORKOUT_LOG` | `workout_log` |
| gs-012 | "Just ran 5K in 28 minutes on the treadmill" | `WORKOUT_LOG` | `workout_log` |
| gs-013 | "How much protein should I eat to build muscle?" | `COACH` | `coach` |
| gs-014 | "I want to lose weight. Give me a 3-day-per-week full body workout using only resistance bands." | `KNOWLEDGE_GRAPH` | `knowledge_graph` |
| gs-015 | "What are the best running shoes for a marathon?" | `FALLBACK` | `fallback` |

**KG cases (gs-004, gs-005, gs-010) additionally assert** `must_contain: ["excluded due to injury constraints"]` to verify the safety gate fired.

**Equipment case (gs-007) additionally asserts** `must_not_contain: ["barbell", "machine"]` to verify equipment filtering.

**Fuzzy-match case (gs-008)** asserts `must_contain: ["bench press"]` to verify the `benchpress` typo was correctly matched.

---

## Scenarios — Coverage Matrix

43 labeled cases spread across 5 categories and 3 difficulty bands. These run on every release (not every commit) and are evaluated as pass-rate trends per cell, not as a binary gate.

### Coverage Grid

| Category | straightforward | ambiguous | edge_case | Total |
|----------|:--------------:|:---------:|:---------:|:-----:|
| `coach` | 3 | 3 | 3 | **9** |
| `fallback` | 3 | 3 | 1 | **7** |
| `workout_gen` | 3 | 3 | 3 | **9** |
| `workout_log` | 3 | 3 | 3 | **9** |
| `knowledge_graph` | 3 | 3 | 3 | **9** |
| **Total** | **15** | **15** | **13** | **43** |

### Subcategory Breakdown

| File | Subcategories covered |
|------|-----------------------|
| `sc-coach.yaml` | recovery, nutrition, programming, safety, medical, malformed_input, general_guidance |
| `sc-fallback.yaml` | off_topic, diet_planning, empty_input |
| `sc-workout-gen.yaml` | muscle_group, program_design, underspecified, goal_based, equipment_constraint, special_population, advanced |
| `sc-workout-log.yaml` | standard_entry, cardio_entry, underspecified, shorthand_notation, vague_log, misspelled_exercise, zero_sets, bilateral_exercise |
| `sc-knowledge-graph.yaml` | injury_avoidance, ambiguous_injury, explicit_kg_request, conflicting_constraints, over_constrained, multi_constraint |

---

## Replays

Stage 3 fixtures capture a real API response (including the full `audit_log`) against a frozen query. They let you re-score the system's output without making new LLM calls.

### Existing Fixtures

| Fixture | Query summary | Captured Route | Confidence |
|---------|--------------|----------------|-----------|
| `workout-log-bench-press.json` | "I just finished 3 sets of 10 bench press at 135 lbs" | `WORKOUT_LOG` | 0.95 |
| `fallback-off-topic.json` | "What is the capital of France?" | `FALLBACK` | 0.95 |
| `kg-knee-injury.json` | "I have a bad knee. Can you build a workout that avoids aggravating it?" | `KNOWLEDGE_GRAPH` | 0.98 |
| `coach-rest-days.json` | "How many rest days should I take between leg workouts?" | `COACH` | 0.95 |
| `workout-gen-upper-body.json` | "Create a 30-minute upper body workout for me" | `KNOWLEDGE_GRAPH` | 0.98 |
| `coach-progressive-overload.json` | "I've been doing 3×10 squats at 135 lbs for 3 weeks — how should I progress?" | `COACH` | *(stub)* |
| `workout-gen-lower-body.json` | "Build me a lower body workout focused on glutes and hamstrings using barbells" | `KNOWLEDGE_GRAPH` | *(stub)* |

### Fixture Schema

Each fixture stores:
- `recorded_at` — ISO date the fixture was captured
- `query` — the exact input sent
- `ground_truth` — `expected_route`, `must_contain`, `must_not_contain`
- `response` — the full API response object: `reply`, `route`, `confidence`, `audit_log`, `workout_draft`, `kg_result`

Stub fixtures additionally include `response._note: "stub — re-record against live API"` and zeroed-out `latency_ms` / token counts. They define the `ground_truth` contract but their response data must be replaced with a live recording before being used in automated scoring.

### Recording a New Fixture

Send a request to the live API and save the response JSON to `evals/replays/fixtures/<slug>.json`, populating the `ground_truth` block by hand. Re-record fixtures monthly or whenever the I/O schema changes so the fixture set tracks current system behavior. The two stub fixtures (`coach-progressive-overload.json` and `workout-gen-lower-body.json`) should be prioritised for re-recording.

---

## Rubrics

`evals/rubrics/workout-wiz.yaml` defines the Stage 4 LLM-as-judge rubric. The rubric scores five weighted dimensions on a 0–5 scale, producing a single weighted quality score.

### Dimensions

| Dimension | Weight | What it measures | Not applicable when |
|-----------|:------:|-----------------|---------------------|
| `routing_accuracy` | **30%** | Did the hub route to the correct sub-agent? | — |
| `exercise_relevance` | **25%** | Are recommended exercises appropriate for the stated goal, fitness level, and equipment? | route is `COACH`, `WORKOUT_LOG`, or `FALLBACK` |
| `injury_safety` | **25%** | For KG responses: are contraindicated exercises excluded and flagged? | route is not `KNOWLEDGE_GRAPH` |
| `response_clarity` | **10%** | Is the response concise, actionable, and free of contradictions? | — |
| `source_faithfulness` | **10%** | Are all exercises traceable to the KG retrieval result? No hallucinated exercise names. | route is not `KNOWLEDGE_GRAPH` |

### Score Thresholds → Action Policy

| Score | Quality | Action |
|:-----:|---------|--------|
| 4.5 – 5.0 | Excellent | Ship it |
| 3.5 – 4.4 | Good | Minor tweaks |
| 2.5 – 3.4 | Acceptable | Review and improve |
| 1.5 – 2.4 | Poor | Significant work needed |
| 0.0 – 1.4 | Critical | Stop. Fix now. |

### Calibration Status

The rubric has been authored with concrete score anchors on every point of every dimension. **Calibration against human scores has not started.** Before running LLM-as-judge at scale:

1. Score 20 examples by hand using the rubric anchors.
2. Run the judge on the same 20 examples.
3. Compute Pearson correlation. Target: **≥ 0.8**.
4. If below 0.8, refine the 3-point anchor descriptions (these are typically the ambiguous ones).

---

## Stage Status Summary

| Stage | Artifact(s) | Status | CI cadence |
|-------|-------------|--------|-----------|
| 1 — Golden Sets | `golden/*.yaml` + `run_golden.py` | Active — 15 cases | Every commit |
| 2 — Labeled Scenarios | `scenarios/sc-*.yaml` | Active | Every release |
| 3 — Replay Harnesses | `replays/fixtures/*.json` | Active (7 fixtures — 5 recorded, 2 stubs) | Weekly / on-demand |
| 4 — Rubrics | `rubrics/workout-wiz.yaml` + `run_rubric.py` | Defined — runner available (`run_rubric.py`), calibration not started | Before shipping / on-demand |
| 5 — Experiments | `experiments/*.yaml` + `run_experiment.py` | Scaffolded — `run_experiment.py` + spec format in `evals/experiments/` | On any model/prompt change |

**Stage 3 maintenance:** 5 fixtures are fully recorded across all routing intents. 2 stubs (`coach-progressive-overload.json`, `workout-gen-lower-body.json`) need re-recording against the live API. Re-record all fixtures monthly or when the I/O schema changes.

**To activate Stage 4:** complete the 20-case human calibration run, then wire the LLM judge to consume `rubrics/workout-wiz.yaml` and output per-dimension scores.
