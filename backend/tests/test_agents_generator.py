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


def test_generator_llm_error_returns_fallback():
    """Generator node should return a fallback AIMessage when llm.invoke raises."""
    from unittest.mock import patch
    from app.agents.workout_generator import build_workout_generator_graph

    with patch("app.agents.workout_generator.ChatAnthropic") as mock_cls:
        mock_cls.return_value.bind_tools.return_value.invoke.side_effect = Exception("boom")
        compiled = build_workout_generator_graph().compile()
        result = compiled.invoke({
            "messages": [HumanMessage(content="Give me a leg workout")],
            "route_decision": None,
            "user_id": "u1",
            "session_id": "s1",
            "audit_log": [],
        })
    last = result["messages"][-1]
    assert isinstance(last, AIMessage), "expected AIMessage on LLM failure"
    assert last.content, "fallback message should be non-empty"

    audit_log = result["audit_log"]
    gen_entries = [e for e in audit_log if e.get("event") == "generator"]
    assert len(gen_entries) == 1, "expected exactly one generator audit entry"
    entry = gen_entries[0]
    assert entry["tokens_in"] == 0
    assert entry["tokens_out"] == 0


def test_build_workout_tool_emits_non_empty_cooldown():
    """Cooldown phase must be non-empty when recovery-tagged exercises exist in cache."""
    from app.agents import exercises as ex_module

    # Build a cache with 2 strength exercises (warmup/main candidates) + 1 cooldown candidate.
    def _make_exercise(uid: str, name: str, movement_patterns: list[str],
                       is_reps: bool, is_duration: bool, priority_tier: int):
        e = MagicMock()
        e.id = _uuid.UUID(uid)
        e.name = name
        e.muscle_groups = ["full body"]
        e.equipment_required = ["bodyweight"]
        e.movement_patterns = movement_patterns
        e.is_reps = is_reps
        e.is_duration = is_duration
        e.supports_weight = False
        e.priority_tier = priority_tier
        return e

    strength_a = _make_exercise(
        "aaaaaaaa-0000-0000-0000-000000000001", "Push-Up",
        ["push"], is_reps=True, is_duration=False, priority_tier=1,
    )
    strength_b = _make_exercise(
        "aaaaaaaa-0000-0000-0000-000000000002", "Bodyweight Squat",
        ["squat"], is_reps=True, is_duration=False, priority_tier=1,
    )
    regen_exercise = _make_exercise(
        "aaaaaaaa-0000-0000-0000-000000000003", "Static Hamstring Stretch",
        ["regen"], is_reps=False, is_duration=True, priority_tier=2,
    )

    ex_module._cache = [strength_a, strength_b, regen_exercise]
    try:
        workout = build_workout_tool.invoke({
            "goal": "full body",
            "exercise_ids": [str(strength_a.id), str(strength_b.id)],
            "sets": 3,
            "rest_seconds": 90,
        })
        cooldown = workout["phases"]["cooldown"]
        warmup_ids = {e["id"] for e in workout["phases"]["warmup"]}
        main_ids = {e["id"] for e in workout["phases"]["main"]}

        # Cooldown must be non-empty.
        assert len(cooldown) > 0, "cooldown phase must not be empty"

        cached_ids = {str(e.id) for e in ex_module._cache}
        for entry in cooldown:
            # Every cooldown entry must reference a real dataset exercise.
            assert entry["id"] in cached_ids, f"invented cooldown id: {entry['id']}"
            # No cooldown id should overlap warmup or main.
            assert entry["id"] not in warmup_ids, f"cooldown id {entry['id']} also in warmup"
            assert entry["id"] not in main_ids, f"cooldown id {entry['id']} also in main"
            # Dict shape must match warmup/main entries.
            for key in ("id", "name", "sets", "reps", "duration_s", "rest_s"):
                assert key in entry, f"missing key '{key}' in cooldown entry"
    finally:
        ex_module._cache = []


def test_build_workout_tool_empty_cooldown_when_no_recovery_exercises():
    """When cache has no recovery/mobility exercises, cooldown must be [] without raising."""
    from app.agents import exercises as ex_module

    strength = MagicMock()
    strength.id = _uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
    strength.name = "Bench Press"
    strength.muscle_groups = ["chest"]
    strength.equipment_required = ["barbell"]
    strength.movement_patterns = ["push - horizontal"]
    strength.is_reps = True
    strength.is_duration = False
    strength.supports_weight = True
    strength.priority_tier = 1

    ex_module._cache = [strength]
    try:
        workout = build_workout_tool.invoke({
            "goal": "upper body",
            "exercise_ids": [str(strength.id)],
            "sets": 3,
            "rest_seconds": 90,
        })
        assert workout["phases"]["cooldown"] == [], (
            "cooldown should be empty when no recovery-tagged exercises exist"
        )
    finally:
        ex_module._cache = []
