"""Unit tests for app.knowledge_graph.ingest_feedback.

All tests mock the Neo4j driver and PostgreSQL session — no real database
connections are made.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.knowledge_graph.ingest_feedback import (
    _upsert_feedback_batch,
    ingest_all_feedback,
)
from app.models.feedback import ExerciseFeedback, FeedbackContextType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(
    context_type: FeedbackContextType,
    workout_id: uuid.UUID | None = None,
    workout_set_id: uuid.UUID | None = None,
) -> ExerciseFeedback:
    """Build a minimal ExerciseFeedback ORM-like object without hitting the DB."""
    row = MagicMock(spec=ExerciseFeedback)
    row.id = uuid.uuid4()
    row.user_id = uuid.uuid4()
    row.exercise_id = uuid.uuid4()
    row.workout_id = workout_id
    row.workout_set_id = workout_set_id
    row.rating = 4
    row.feedback_text = "Great exercise!"
    row.context_type = context_type
    row.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return row


def _build_neo4j_session_mock() -> AsyncMock:
    """Return an AsyncMock that records calls to execute_write."""
    session = AsyncMock()
    # execute_write receives a callable; capture the calls by executing the
    # coroutine immediately with a recording transaction mock.
    recorded_queries: list[str] = []

    async def _execute_write(fn, *args, **kwargs):
        tx = AsyncMock()
        run_calls: list[tuple[str, dict]] = []

        async def _tx_run(cypher: str, **params):
            run_calls.append((cypher, params))

        tx.run = _tx_run
        await fn(tx)
        recorded_queries.extend(q for q, _ in run_calls)

    session.execute_write.side_effect = _execute_write
    # Expose recorded queries for assertions
    session._recorded_queries = recorded_queries
    return session


# ---------------------------------------------------------------------------
# Test 1: exercise context writes both ABOUT and RATED edges
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exercise_context_writes_rated_edge():
    """EXERCISE context → both ABOUT→Exercise and RATED edge are written."""
    row = _make_row(FeedbackContextType.EXERCISE)
    session = _build_neo4j_session_mock()

    await _upsert_feedback_batch(session, [row])

    queries = session._recorded_queries
    about_found = any("[:ABOUT]->(e)" in q for q in queries)
    rated_found = any(":RATED]->(e)" in q for q in queries)

    assert about_found, f"Expected ABOUT→Exercise edge. Queries: {queries}"
    assert rated_found, f"Expected RATED edge. Queries: {queries}"


# ---------------------------------------------------------------------------
# Test 2: workout context writes ABOUT→WorkoutSession, no RATED edge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workout_context_writes_about_session():
    """WORKOUT context → ABOUT→WorkoutSession edge written; no RATED edge."""
    row = _make_row(FeedbackContextType.WORKOUT, workout_id=uuid.uuid4())
    session = _build_neo4j_session_mock()

    await _upsert_feedback_batch(session, [row])

    queries = session._recorded_queries
    about_ws_found = any("[:ABOUT]->(ws)" in q for q in queries)
    rated_found = any("[:RATED]->" in q for q in queries)

    assert about_ws_found, f"Expected ABOUT→WorkoutSession edge. Queries: {queries}"
    assert not rated_found, f"Expected NO RATED edge for WORKOUT context. Queries: {queries}"


# ---------------------------------------------------------------------------
# Test 3: set context merges Set node
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_context_merges_set_node():
    """SET context → MERGE (s:Set {id: ...}) appears in executed Cypher."""
    set_id = uuid.uuid4()
    row = _make_row(FeedbackContextType.SET, workout_set_id=set_id)
    session = _build_neo4j_session_mock()

    await _upsert_feedback_batch(session, [row])

    queries = session._recorded_queries
    set_merge_found = any("MERGE (s:Set" in q for q in queries)

    assert set_merge_found, f"Expected MERGE (s:Set ...) Cypher. Queries: {queries}"


# ---------------------------------------------------------------------------
# Test 4: idempotent merge (ON MATCH SET pattern present, no CREATE)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_merge_on_match():
    """Running _upsert_feedback_batch twice does not raise and uses MERGE/ON MATCH SET."""
    row = _make_row(FeedbackContextType.EXERCISE)
    session = _build_neo4j_session_mock()

    # First run
    await _upsert_feedback_batch(session, [row])
    # Second run — must not raise
    await _upsert_feedback_batch(session, [row])

    queries = session._recorded_queries
    merge_found = any("MERGE (f:FeedbackEvent" in q for q in queries)
    on_match_found = any("ON MATCH SET" in q for q in queries)

    assert merge_found, f"Expected MERGE pattern. Queries: {queries}"
    assert on_match_found, f"Expected ON MATCH SET pattern. Queries: {queries}"
    # Should never contain a bare CREATE (all idempotent MERGE)
    bare_create = [q for q in queries if q.strip().startswith("CREATE")]
    assert not bare_create, f"Found bare CREATE (non-idempotent). Queries: {bare_create}"
