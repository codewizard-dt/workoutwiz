"""Workout generator sub-agent for the workout-wiz multi-agent system.

build_workout_tool constructs a structured workout plan from a list of
exercise IDs returned by search_exercises_tool.  It validates every ID
against the exercises.json dataset and places invalid/hallucinated IDs
in ``invalid_ids_skipped`` so callers can detect grounding failures.

No database or API key is required — exercises are loaded from the
bundled exercises.json file at import time.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Load exercises.json once at import time (no DB / network required)
# ---------------------------------------------------------------------------

_EXERCISES_JSON = Path(__file__).parent.parent.parent.parent / "exercises.json"

with _EXERCISES_JSON.open() as _f:
    _RAW_EXERCISES: list[dict[str, Any]] = json.load(_f)

# Index by string ID for O(1) lookups
_EXERCISE_INDEX: dict[str, dict[str, Any]] = {str(e["id"]): e for e in _RAW_EXERCISES}


# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------

class SearchExercisesInput(BaseModel):
    muscle_groups: list[str] = Field(default_factory=list, description="Target muscle groups")
    equipment: list[str] = Field(default_factory=list, description="Available equipment")
    movement_patterns: list[str] = Field(default_factory=list, description="Movement pattern filters")
    max_results: int = Field(default=10, description="Maximum number of exercises to return")


class BuildWorkoutInput(BaseModel):
    exercise_ids: list[str] = Field(description="Exercise IDs returned by search_exercises_tool")
    workout_type: str = Field(default="strength", description="Type of workout (e.g. strength, cardio, full_body)")
    sets: int = Field(default=3, description="Number of sets per exercise")
    rest_seconds: int = Field(default=90, description="Rest between sets in seconds")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool(args_schema=SearchExercisesInput)
def search_exercises_tool(
    muscle_groups: list[str] | None = None,
    equipment: list[str] | None = None,
    movement_patterns: list[str] | None = None,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search exercises from exercises.json by muscle group, equipment, or movement pattern."""
    results = list(_RAW_EXERCISES)

    if muscle_groups:
        mg_lower = [m.lower() for m in muscle_groups]
        results = [
            e for e in results
            if any(m in " ".join(e.get("muscle_groups", [])).lower() for m in mg_lower)
        ]

    if equipment:
        eq_lower = [eq.lower() for eq in equipment]
        results = [
            e for e in results
            if any(eq in " ".join(e.get("equipment_required", [])).lower() for eq in eq_lower)
        ]

    if movement_patterns:
        mp_lower = [p.lower() for p in movement_patterns]
        results = [
            e for e in results
            if any(p in json.dumps(e.get("movement_patterns", {})).lower() for p in mp_lower)
        ]

    results.sort(key=lambda e: e.get("priority_tier", 99))
    return results[:max_results]


@tool(args_schema=BuildWorkoutInput)
def build_workout_tool(
    exercise_ids: list[str],
    workout_type: str = "strength",
    sets: int = 3,
    rest_seconds: int = 90,
) -> dict[str, Any]:
    """Build a structured workout plan from a list of exercise IDs.

    Only uses IDs that exist in exercises.json.  Any ID not found in
    the dataset is quarantined in ``invalid_ids_skipped`` — it will
    never appear in the returned workout phases.
    """
    valid: list[dict[str, Any]] = []
    invalid_ids_skipped: list[str] = []

    for eid in exercise_ids:
        ex = _EXERCISE_INDEX.get(str(eid))
        if ex is None:
            invalid_ids_skipped.append(eid)
        else:
            valid.append(ex)

    warmup = valid[:2] if len(valid) >= 3 else []
    main = valid[2:] if len(valid) >= 3 else valid
    cooldown: list[dict[str, Any]] = []

    def _to_dict(e: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(e["id"]),
            "name": e["name"],
            "sets": sets,
            "reps": "10-12" if e.get("is_reps") else None,
            "duration_s": 30 if e.get("is_duration") else None,
            "rest_s": rest_seconds,
        }

    return {
        "workout_type": workout_type,
        "phases": {
            "warmup": [_to_dict(e) for e in warmup],
            "main": [_to_dict(e) for e in main],
            "cooldown": cooldown,
        },
        "total_exercises": len(valid),
        "invalid_ids_skipped": invalid_ids_skipped,
    }
