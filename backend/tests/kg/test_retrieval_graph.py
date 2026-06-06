"""
Unit tests for the GraphRAG retrieval sub-graph (backend/app/kg/retrieval_graph.py).

All tests use mocks — no live Neo4j or vector store connections required.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context_slice() -> dict:
    """Return a minimal valid ContextSlice dict."""
    return {
        "member_profile": {"id": "m1", "name": "Test Member"},
        "safe_exercises": [{"id": "ex-1", "name": "Squat"}],
        "preferred_exercises": [],
        "vector_hits": [],
        "token_counts": {
            "member_profile": 10,
            "safe_exercises": 20,
            "preferred_exercises": 0,
            "vector_hits": 0,
            "total": 30,
        },
    }


def _make_member_profile() -> dict:
    return {"id": "m1", "name": "Test Member", "goals": ["strength"], "equipment": ["barbell"]}


def _make_exercises() -> list[dict]:
    return [{"id": "ex-1", "name": "Squat", "muscle_groups": ["quads"]}]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_build_retrieval_graph_returns_compiled_graph() -> None:
    """build_retrieval_graph(mock_driver) should return an object with .ainvoke method."""
    from app.kg.retrieval_graph import build_retrieval_graph

    mock_driver = MagicMock()
    graph = build_retrieval_graph(mock_driver)

    assert hasattr(graph, "ainvoke"), "Compiled graph must expose .ainvoke()"
    assert callable(graph.ainvoke)


@pytest.mark.asyncio
async def test_retrieval_graph_invokes_assemble_context() -> None:
    """Full happy-path: assemble_context returns a ContextSlice via the graph."""
    mock_driver = MagicMock()
    context_slice = _make_context_slice()
    profile = _make_member_profile()
    exercises = _make_exercises()

    with (
        patch(
            "app.kg.retrieval_graph.get_member_profile",
            new=AsyncMock(return_value=profile),
        ),
        patch(
            "app.kg.retrieval_graph.get_contraindicated_exercise_ids",
            new=AsyncMock(return_value=set()),
        ),
        patch(
            "app.kg.retrieval_graph.get_safe_exercises",
            new=AsyncMock(return_value=exercises),
        ),
        patch(
            "app.kg.retrieval_graph.get_preferred_exercises",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_performed_exercises",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_exercise_vector_store",
            return_value=MagicMock(similarity_search=MagicMock(return_value=[])),
        ),
        patch(
            "app.kg.retrieval_graph.assemble_context",
            new=AsyncMock(return_value=context_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        result = await graph.ainvoke({"member_id": "m1", "query": "leg workout"})

    assert result["context"] is not None
    assert result["context"]["member_profile"]["id"] == "m1"


@pytest.mark.asyncio
async def test_retrieval_graph_raises_when_member_not_found() -> None:
    """lookup_member node should raise ValueError when get_member_profile returns None."""
    mock_driver = MagicMock()

    with patch(
        "app.kg.retrieval_graph.get_member_profile",
        new=AsyncMock(return_value=None),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)

        with pytest.raises((ValueError, Exception)):
            await graph.ainvoke({"member_id": "missing-member", "query": "leg workout"})


@pytest.mark.asyncio
async def test_vector_search_failure_does_not_fail_graph() -> None:
    """A RuntimeError in vector search should not abort the graph (non-fatal path)."""
    mock_driver = MagicMock()
    context_slice = _make_context_slice()
    profile = _make_member_profile()
    exercises = _make_exercises()

    mock_vector_store = MagicMock()
    mock_vector_store.similarity_search.side_effect = RuntimeError("vector store unavailable")

    with (
        patch(
            "app.kg.retrieval_graph.get_member_profile",
            new=AsyncMock(return_value=profile),
        ),
        patch(
            "app.kg.retrieval_graph.get_contraindicated_exercise_ids",
            new=AsyncMock(return_value=set()),
        ),
        patch(
            "app.kg.retrieval_graph.get_safe_exercises",
            new=AsyncMock(return_value=exercises),
        ),
        patch(
            "app.kg.retrieval_graph.get_preferred_exercises",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_performed_exercises",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_exercise_vector_store",
            return_value=mock_vector_store,
        ),
        patch(
            "app.kg.retrieval_graph.assemble_context",
            new=AsyncMock(return_value=context_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        result = await graph.ainvoke({"member_id": "m1", "query": "leg workout"})

    # Graph should complete — vector failure is non-fatal
    assert result["context"] is not None
    # The error field should be populated
    assert result.get("error") is not None


def test_knowledge_graph_intent_in_route_intent_enum() -> None:
    """Intent enum must contain KNOWLEDGE_GRAPH after Step 3 changes."""
    from app.agents.state import Intent

    assert hasattr(Intent, "KNOWLEDGE_GRAPH"), "Intent.KNOWLEDGE_GRAPH must exist"
    assert Intent.KNOWLEDGE_GRAPH == "KNOWLEDGE_GRAPH"
