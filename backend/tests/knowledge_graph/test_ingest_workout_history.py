"""Unit tests for app.knowledge_graph.ingest_workout_history."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.knowledge_graph.ingest_workout_history import (
    _merge_session,
    ingest_workout_history,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_SESSION: dict = {
    "id": str(uuid.uuid4()),
    "member_id": str(uuid.uuid4()),
    "started_at": datetime.now(tz=timezone.utc).isoformat(),
    "ended_at": datetime.now(tz=timezone.utc).isoformat(),
    "exercises": [
        {
            "exercise_id": str(uuid.uuid4()),
            "sets": 3,
            "reps": [10, 10, 10],
            "weight_kg": 60.0,
            "duration_s": None,
        }
    ],
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ingest_empty_raises_value_error() -> None:
    """ingest_workout_history must refuse an empty sessions list."""
    mock_driver = MagicMock()
    with pytest.raises(ValueError):
        ingest_workout_history(mock_driver, [])


def test_merge_session_cypher_calls() -> None:
    """_merge_session must call tx.run at least 3 times for a single session
    with one exercise: once for the node, once for PERFORMED, once for INCLUDED.
    """
    mock_tx = MagicMock()
    _merge_session(mock_tx, SAMPLE_SESSION)
    assert mock_tx.run.call_count >= 3


def test_ingest_returns_count() -> None:
    """ingest_workout_history must return the number of sessions processed."""
    mock_driver = MagicMock()
    # Make driver.session() work as a context manager that returns a mock session
    mock_neo_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_neo_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    result = ingest_workout_history(mock_driver, [SAMPLE_SESSION])
    assert result == 1


def test_idempotent_cypher_uses_merge() -> None:
    """Every Cypher statement issued by _merge_session must contain MERGE."""
    mock_tx = MagicMock()
    _merge_session(mock_tx, SAMPLE_SESSION)

    for c in mock_tx.run.call_args_list:
        # First positional arg is the Cypher string
        cypher: str = c.args[0]
        assert "MERGE" in cypher, f"Cypher statement missing MERGE: {cypher!r}"
