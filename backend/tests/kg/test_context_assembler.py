"""
Unit tests for the context assembler (TASK-058).

All tests use mocks — no live Neo4j or embedding model calls.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_exercise(ex_id: str, name: str = "Exercise", priority_tier: int = 1) -> dict[str, Any]:
    return {
        "id": ex_id,
        "name": name,
        "muscle_groups": ["legs"],
        "movement_patterns": ["squat"],
        "equipment_required": ["barbell"],
        "priority_tier": priority_tier,
        "is_reps": True,
        "is_duration": False,
        "supports_weight": True,
    }


def _make_member_profile() -> dict[str, Any]:
    return {
        "id": "member-1",
        "name": "Alice",
        "goals": ["build muscle"],
        "equipment": ["barbell", "rack"],
        "fitness_level": "intermediate",
        "injury_names": [],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assemble_context_returns_context_slice() -> None:
    """assemble_context() returns a ContextSlice with expected keys and non-zero token_counts."""
    mock_driver = MagicMock()
    profile = _make_member_profile()
    safe = [_make_exercise("ex-1"), _make_exercise("ex-2")]

    with (
        patch("app.kg.context_assembler.get_member_profile", new=AsyncMock(return_value=profile)),
        patch("app.kg.context_assembler.get_safe_exercises", new=AsyncMock(return_value=safe)),
        patch("app.kg.context_assembler._safe_call", new=AsyncMock(return_value=[])),
        patch("app.kg.context_assembler._safe_vector_search", new=AsyncMock(return_value=[])),
    ):
        from app.kg.context_assembler import assemble_context

        result = await assemble_context("member-1", "build a leg workout", mock_driver)

    assert "member_profile" in result
    assert "safe_exercises" in result
    assert "preferred_exercises" in result
    assert "vector_hits" in result
    assert "token_counts" in result
    assert result["token_counts"]["total"] > 0


@pytest.mark.asyncio
async def test_assemble_context_raises_when_member_not_found() -> None:
    """assemble_context() raises ValueError when member_profile is None."""
    mock_driver = MagicMock()

    with (
        patch("app.kg.context_assembler.get_member_profile", new=AsyncMock(return_value=None)),
        patch("app.kg.context_assembler.get_safe_exercises", new=AsyncMock(return_value=[])),
        patch("app.kg.context_assembler._safe_call", new=AsyncMock(return_value=[])),
        patch("app.kg.context_assembler._safe_vector_search", new=AsyncMock(return_value=[])),
    ):
        from app.kg.context_assembler import assemble_context

        with pytest.raises(ValueError, match="not found in Neo4j"):
            await assemble_context("bad-member", "any query", mock_driver)


@pytest.mark.asyncio
async def test_deduplication_removes_preferred_from_vector_hits() -> None:
    """Exercises already in preferred_exercises are excluded from vector_hits."""
    mock_driver = MagicMock()
    profile = _make_member_profile()
    safe = [_make_exercise("ex-1"), _make_exercise("ex-2")]
    preferred = [_make_exercise("ex-1")]

    # Simulate LangChain Document objects with metadata
    doc_ex1 = MagicMock()
    doc_ex1.page_content = "Exercise 1"
    doc_ex1.metadata = {"id": "ex-1", "score": 0.95}

    doc_ex2 = MagicMock()
    doc_ex2.page_content = "Exercise 2"
    doc_ex2.metadata = {"id": "ex-2", "score": 0.80}

    with (
        patch("app.kg.context_assembler.get_member_profile", new=AsyncMock(return_value=profile)),
        patch("app.kg.context_assembler.get_safe_exercises", new=AsyncMock(return_value=safe)),
        patch("app.kg.context_assembler._safe_call", side_effect=[preferred, []]),
        patch("app.kg.context_assembler._safe_vector_search", new=AsyncMock(return_value=[doc_ex1, doc_ex2])),
    ):
        from app.kg.context_assembler import assemble_context

        result = await assemble_context("member-1", "leg workout", mock_driver)

    vector_ids = [v["id"] for v in result["vector_hits"]]
    assert "ex-1" not in vector_ids, "ex-1 should be excluded from vector_hits (already in preferred)"
    assert "ex-2" in vector_ids, "ex-2 should appear in vector_hits"


@pytest.mark.asyncio
async def test_deduplication_filters_unsafe_exercises_from_preferred() -> None:
    """Exercises not in the safe set are excluded from preferred_exercises."""
    mock_driver = MagicMock()
    profile = _make_member_profile()
    safe = [_make_exercise("ex-safe")]
    preferred = [_make_exercise("ex-unsafe")]

    with (
        patch("app.kg.context_assembler.get_member_profile", new=AsyncMock(return_value=profile)),
        patch("app.kg.context_assembler.get_safe_exercises", new=AsyncMock(return_value=safe)),
        patch("app.kg.context_assembler._safe_call", side_effect=[preferred, []]),
        patch("app.kg.context_assembler._safe_vector_search", new=AsyncMock(return_value=[])),
    ):
        from app.kg.context_assembler import assemble_context

        result = await assemble_context("member-1", "workout", mock_driver)

    assert result["preferred_exercises"] == [], "unsafe exercise must be excluded from preferred"


@pytest.mark.asyncio
async def test_token_budget_truncates_safe_exercises() -> None:
    """safe_exercises section is truncated to stay within SAFE_EXERCISES_BUDGET."""
    from app.kg.context_assembler import SAFE_EXERCISES_BUDGET

    mock_driver = MagicMock()
    profile = _make_member_profile()
    # Create 100 large exercise dicts to exceed the budget
    large_exercises = [
        {**_make_exercise(f"ex-{i}"), "extra_data": "x" * 200}
        for i in range(100)
    ]

    with (
        patch("app.kg.context_assembler.get_member_profile", new=AsyncMock(return_value=profile)),
        patch("app.kg.context_assembler.get_safe_exercises", new=AsyncMock(return_value=large_exercises)),
        patch("app.kg.context_assembler._safe_call", new=AsyncMock(return_value=[])),
        patch("app.kg.context_assembler._safe_vector_search", new=AsyncMock(return_value=[])),
    ):
        from app.kg.context_assembler import assemble_context

        result = await assemble_context("member-1", "workout", mock_driver)

    assert len(result["safe_exercises"]) < 100, "safe_exercises should be truncated"
    assert result["token_counts"]["safe_exercises"] <= SAFE_EXERCISES_BUDGET


@pytest.mark.asyncio
async def test_safe_call_returns_empty_list_on_exception() -> None:
    """_safe_call() returns [] when the wrapped function raises an exception."""
    from app.kg.context_assembler import _safe_call

    async def raising_fn(*args: Any, **kwargs: Any) -> list[Any]:
        raise RuntimeError("Something went wrong")

    result = await _safe_call(raising_fn)
    assert result == []


def test_estimate_tokens_approximation() -> None:
    """_estimate_tokens() returns a positive int for any input."""
    from app.kg.context_assembler import _estimate_tokens

    assert _estimate_tokens({"name": "Squat"}) > 0
    # Empty list → "[]" → 2 chars → max(1, 0) = 1
    assert _estimate_tokens([]) == 1


def test_truncate_to_budget_respects_budget() -> None:
    """_truncate_to_budget() never returns a list that exceeds the budget."""
    from app.kg.context_assembler import CHARS_PER_TOKEN, _estimate_tokens, _truncate_to_budget

    items = [{"id": f"ex-{i}", "name": "A" * 50} for i in range(50)]
    budget = 100
    selected, used = _truncate_to_budget(items, budget)

    assert used <= budget
    assert len(selected) <= len(items)
    # Verify each item in selected would fit
    for item in selected:
        assert _estimate_tokens(item) > 0
