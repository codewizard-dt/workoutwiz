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
    """Full happy-path: assemble_context_from_parts returns a ContextSlice via the graph."""
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
            "app.kg.retrieval_graph.assemble_context_from_parts",
            new=AsyncMock(return_value=context_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        result = await graph.ainvoke({"member_id": "m1", "query": "leg workout"})

    assert result["context"] is not None
    assert result["context"]["member_profile"]["id"] == "m1"


@pytest.mark.asyncio
async def test_retrieval_graph_returns_vector_only_when_member_not_found() -> None:
    """When get_member_profile returns None, graph returns a vector-only ContextSlice.

    The lookup_member node converts None to an empty profile dict. The assemble node
    then falls back to the vector-only path via assemble_context_from_parts.
    """
    mock_driver = MagicMock()
    context_slice = _make_context_slice()
    context_slice["member_profile"] = {}
    context_slice["safe_exercises"] = []

    with (
        patch(
            "app.kg.retrieval_graph.get_member_profile",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.kg.retrieval_graph.get_contraindicated_exercise_ids",
            new=AsyncMock(return_value=set()),
        ),
        patch(
            "app.kg.retrieval_graph.get_contraindicated_provenance",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_safe_exercises",
            new=AsyncMock(return_value=[]),
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
            "app.kg.retrieval_graph.get_avoided_exercises",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_exercise_vector_store",
            return_value=MagicMock(similarity_search=MagicMock(return_value=[])),
        ),
        patch(
            "app.kg.retrieval_graph.assemble_context_from_parts",
            new=AsyncMock(return_value=context_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        result = await graph.ainvoke({"member_id": "missing-member", "query": "leg workout"})

    # Graph completes with a vector-only context (no raise)
    assert result["context"] is not None
    assert result["context"]["member_profile"] == {}


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
            "app.kg.retrieval_graph.assemble_context_from_parts",
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


@pytest.mark.asyncio
async def test_retrieval_graph_audit_log_contains_all_5_entries() -> None:
    """After a full retrieval graph invocation, audit_log must contain 5 retrieval entries."""
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
            "app.kg.retrieval_graph.assemble_context_from_parts",
            new=AsyncMock(return_value=context_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        result = await graph.ainvoke({"member_id": "m1", "query": "leg workout", "user_id": "user-42"})

    audit_log: list = result.get("audit_log", [])
    retrieval_events = [e["event"] for e in audit_log if e["event"].startswith("retrieval_")]

    assert len(retrieval_events) == 5, f"Expected 5 retrieval audit entries, got: {retrieval_events}"
    assert set(retrieval_events) == {
        "retrieval_lookup_member",
        "retrieval_injury_traversal",
        "retrieval_preference_traversal",
        "retrieval_vector_search",
        "retrieval_assemble",
    }

    retrieval_entries = [e for e in audit_log if e["event"].startswith("retrieval_")]
    assert all(e["latency_ms"] >= 0 for e in retrieval_entries), "All entries must have non-negative latency_ms"
    assert all("user_id" in e for e in retrieval_entries), "All entries must have user_id"
    # result_count present in nodes that produce it
    for entry in retrieval_entries:
        if entry["event"] in ("retrieval_lookup_member", "retrieval_injury_traversal",
                               "retrieval_preference_traversal", "retrieval_vector_search"):
            assert "result_count" in entry, f"Missing result_count in {entry['event']}"


@pytest.mark.asyncio
async def test_assemble_node_does_not_re_run_traversals() -> None:
    """Each traversal function must be called exactly once per graph invocation.

    Regression test: the assemble node must not re-query Neo4j by calling
    traversal functions a second time — it reads from state instead.
    """
    mock_driver = MagicMock()
    profile = _make_member_profile()
    exercises = _make_exercises()
    context_slice = _make_context_slice()

    mock_get_member_profile = AsyncMock(return_value=profile)
    mock_get_safe_exercises = AsyncMock(return_value=exercises)
    mock_get_preferred = AsyncMock(return_value=[])
    mock_get_performed = AsyncMock(return_value=[])
    mock_get_avoided = AsyncMock(return_value=[])

    with (
        patch(
            "app.kg.retrieval_graph.get_member_profile",
            new=mock_get_member_profile,
        ),
        patch(
            "app.kg.retrieval_graph.get_contraindicated_exercise_ids",
            new=AsyncMock(return_value=set()),
        ),
        patch(
            "app.kg.retrieval_graph.get_contraindicated_provenance",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_safe_exercises",
            new=mock_get_safe_exercises,
        ),
        patch(
            "app.kg.retrieval_graph.get_preferred_exercises",
            new=mock_get_preferred,
        ),
        patch(
            "app.kg.retrieval_graph.get_performed_exercises",
            new=mock_get_performed,
        ),
        patch(
            "app.kg.retrieval_graph.get_avoided_exercises",
            new=mock_get_avoided,
        ),
        patch(
            "app.kg.retrieval_graph.get_exercise_vector_store",
            return_value=MagicMock(similarity_search=MagicMock(return_value=[])),
        ),
        patch(
            "app.kg.retrieval_graph.assemble_context_from_parts",
            new=AsyncMock(return_value=context_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        await graph.ainvoke({"member_id": "m1", "query": "leg workout"})

    # Each traversal function must have been called exactly once (by its own node, not by assemble)
    mock_get_member_profile.assert_called_once()
    mock_get_safe_exercises.assert_called_once()
    mock_get_preferred.assert_called_once()
    mock_get_performed.assert_called_once()
    mock_get_avoided.assert_called_once()


@pytest.mark.asyncio
async def test_assemble_node_output_equivalence_and_provenance_stitch() -> None:
    """assemble node must produce equivalent ContextSlice and stitch contraindicated_provenance.

    Verifies that:
    - The ContextSlice returned in state["context"] matches what assemble_context_from_parts returns.
    - contraindicated_provenance from state (set by run_injury_traversal) is stitched
      onto the returned context by the assemble node.
    """
    mock_driver = MagicMock()
    profile = _make_member_profile()
    exercises = _make_exercises()
    provenance = [{"snomed_code": "123", "exercise_id": "ex-1"}]

    # Build an expected context_slice without provenance — assemble node stitches it in
    expected_slice = _make_context_slice()
    expected_slice["contraindicated_provenance"] = []  # will be overwritten by node

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
            "app.kg.retrieval_graph.get_contraindicated_provenance",
            new=AsyncMock(return_value=provenance),
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
            "app.kg.retrieval_graph.get_avoided_exercises",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.kg.retrieval_graph.get_exercise_vector_store",
            return_value=MagicMock(similarity_search=MagicMock(return_value=[])),
        ),
        patch(
            "app.kg.retrieval_graph.assemble_context_from_parts",
            new=AsyncMock(return_value=expected_slice),
        ),
    ):
        from app.kg.retrieval_graph import build_retrieval_graph

        graph = build_retrieval_graph(mock_driver)
        result = await graph.ainvoke({"member_id": "m1", "query": "leg workout"})

    context = result["context"]
    assert context is not None
    # Core ContextSlice fields match the fixture
    assert context["member_profile"]["id"] == "m1"
    assert context["safe_exercises"] == [{"id": "ex-1", "name": "Squat"}]
    assert context["token_counts"]["total"] == 30
    # SNOMED provenance was stitched from state["contraindicated_provenance"]
    assert context["contraindicated_provenance"] == provenance
