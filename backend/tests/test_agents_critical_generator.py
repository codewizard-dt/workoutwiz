"""
Critical-path test B: workout generator returns exercises grounded in exercises.json.

Tests verify:
  1. build_workout_tool only uses IDs that exist in exercises.json
  2. Invalid/hallucinated IDs land in invalid_ids_skipped, not in the workout
  3. A fully-valid generated workout contains only real exercise IDs

No API key is required — real exercise data, no LLM calls.

Note on return structure: build_workout_tool returns:
    {
        "goal": str,
        "phases": {"warmup": [...], "main": [...], "cooldown": [...]},
        "total_exercises": int,
        "invalid_ids_skipped": [str, ...],
    }
Each exercise dict in the phases has an "id" field.
"""
import json
import pytest
from pathlib import Path

# Load the real exercises dataset once
_EXERCISES_PATH = Path(__file__).parent.parent.parent / "1-multi-agent" / "exercises.json"
with _EXERCISES_PATH.open() as f:
    _ALL_EXERCISES: list[dict] = json.load(f)

_VALID_IDS: set[str] = {ex["id"] for ex in _ALL_EXERCISES}


# ---------------------------------------------------------------------------
# Helper: collect all exercise dicts across all phases
# ---------------------------------------------------------------------------

def _all_phase_exercises(result: dict) -> list[dict]:
    """Flatten warmup + main + cooldown into a single list of exercise dicts."""
    phases = result.get("phases", {})
    return (
        phases.get("warmup", [])
        + phases.get("main", [])
        + phases.get("cooldown", [])
    )


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
    from app.agents.workout_generator import build_workout_tool

    valid_ids = _real_ids(3)
    result = build_workout_tool.invoke({
        "goal": "strength",
        "exercise_ids": valid_ids,
    })

    for ex in _all_phase_exercises(result):
        assert ex["id"] in valid_ids, (
            f"build_workout_tool included exercise {ex['id']} which was not in the provided list"
        )


# ---------------------------------------------------------------------------
# Test 2: invalid/hallucinated IDs land in invalid_ids_skipped
# ---------------------------------------------------------------------------

def test_invalid_ids_go_to_skipped_not_workout():
    """
    When build_workout_tool receives IDs that don't exist in exercises.json,
    those IDs must appear in invalid_ids_skipped and NOT in any phase.
    """
    from app.agents.workout_generator import build_workout_tool

    real_ids = _real_ids(2)
    fake_ids = ["hallucinated-id-aaaa", "made-up-id-bbbb"]
    all_ids = real_ids + fake_ids

    result = build_workout_tool.invoke({
        "goal": "strength",
        "exercise_ids": all_ids,
    })

    workout_ids = {ex["id"] for ex in _all_phase_exercises(result)}
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
    from app.agents.workout_generator import build_workout_tool

    sampled_ids = _real_ids(5)
    result = build_workout_tool.invoke({
        "goal": "full_body",
        "exercise_ids": sampled_ids,
    })

    for ex in _all_phase_exercises(result):
        assert ex["id"] in _VALID_IDS, (
            f"Exercise ID {ex['id']} in generated workout does not exist in exercises.json"
        )
