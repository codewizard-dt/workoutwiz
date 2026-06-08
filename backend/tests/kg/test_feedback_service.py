"""Unit tests for backend/app/kg/feedback_service.py."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.kg.feedback_service import write_feedback
from app.models.feedback import ExerciseFeedback
from app.schemas.kg import FeedbackPayload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_payload(**overrides) -> FeedbackPayload:
    defaults = {
        "member_id": str(uuid.uuid4()),
        "exercise_id": str(uuid.uuid4()),
        "rating": 4,
    }
    defaults.update(overrides)
    return FeedbackPayload(**defaults)


def _build_pg_session_mock() -> AsyncMock:
    """Return a minimal mock SQLAlchemy AsyncSession for write_feedback tests.

    ``add`` is synchronous in SQLAlchemy, so it must be a plain MagicMock.
    ``commit`` and ``rollback`` are coroutines, so they use AsyncMock.
    """
    from unittest.mock import MagicMock

    session = AsyncMock()
    session.add = MagicMock()  # synchronous — must NOT be AsyncMock
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _build_driver_mock() -> AsyncMock:
    """Return a mock neo4j driver whose session records Cypher calls.

    ``driver.session()`` is called as a *synchronous* method that returns an
    async context manager (matching the real neo4j ``AsyncDriver`` API).  We
    therefore use a plain ``MagicMock`` for ``driver.session`` so it returns
    the context-manager mock directly rather than a coroutine.
    """
    from unittest.mock import MagicMock

    driver = MagicMock()
    recorded_queries: list[str] = []

    async def _execute_write(fn, *args, **kwargs):
        tx = AsyncMock()

        async def _tx_run(cypher: str, **params):
            recorded_queries.append(cypher)

        tx.run = _tx_run
        await fn(tx)

    session_mock = AsyncMock()
    session_mock.execute_write.side_effect = _execute_write
    session_mock._recorded_queries = recorded_queries

    # driver.session() → sync call returns an async context manager
    ctx_manager = AsyncMock()
    ctx_manager.__aenter__.return_value = session_mock
    ctx_manager.__aexit__.return_value = False
    driver.session.return_value = ctx_manager

    driver._session_mock = session_mock
    return driver


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_feedback_calls_ingestion():
    """write_feedback should execute_write on the neo4j session and return a UUID."""
    driver = _build_driver_mock()
    pg_session = _build_pg_session_mock()
    payload = _make_payload(rating=3, text="Felt good")

    result = await write_feedback(payload, driver, pg_session)

    # Return value is a valid UUID string
    uuid.UUID(result)  # raises ValueError if not a valid UUID

    # execute_write was called once
    session_mock = driver._session_mock
    session_mock.execute_write.assert_called_once()


@pytest.mark.asyncio
async def test_write_feedback_writes_correct_cypher_queries():
    """write_feedback should emit MERGE FeedbackEvent, ABOUT->Exercise, and RATED queries."""
    driver = _build_driver_mock()
    pg_session = _build_pg_session_mock()
    payload = _make_payload()

    await write_feedback(payload, driver, pg_session)

    queries = driver._session_mock._recorded_queries
    assert any("FeedbackEvent" in q for q in queries), (
        f"Expected FeedbackEvent MERGE. Queries: {queries}"
    )
    assert any("[:ABOUT]->(e)" in q for q in queries), (
        f"Expected ABOUT->Exercise edge. Queries: {queries}"
    )
    assert any(":RATED]->(e)" in q for q in queries), (
        f"Expected RATED edge. Queries: {queries}"
    )


@pytest.mark.asyncio
async def test_write_feedback_returns_unique_ids():
    """Two calls should return distinct UUIDs."""
    driver = _build_driver_mock()
    pg_session = _build_pg_session_mock()
    payload = _make_payload()

    id1 = await write_feedback(payload, driver, pg_session)

    # Reset session side_effect for second call
    driver2 = _build_driver_mock()
    pg_session2 = _build_pg_session_mock()
    id2 = await write_feedback(payload, driver2, pg_session2)

    assert id1 != id2


# ---------------------------------------------------------------------------
# Persistence tests — PostgreSQL primary, Neo4j best-effort
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_feedback_persists_pg_row():
    """The rating must be written to PostgreSQL (the UI restore source of truth)."""
    driver = _build_driver_mock()
    pg_session = _build_pg_session_mock()
    member_id = str(uuid.uuid4())
    exercise_id = str(uuid.uuid4())
    workout_id = str(uuid.uuid4())
    workout_set_id = str(uuid.uuid4())
    payload = _make_payload(
        member_id=member_id,
        exercise_id=exercise_id,
        workout_id=workout_id,
        workout_set_id=workout_set_id,
        rating=5,
    )

    await write_feedback(payload, driver, pg_session)

    pg_session.add.assert_called_once()
    row = pg_session.add.call_args.args[0]
    assert isinstance(row, ExerciseFeedback)
    assert str(row.user_id) == member_id
    assert str(row.exercise_id) == exercise_id
    assert str(row.workout_id) == workout_id
    assert str(row.workout_set_id) == workout_set_id
    assert row.rating == 5
    pg_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_write_feedback_neo4j_failure_is_best_effort():
    """A Neo4j outage must not lose the rating or raise — PG commit still happens."""
    driver = _build_driver_mock()
    driver._session_mock.execute_write.side_effect = RuntimeError("neo4j unavailable")
    pg_session = _build_pg_session_mock()
    payload = _make_payload(rating=2)

    result = await write_feedback(payload, driver, pg_session)

    uuid.UUID(result)  # still returns a valid id (no exception escaped)
    pg_session.add.assert_called_once()
    pg_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_write_feedback_pg_integrity_error_propagates():
    """A genuine PG constraint failure must surface, not be reported as success."""
    driver = _build_driver_mock()
    pg_session = _build_pg_session_mock()
    pg_session.commit.side_effect = IntegrityError("INSERT", {}, Exception("fk violation"))
    payload = _make_payload()

    with pytest.raises(IntegrityError):
        await write_feedback(payload, driver, pg_session)

    pg_session.rollback.assert_awaited_once()
    # PG is primary: a failed commit short-circuits before the Neo4j enrichment.
    driver._session_mock.execute_write.assert_not_called()


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


def test_feedback_payload_validates_rating_range():
    """rating must be between 1 and 5 inclusive."""
    base = {"member_id": "m1", "exercise_id": "e1"}

    # rating=0 should fail
    with pytest.raises(ValidationError):
        FeedbackPayload(**base, rating=0)

    # rating=6 should fail
    with pytest.raises(ValidationError):
        FeedbackPayload(**base, rating=6)

    # rating=1 and rating=5 are valid
    p1 = FeedbackPayload(**base, rating=1)
    p5 = FeedbackPayload(**base, rating=5)
    assert p1.rating == 1
    assert p5.rating == 5


def test_feedback_payload_optional_fields():
    """text, workout_id, and workout_set_id are optional; context_type defaults to 'exercise'."""
    payload = FeedbackPayload(member_id="m1", exercise_id="e1", rating=3)
    assert payload.text is None
    assert payload.workout_id is None
    assert payload.workout_set_id is None
    assert payload.context_type == "exercise"
