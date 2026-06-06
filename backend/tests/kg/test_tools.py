"""Unit tests for backend/app/kg/tools.py.

All Neo4j driver calls, retrieval graph, and generation graph are mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_recommendation(exercises=None, overall_reasoning="Great workout!", skipped_exercise_ids=None):
    rec = MagicMock()
    rec.exercises = exercises or [{"exercise_id": "abc", "sets": 3, "reps": 10}]
    rec.overall_reasoning = overall_reasoning
    rec.skipped_exercise_ids = skipped_exercise_ids or ["skip-1"]
    return rec


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kg_recommend_tool_returns_recommendation_dict() -> None:
    """kg_recommend_tool should return a dict with an 'exercises' key."""
    from app.kg.tools import kg_recommend_tool

    recommendation = _make_recommendation()

    mock_retrieval_graph = AsyncMock()
    mock_retrieval_graph.ainvoke = AsyncMock(return_value={"context": {"member_id": "m1", "exercises": []}})

    mock_generation_graph = AsyncMock()
    mock_generation_graph.ainvoke = AsyncMock(
        return_value={"recommendation": recommendation, "fallback_triggered": False}
    )

    mock_driver = AsyncMock()
    mock_driver.close = AsyncMock()

    with (
        patch("app.kg.tools.neo4j.AsyncGraphDatabase.driver", return_value=mock_driver),
        patch("app.kg.tools.build_retrieval_graph", return_value=mock_retrieval_graph),
        patch("app.kg.tools.build_generation_graph", return_value=mock_generation_graph),
    ):
        result = await kg_recommend_tool.ainvoke({"member_id": "member-1", "query": "upper body workout"})

    assert isinstance(result, dict), "Result should be a dict"
    assert "exercises" in result, "Result should contain 'exercises' key"
    assert "overall_reasoning" in result, "Result should contain 'overall_reasoning' key"
    assert "skipped_exercise_ids" in result, "Result should contain 'skipped_exercise_ids' key"
    assert result["exercises"] == recommendation.exercises
    mock_driver.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_kg_explain_tool_returns_explanation_string() -> None:
    """kg_explain_tool should return a dict with an 'explanation' key containing a string."""
    from app.kg.tools import kg_explain_tool

    mock_driver = AsyncMock()
    mock_driver.close = AsyncMock()

    with (
        patch("app.kg.tools.neo4j.AsyncGraphDatabase.driver", return_value=mock_driver),
        patch(
            "app.kg.tools.explain_skipped_exercise",
            new=AsyncMock(return_value=("'Deadlift' was skipped because it is contraindicated for: lower back strain.", {"event": "kg_explainability", "latency_ms": 5, "query_count": 1, "result_count": 1, "path_depth": 2, "reason_type": "contraindication", "user_id": "member-1", "confidence": 0.625}, 0.625)),
        ),
    ):
        result = await kg_explain_tool.ainvoke({"member_id": "member-1", "exercise_id": "exercise-99"})

    assert isinstance(result, dict), "Result should be a dict"
    assert "explanation" in result, "Result should contain 'explanation' key"
    assert isinstance(result["explanation"], str), "'explanation' value should be a string"
    assert len(result["explanation"]) > 0, "'explanation' should be non-empty"
    mock_driver.close.assert_awaited_once()


def test_kg_tools_have_correct_descriptions() -> None:
    """Both KG tools should have non-empty descriptions."""
    from app.kg.tools import kg_explain_tool, kg_recommend_tool

    assert kg_recommend_tool.description, "kg_recommend_tool should have a non-empty description"
    assert kg_explain_tool.description, "kg_explain_tool should have a non-empty description"
    assert isinstance(kg_recommend_tool.description, str)
    assert isinstance(kg_explain_tool.description, str)


def test_kg_tools_list_contains_both_tools() -> None:
    """KG_TOOLS list should be importable and contain both tools."""
    from app.kg.tools import KG_TOOLS, kg_explain_tool, kg_recommend_tool

    assert isinstance(KG_TOOLS, list), "KG_TOOLS should be a list"
    assert len(KG_TOOLS) == 2, "KG_TOOLS should contain exactly 2 tools"
    assert kg_recommend_tool in KG_TOOLS
    assert kg_explain_tool in KG_TOOLS


def test_kg_tools_have_args_schema() -> None:
    """Both tools should expose args_schema with field descriptions."""
    from app.kg.tools import KGExplainInput, KGRecommendInput, kg_explain_tool, kg_recommend_tool

    assert kg_recommend_tool.args_schema is KGRecommendInput
    assert kg_explain_tool.args_schema is KGExplainInput

    recommend_fields = KGRecommendInput.model_fields
    assert "member_id" in recommend_fields
    assert "query" in recommend_fields
    assert recommend_fields["member_id"].description, "member_id field should have a description"
    assert recommend_fields["query"].description, "query field should have a description"

    explain_fields = KGExplainInput.model_fields
    assert "member_id" in explain_fields
    assert "exercise_id" in explain_fields
    assert explain_fields["member_id"].description, "member_id field should have a description"
    assert explain_fields["exercise_id"].description, "exercise_id field should have a description"
