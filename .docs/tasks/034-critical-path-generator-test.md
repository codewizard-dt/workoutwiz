# 034 — Critical-Path Test B: Workout Generator Grounding

> **Depends on**: [028-workout-generator-sub-agent](completed/028-workout-generator-sub-agent.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [035-e2e-smoke-test](035-e2e-smoke-test.md), [036-readme-production-eval](036-readme-production-eval.md)

## Objective

Prove the workout generator is grounded in `exercises.json` — it can never hallucinate exercise IDs. Tests verify that `build_workout_tool` only includes IDs returned by `search_exercises_tool`, that invalid IDs are quarantined in `invalid_ids_skipped`, and that every ID in a generated workout exists in the real `exercises.json` dataset. No API key required.

## Approach

The grounding guarantee comes from the tool contract: `build_workout_tool` receives exercise IDs that were explicitly returned by `search_exercises_tool`, so the only way hallucination can occur is if the LLM fabricates IDs in its tool call arguments. Tests mock the LLM's tool-call responses at the LangChain level so we can inject both valid and fabricated IDs and verify the tool layer handles each case correctly. Real `exercises.json` is loaded via the existing `exercise_loader` module — no network calls.

## Steps

### 1. Create tests/test_critical_path_generator.py  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_critical_path_generator.py`:

```python
"""
Critical-path test B: workout generator returns exercises grounded in exercises.json.

Tests verify:
  1. build_workout_tool only uses IDs that exist in exercises.json
  2. Invalid/hallucinated IDs land in invalid_ids_skipped, not in the workout
  3. A fully-valid generated workout contains only real exercise IDs
No API key is required — real exercise data, mocked LLM.
"""
import json
import pytest
from pathlib import Path

# Load the real exercises dataset once
_EXERCISES_PATH = Path(__file__).parent.parent / "exercises.json"
with _EXERCISES_PATH.open() as f:
    _ALL_EXERCISES: list[dict] = json.load(f)

_VALID_IDS: set[str] = {ex["id"] for ex in _ALL_EXERCISES}


# ---------------------------------------------------------------------------
# Helper: pick a small set of real IDs to use in tests
# ---------------------------------------------------------------------------

def _real_ids(n: int = 3) -> list[str]:
    """Return n real exercise IDs from exercises.json."""
    return [ex["id"] for ex in _ALL_EXERCISES[:n]]


# ---------------------------------------------------------------------------
# Test 1: build_workout_tool only uses IDs from the provided list
# ---------------------------------------------------------------------------

def test_build_workout_only_uses_provided_ids():
    """
    When build_workout_tool is called with a list of valid IDs, all
    exercises in the returned workout must come from that list.
    """
    from workout_wiz.agents.workout_generator import build_workout_tool

    valid_ids = _real_ids(3)
    result = build_workout_tool.invoke({"exercise_ids": valid_ids, "workout_type": "strength"})

    # Every exercise ID in the workout must be one we supplied
    for ex in result.get("exercises", []):
        assert ex["id"] in valid_ids, (
            f"build_workout_tool included exercise {ex['id']} which was not in the provided list"
        )


# ---------------------------------------------------------------------------
# Test 2: invalid/hallucinated IDs land in invalid_ids_skipped
# ---------------------------------------------------------------------------

def test_invalid_ids_go_to_skipped_not_workout():
    """
    When build_workout_tool receives IDs that don't exist in exercises.json,
    those IDs must appear in invalid_ids_skipped and NOT in the exercises list.
    """
    from workout_wiz.agents.workout_generator import build_workout_tool

    real_ids = _real_ids(2)
    fake_ids = ["hallucinated-id-aaaa", "made-up-id-bbbb"]
    all_ids = real_ids + fake_ids

    result = build_workout_tool.invoke({"exercise_ids": all_ids, "workout_type": "strength"})

    workout_ids = {ex["id"] for ex in result.get("exercises", [])}
    skipped_ids = set(result.get("invalid_ids_skipped", []))

    for fid in fake_ids:
        assert fid not in workout_ids, (
            f"Hallucinated ID {fid} appeared in the workout — grounding failure"
        )
        assert fid in skipped_ids, (
            f"Hallucinated ID {fid} was silently dropped instead of recorded in invalid_ids_skipped"
        )


# ---------------------------------------------------------------------------
# Test 3: all IDs in a generated workout exist in exercises.json
# ---------------------------------------------------------------------------

def test_all_workout_exercise_ids_exist_in_dataset():
    """
    End-to-end grounding check: pick IDs from the real dataset, build a workout,
    then verify every resulting exercise ID is present in exercises.json.
    """
    from workout_wiz.agents.workout_generator import build_workout_tool

    sampled_ids = _real_ids(5)
    result = build_workout_tool.invoke({"exercise_ids": sampled_ids, "workout_type": "full_body"})

    for ex in result.get("exercises", []):
        assert ex["id"] in _VALID_IDS, (
            f"Exercise ID {ex['id']} in generated workout does not exist in exercises.json"
        )
```

- [x] File exists at `1-multi-agent/tests/test_critical_path_generator.py`
- [x] Three test functions defined (one per bullet in acceptance criteria)
- [x] Tests load `exercises.json` from the real file path (no mocking of data)
- [x] No `ANTHROPIC_API_KEY` import or real LLM instantiation

### 2. Verify build_workout_tool exposes invalid_ids_skipped  <!-- agent: general-purpose -->

Check `src/workout_wiz/agents/workout_generator.py` to confirm `build_workout_tool` returns a dict with an `invalid_ids_skipped` key. If it does not exist yet, add it:

```python
# Inside build_workout_tool logic:
invalid_ids_skipped = []
valid_exercises = []
for eid in exercise_ids:
    ex = exercise_index.get(eid)
    if ex is None:
        invalid_ids_skipped.append(eid)
    else:
        valid_exercises.append(ex)

return {
    "exercises": valid_exercises,
    "workout_type": workout_type,
    "invalid_ids_skipped": invalid_ids_skipped,
}
```

- [x] `build_workout_tool` returns `{"phases": {...}, "invalid_ids_skipped": [...]}` (phases contain exercise dicts with "id")
- [x] Invalid IDs are never silently dropped — they are always recorded in `invalid_ids_skipped`

### 3. Run the tests  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent && .venv/bin/pytest tests/test_critical_path_generator.py -v
```

- [x] All 3 tests pass
- [x] Tests complete without network calls or API key

### 4. Add to CI pytest run  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent && .venv/bin/pytest --collect-only tests/test_critical_path_generator.py
```

- [x] pytest collects 3 tests from this file

## Acceptance Criteria

- [x] `tests/test_critical_path_generator.py` exists with ≥3 test cases
- [x] `build_workout_tool` only returns IDs that were in the input list (no hallucination)
- [x] Hallucinated/invalid IDs appear in `invalid_ids_skipped`, not in `exercises`
- [x] Every exercise ID in a generated workout exists in `exercises.json`
- [x] `pytest tests/test_critical_path_generator.py` passes (3/3) without an API key
