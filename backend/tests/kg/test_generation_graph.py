"""Unit tests for backend/app/kg/generation_graph.py.

All tests mock the LLM — no live API calls are made.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.kg.generation_graph import (
    GenerationState,
    RecommendedExercise,
    WorkoutRecommendation,
    _fallback_node,
    _safety_gate_node,
    _validate_context_node,
    build_generation_graph,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_safe_exercises(n: int = 2) -> list[dict[str, Any]]:
    return [
        {
            "id": f"ex-{i}",
            "name": f"Exercise {i}",
            "muscle_groups": ["chest"],
            "equipment_required": ["barbell"],
        }
        for i in range(n)
    ]


def _make_context_slice(
    safe_exercises: list[dict] | None = None,
) -> dict[str, Any]:
    return {
        "member_profile": {"id": "m1", "age": 30, "fitness_level": "intermediate"},
        "safe_exercises": safe_exercises if safe_exercises is not None else _make_safe_exercises(),
        "preferred_exercises": [],
        "vector_hits": [],
        "token_counts": {
            "member_profile": 50,
            "safe_exercises": 100,
            "preferred_exercises": 0,
            "vector_hits": 0,
            "total": 150,
        },
    }


def _make_recommendation() -> WorkoutRecommendation:
    return WorkoutRecommendation(
        exercises=[
            RecommendedExercise(
                exercise_id="ex-0",
                name="Exercise 0",
                sets=3,
                reps=10,
                reasoning="Great for chest strength.",
            )
        ],
        overall_reasoning="Balanced upper-body workout.",
        member_id="m1",
        skipped_exercise_ids=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_build_generation_graph_returns_compiled_graph() -> None:
    """build_generation_graph() should return an object with .ainvoke."""
    graph = build_generation_graph()
    assert hasattr(graph, "ainvoke"), "Compiled graph must expose ainvoke"


@pytest.mark.asyncio
async def test_validate_context_triggers_fallback_when_no_safe_exercises() -> None:
    """validate_context should set fallback_triggered=True when safe_exercises is empty."""
    state: GenerationState = {
        "member_id": "m1",
        "query": "give me a workout",
        "context": _make_context_slice(safe_exercises=[]),
        "fallback_triggered": False,
        "recommendation": None,
        "error": None,
    }

    result = _validate_context_node(state)

    assert result["fallback_triggered"] is True


@pytest.mark.asyncio
async def test_generate_workout_returns_recommendation() -> None:
    """Happy path: mock LLM returns a WorkoutRecommendation."""
    recommendation = _make_recommendation()

    with patch(
        "app.kg.generation_graph.ChatAnthropic",
    ) as mock_chat_cls:
        mock_llm = MagicMock()
        mock_llm_with_structured = MagicMock()
        mock_llm_with_structured.ainvoke = AsyncMock(return_value=recommendation)
        mock_llm.with_structured_output.return_value = mock_llm_with_structured
        mock_chat_cls.return_value = mock_llm

        graph = build_generation_graph()
        result = await graph.ainvoke(
            {
                "member_id": "m1",
                "query": "upper body workout",
                "context": _make_context_slice(),
            }
        )

    assert result.get("recommendation") is not None
    rec = result["recommendation"]
    assert hasattr(rec, "exercises") or isinstance(rec, dict)
    # Handle both Pydantic model and dict return
    exercises = rec.exercises if hasattr(rec, "exercises") else rec.get("exercises", [])
    assert len(exercises) >= 1


@pytest.mark.asyncio
async def test_generate_workout_skips_generation_when_fallback_triggered() -> None:
    """When safe_exercises is empty the generate_workout node must never be called."""
    with patch(
        "app.kg.generation_graph.ChatAnthropic",
    ) as mock_chat_cls:
        mock_llm = MagicMock()
        mock_llm_with_structured = MagicMock()
        mock_llm_with_structured.ainvoke = AsyncMock(return_value=_make_recommendation())
        mock_llm.with_structured_output.return_value = mock_llm_with_structured
        mock_chat_cls.return_value = mock_llm

        graph = build_generation_graph()
        result = await graph.ainvoke(
            {
                "member_id": "m1",
                "query": "leg day",
                "context": _make_context_slice(safe_exercises=[]),
            }
        )

    # LLM should never have been instantiated
    mock_chat_cls.assert_not_called()

    # fallback_triggered should be True in the result
    assert result.get("fallback_triggered") is True


@pytest.mark.asyncio
async def test_validate_context_passes_when_safe_exercises_present() -> None:
    """validate_context should return fallback_triggered=False when safe_exercises exist."""
    state: GenerationState = {
        "member_id": "m1",
        "query": "chest workout",
        "context": _make_context_slice(),
        "fallback_triggered": False,
        "recommendation": None,
        "error": None,
    }

    result = _validate_context_node(state)

    assert result["fallback_triggered"] is False


@pytest.mark.asyncio
async def test_validate_context_triggers_fallback_when_context_is_none() -> None:
    """validate_context should set fallback_triggered=True when context is None."""
    state: GenerationState = {
        "member_id": "m1",
        "query": "any workout",
        "context": None,
        "fallback_triggered": False,
        "recommendation": None,
        "error": None,
    }

    result = _validate_context_node(state)

    assert result["fallback_triggered"] is True


# ---------------------------------------------------------------------------
# Safety gate tests
# ---------------------------------------------------------------------------


def test_safety_gate_removes_contraindicated_exercise() -> None:
    """Safety gate removes exercises whose IDs appear in contraindicated_ids."""
    context = _make_context_slice()
    context["contraindicated_ids"] = ["ex-0"]

    rec = _make_recommendation()  # contains ex-0
    state: GenerationState = {
        "member_id": "m1",
        "query": "upper body workout",
        "context": context,
        "recommendation": rec,
        "fallback_triggered": False,
        "error": None,
    }

    result = _safety_gate_node(state)

    assert "recommendation" in result
    final_rec = result["recommendation"]
    exercise_ids = [e.exercise_id for e in final_rec.exercises]
    assert "ex-0" not in exercise_ids
    assert "ex-0" in final_rec.skipped_exercise_ids
    assert "(Removed 1 contraindicated exercise(s).)" in final_rec.overall_reasoning


def test_safety_gate_passes_clean_recommendation() -> None:
    """Safety gate leaves recommendation unchanged when no contraindicated IDs match."""
    context = _make_context_slice()
    context["contraindicated_ids"] = ["some-other-id"]

    # Build a recommendation with 2 exercises so the fallback threshold (< 2) is not hit
    rec = WorkoutRecommendation(
        exercises=[
            RecommendedExercise(
                exercise_id="ex-1",
                name="Exercise 1",
                sets=3,
                reps=10,
                reasoning="Good for back.",
            ),
            RecommendedExercise(
                exercise_id="ex-2",
                name="Exercise 2",
                sets=3,
                reps=12,
                reasoning="Good for legs.",
            ),
        ],
        overall_reasoning="Balanced workout.",
        member_id="m1",
        skipped_exercise_ids=[],
    )
    state: GenerationState = {
        "member_id": "m1",
        "query": "upper body workout",
        "context": context,
        "recommendation": rec,
        "fallback_triggered": False,
        "error": None,
    }

    result = _safety_gate_node(state)

    # No exercises removed, no fallback triggered
    assert result.get("fallback_triggered") is not True
    # recommendation unchanged (either not in result or identical)
    if "recommendation" in result:
        assert result["recommendation"].exercises == rec.exercises
        assert result["recommendation"].skipped_exercise_ids == rec.skipped_exercise_ids


def test_safety_gate_triggers_fallback_when_too_few_exercises() -> None:
    """Safety gate sets fallback_triggered=True when ≤1 exercise survives filtering."""
    context = _make_context_slice()
    # Mark ex-0 (the only exercise) as contraindicated → 0 survivors
    context["contraindicated_ids"] = ["ex-0"]

    rec = _make_recommendation()  # only has ex-0
    state: GenerationState = {
        "member_id": "m1",
        "query": "upper body workout",
        "context": context,
        "recommendation": rec,
        "fallback_triggered": False,
        "error": None,
    }

    result = _safety_gate_node(state)

    assert result.get("fallback_triggered") is True
    # The contraindicated exercise should still be removed
    final_rec = result.get("recommendation")
    if final_rec is not None:
        assert "ex-0" not in [e.exercise_id for e in final_rec.exercises]


# ---------------------------------------------------------------------------
# Fallback node tests
# ---------------------------------------------------------------------------


def test_fallback_node_uses_safe_exercises_when_triggered() -> None:
    """Fallback node builds a recommendation from the first 3 safe exercises."""
    safe = _make_safe_exercises(5)  # 5 exercises; fallback should pick first 3
    state: GenerationState = {
        "member_id": "m1",
        "query": "workout",
        "context": _make_context_slice(safe_exercises=safe),
        "fallback_triggered": True,
        "recommendation": None,
        "error": None,
    }

    result = _fallback_node(state)

    rec: WorkoutRecommendation = result["recommendation"]
    assert len(rec.exercises) <= 3
    safe_ids = {e["id"] for e in safe}
    for ex in rec.exercises:
        assert ex.exercise_id in safe_ids
    assert "injury" in rec.overall_reasoning.lower() or "constraint" in rec.overall_reasoning.lower()


def test_fallback_node_uses_empty_list_when_no_safe_exercises() -> None:
    """Fallback node produces empty exercises list when safe_exercises is empty."""
    state: GenerationState = {
        "member_id": "m1",
        "query": "workout",
        "context": _make_context_slice(safe_exercises=[]),
        "fallback_triggered": True,
        "recommendation": None,
        "error": None,
    }

    result = _fallback_node(state)

    rec: WorkoutRecommendation = result["recommendation"]
    assert rec.exercises == []
    assert rec.overall_reasoning != ""


def test_fallback_triggered_by_empty_context() -> None:
    """Graph invoked with context=None or context={} triggers fallback_triggered=True."""
    from app.kg.generation_graph import _validate_context_node

    for ctx in (None, {}):
        state: GenerationState = {
            "member_id": "m1",
            "query": "workout",
            "context": ctx,  # type: ignore[typeddict-item]
            "fallback_triggered": False,
            "recommendation": None,
            "error": None,
        }
        result = _validate_context_node(state)
        assert result.get("fallback_triggered") is True, f"Expected fallback for context={ctx!r}"
