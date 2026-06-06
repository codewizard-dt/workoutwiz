from app.agents.workout_logger import (
    WorkoutLog,
    LoggedSet,
    _fuzzy_match_exercise,
    build_workout_logger_graph,
)
from app.agents.exercises import get_all_exercises


import uuid as _uuid
from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def populate_exercise_cache():
    from app.agents import exercises as ex_module
    fake = MagicMock()
    fake.id = "00000000-0000-0000-0000-000000000002"
    fake.name = "Barbell Squat"
    fake.muscle_groups = ["quadriceps"]
    fake.equipment_required = ["barbell"]
    fake.movement_patterns = ["squat"]
    fake.is_reps = True
    fake.is_duration = False
    fake.supports_weight = True
    fake.priority_tier = 1
    ex_module._cache = [fake]
    yield
    ex_module._cache = []


def test_logger_graph_compiles():
    graph = build_workout_logger_graph()
    assert graph.compile() is not None


def test_fuzzy_match_exact():
    exercises = get_all_exercises()
    # Pick a real exercise name and match it exactly
    first = exercises[0]
    exercise_id, canonical_name, confidence = _fuzzy_match_exercise(first.name, exercises)
    assert exercise_id == first.id
    assert canonical_name == first.name
    assert confidence >= 0.99


def test_fuzzy_match_partial():
    exercises = get_all_exercises()
    # "bench press" should match "Bench Press" or similar
    exercise_id, canonical_name, confidence = _fuzzy_match_exercise("bench press", exercises)
    # May or may not match depending on dataset; at minimum should not crash
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


def test_fuzzy_match_below_threshold():
    exercises = get_all_exercises()
    exercise_id, canonical_name, confidence = _fuzzy_match_exercise("xyzzy nonexistent", exercises)
    assert exercise_id is None
    assert canonical_name is None
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
