from langchain_core.messages import AIMessage, HumanMessage

from app.agents.workout_generator import (
    build_workout_generator_graph,
    build_workout_tool,
    search_exercises_tool,
)


import uuid as _uuid
from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def populate_exercise_cache():
    from app.agents import exercises as ex_module
    fake = MagicMock()
    fake.id = _uuid.UUID("00000000-0000-0000-0000-000000000002")
    fake.name = "Barbell Squat"
    fake.muscle_groups = ["quadriceps", "glutes"]
    fake.equipment_required = ["barbell"]
    fake.movement_patterns = ["squat"]
    fake.is_reps = True
    fake.is_duration = False
    fake.supports_weight = True
    fake.priority_tier = 1
    ex_module._cache = [fake]
    yield
    ex_module._cache = []


def test_generator_graph_compiles():
    graph = build_workout_generator_graph()
    assert graph.compile() is not None


def test_search_exercises_tool_returns_results():
    results = search_exercises_tool.invoke({"muscle_groups": ["quadriceps"]})
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("id" in r and "name" in r for r in results)


def test_search_exercises_tool_respects_max_results():
    results = search_exercises_tool.invoke({"max_results": 3})
    assert len(results) <= 3


def test_build_workout_tool_valid_ids():
    exercises = search_exercises_tool.invoke({"max_results": 5})
    ids = [e["id"] for e in exercises]
    workout = build_workout_tool.invoke({
        "goal": "full body strength",
        "exercise_ids": ids,
        "sets": 3,
        "rest_seconds": 90,
    })
    assert workout["total_exercises"] == len(ids)
    assert workout["invalid_ids_skipped"] == []
    assert "phases" in workout


def test_build_workout_tool_rejects_invalid_ids():
    workout = build_workout_tool.invoke({
        "goal": "test",
        "exercise_ids": ["00000000-0000-0000-0000-000000000000"],
        "sets": 3,
        "rest_seconds": 60,
    })
    assert workout["total_exercises"] == 0
    assert "00000000-0000-0000-0000-000000000000" in workout["invalid_ids_skipped"]


def test_hub_imports_cleanly():
    from app.agents.hub import hub
    assert hub is not None
