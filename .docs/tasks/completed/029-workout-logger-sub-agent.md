# 029 — Workout Logger Sub-Agent

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [024-router-node](024-router-node.md), [027-coach-sub-agent](027-coach-sub-agent.md), [028-workout-generator-sub-agent](028-workout-generator-sub-agent.md)

## Objective

Implement the workout logger as a separate, composable `StateGraph` that parses a natural-language workout description, fuzzy-matches exercises against `exercises.json` using `rapidfuzz`, and returns a structured JSON workout log — wired into the hub as the `workout_log` node.

## Approach

The sub-agent lives in `src/workout_wiz/agents/workout_logger.py`. It uses a single `log_node` that calls the LLM with a structured output schema (`WorkoutLog` Pydantic model). The LLM extracts exercise names from the user's message; those names are then fuzzy-matched against the exercise dataset using `rapidfuzz.process.extractOne` (threshold ≥ 75) to resolve to canonical exercise IDs. No LangGraph tools are needed — the fuzzy matching happens in Python after the LLM's structured extraction.

## Steps

### 1. Define WorkoutLog output schema  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/agents/workout_logger.py` with the output schema:

```python
import os
from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import process as fuzz_process, fuzz
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END

from workout_wiz.state import AgentState
from workout_wiz.exercises import get_all_exercises


class LoggedSet(BaseModel):
    exercise_name: str = Field(description="The name of the exercise as stated by the user")
    exercise_id: Optional[str] = Field(
        default=None,
        description="UUID of the matched exercise from the database (null if no match found)"
    )
    match_confidence: float = Field(
        default=0.0,
        description="Fuzzy match confidence 0.0-1.0 (1.0 = exact match)"
    )
    sets: Optional[int] = Field(default=None, description="Number of sets performed")
    reps: Optional[int] = Field(default=None, description="Reps per set")
    weight_kg: Optional[float] = Field(default=None, description="Weight in kg (if applicable)")
    duration_s: Optional[int] = Field(default=None, description="Duration in seconds (if applicable)")
    distance_m: Optional[float] = Field(default=None, description="Distance in metres (if applicable)")
    notes: Optional[str] = Field(default=None, description="Any additional notes for this set")


class WorkoutLog(BaseModel):
    raw_input: str = Field(description="The user's original workout description, verbatim")
    logged_sets: list[LoggedSet] = Field(
        description="Structured list of exercises with their metrics, parsed from the user's input"
    )
    unrecognized: list[str] = Field(
        default_factory=list,
        description="Exercise names mentioned that could not be matched to any exercise (confidence < 0.75)"
    )
    parse_notes: Optional[str] = Field(
        default=None,
        description="Any ambiguity or assumptions made during parsing"
    )
```

- [ ] `WorkoutLog` Pydantic model with `logged_sets`, `unrecognized`, `raw_input`, `parse_notes` fields
- [ ] `LoggedSet` has `exercise_name`, `exercise_id`, `match_confidence`, and all metric fields

### 2. Implement fuzzy matching and log node  <!-- agent: general-purpose -->

Add the fuzzy matching helper and the log node to `workout_logger.py`:

```python
_LOGGER_SYSTEM_PROMPT = """You are a workout logging assistant. Parse the user's workout description into a structured format.

For each exercise mentioned, extract:
- The exercise name (as stated by the user)
- Sets and reps (if mentioned), e.g. "3x10" = 3 sets of 10 reps
- Weight (if mentioned), convert to kg if in lbs (1 lb = 0.453592 kg)
- Duration (if mentioned), convert to seconds
- Distance (if mentioned), convert to metres

Be precise. If an exercise is mentioned multiple times, create separate entries.
If information is not mentioned, leave the field null.
If you're making assumptions, note them in parse_notes.
"""


def _fuzzy_match_exercise(name: str, exercises: list) -> tuple[str | None, float]:
    """Fuzzy-match exercise name against the dataset. Returns (exercise_id, confidence 0-1)."""
    if not exercises:
        return None, 0.0
    exercise_names = [e.name for e in exercises]
    result = fuzz_process.extractOne(name, exercise_names, scorer=fuzz.token_sort_ratio)
    if result is None:
        return None, 0.0
    matched_name, score, idx = result
    confidence = score / 100.0
    if confidence < 0.75:
        return None, confidence
    return exercises[idx].id, confidence


def _log_node(state: AgentState) -> dict:
    model_name = os.getenv("LOGGER_MODEL", "claude-haiku-4-5-20251001")
    llm = ChatAnthropic(model=model_name).with_structured_output(WorkoutLog)
    exercises = get_all_exercises()

    last_human = next(
        (m for m in reversed(state["messages"]) if hasattr(m, "type") and m.type == "human"),
        None,
    )
    user_text = last_human.content if last_human else ""

    workout_log: WorkoutLog = llm.invoke([
        SystemMessage(content=_LOGGER_SYSTEM_PROMPT),
        *state["messages"],
    ])

    # Resolve exercise IDs via fuzzy matching
    unrecognized = []
    for logged_set in workout_log.logged_sets:
        if logged_set.exercise_id is None:
            exercise_id, confidence = _fuzzy_match_exercise(logged_set.exercise_name, exercises)
            logged_set.exercise_id = exercise_id
            logged_set.match_confidence = confidence
            if exercise_id is None:
                unrecognized.append(logged_set.exercise_name)

    workout_log.unrecognized = unrecognized

    from langchain_core.messages import AIMessage
    response_text = (
        f"Logged {len(workout_log.logged_sets)} exercise(s).\n"
        + "\n".join(
            f"• {s.exercise_name}: "
            + (f"{s.sets}×{s.reps}" if s.sets and s.reps else "")
            + (f" @ {s.weight_kg}kg" if s.weight_kg else "")
            + (f" ({int(s.match_confidence * 100)}% match)" if s.exercise_id else " [unrecognized]")
            for s in workout_log.logged_sets
        )
        + (f"\nUnrecognized: {', '.join(unrecognized)}" if unrecognized else "")
    )

    return {
        "messages": [AIMessage(content=response_text)],
    }


def build_workout_logger_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("log", _log_node)
    graph.add_edge(START, "log")
    graph.add_edge("log", END)
    return graph


workout_logger_graph = build_workout_logger_graph().compile()
```

- [ ] `_fuzzy_match_exercise` uses `rapidfuzz.process.extractOne` with `fuzz.token_sort_ratio`
- [ ] Match threshold is 0.75 (75 out of 100 score)
- [ ] `_log_node` uses `with_structured_output(WorkoutLog)` 
- [ ] Unrecognized exercises (confidence < 0.75) go into `workout_log.unrecognized` list
- [ ] Response message summarizes what was logged

### 3. Wire into hub  <!-- agent: general-purpose -->

In `1-multi-agent/src/workout_wiz/hub.py`, replace `_workout_log_stub` with the imported logger graph:

```python
from workout_wiz.agents.workout_logger import workout_logger_graph

# In build_hub_graph():
# Replace: graph.add_node("workout_log", _workout_log_stub)
# With:
graph.add_node("workout_log", workout_logger_graph)
```

Remove `_workout_log_stub` from `hub.py`.

- [ ] `hub.py` imports `workout_logger_graph`
- [ ] `graph.add_node("workout_log", workout_logger_graph)` replaces the stub
- [ ] `_workout_log_stub` removed from `hub.py`

### 4. Write tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_workout_logger.py`:

```python
from workout_wiz.agents.workout_logger import (
    build_workout_logger_graph,
    _fuzzy_match_exercise,
    WorkoutLog,
    LoggedSet,
)
from workout_wiz.exercises import get_all_exercises


def test_logger_graph_compiles():
    graph = build_workout_logger_graph()
    assert graph.compile() is not None


def test_fuzzy_match_exact():
    exercises = get_all_exercises()
    # Pick a real exercise name and match it exactly
    first = exercises[0]
    exercise_id, confidence = _fuzzy_match_exercise(first.name, exercises)
    assert exercise_id == first.id
    assert confidence >= 0.99


def test_fuzzy_match_partial():
    exercises = get_all_exercises()
    # "bench" should match "Bench Press" or similar
    exercise_id, confidence = _fuzzy_match_exercise("bench press", exercises)
    # May or may not match depending on dataset; at minimum should not crash
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


def test_fuzzy_match_below_threshold():
    exercises = get_all_exercises()
    exercise_id, confidence = _fuzzy_match_exercise("xyzzy nonexistent", exercises)
    assert exercise_id is None
    assert confidence < 0.75


def test_workout_log_schema():
    log = WorkoutLog(
        raw_input="3x10 squats at 100kg",
        logged_sets=[
            LoggedSet(
                exercise_name="squats",
                sets=3,
                reps=10,
                weight_kg=100.0,
            )
        ],
    )
    assert log.raw_input == "3x10 squats at 100kg"
    assert len(log.logged_sets) == 1
    assert log.logged_sets[0].weight_kg == 100.0
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_workout_logger.py -v`

- [ ] All 5 tests pass (no real LLM calls — pure function tests)

### 5. Verify hub still compiles  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "from workout_wiz.hub import hub; print('Hub OK')"
```

- [ ] Exits 0 with "Hub OK"

## Acceptance Criteria

- [ ] `src/workout_wiz/agents/workout_logger.py` exists with `WorkoutLog`, `LoggedSet`, `_fuzzy_match_exercise`, `_log_node`
- [ ] Fuzzy matching uses `rapidfuzz.process.extractOne` with threshold 0.75
- [ ] `_log_node` uses `with_structured_output(WorkoutLog)` — not regex parsing
- [ ] Unrecognized exercises appear in `unrecognized` list, not silently dropped
- [ ] `workout_logger_graph` wired into hub as `workout_log` node (stub removed)
- [ ] `pytest tests/test_workout_logger.py` passes (5/5)

---
**UAT**: [`.docs/uat/029-workout-logger-sub-agent.uat.md`](../uat/029-workout-logger-sub-agent.uat.md)
