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
    phases = result.get("phases", {})
    all_exercises = (
        phases.get("warmup", [])
        + phases.get("main", [])
        + phases.get("cooldown", [])
    )
    for ex in all_exercises:
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

    phases = result.get("phases", {})
    all_exercises = (
        phases.get("warmup", [])
        + phases.get("main", [])
        + phases.get("cooldown", [])
    )
    workout_ids = {ex["id"] for ex in all_exercises}
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

    phases = result.get("phases", {})
    all_exercises = (
        phases.get("warmup", [])
        + phases.get("main", [])
        + phases.get("cooldown", [])
    )
    for ex in all_exercises:
        assert ex["id"] in _VALID_IDS, (
            f"Exercise ID {ex['id']} in generated workout does not exist in exercises.json"
        )
