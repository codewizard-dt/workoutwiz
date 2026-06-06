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
