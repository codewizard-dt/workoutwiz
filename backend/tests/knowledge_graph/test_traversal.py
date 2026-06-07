"""
Unit tests for backend/app/knowledge_graph/traversal.py.

All tests mock the Neo4j AsyncDriver — no live connection required.
The session is used as an async context manager:
    async with driver.session(database=...) as session:
        result = await session.run(...)
        records = await result.data()   # or result.single()
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.knowledge_graph.traversal import (
    get_contraindicated_exercise_ids,
    get_exercises_by_equipment,
    get_exercises_targeting_muscle,
    get_member_profile,
    get_performed_exercises,
    get_preferred_exercises,
    get_safe_exercises,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_driver(run_return: object = None, single_return: object = None) -> AsyncMock:
    """
    Build a minimal AsyncDriver mock.

    The driver is used as:
        async with driver.session(database=...) as session:
            result = await session.run(...)
            records = await result.data()   # OR
            record  = await result.single()

    ``run_return`` is what ``await result.data()`` returns.
    ``single_return`` is what ``await result.single()`` returns.
    """
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=run_return or [])
    mock_result.single = AsyncMock(return_value=single_return)

    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)

    # driver.session() returns an async context manager
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_session_cm)

    return mock_driver  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# get_contraindicated_exercise_ids
# ---------------------------------------------------------------------------


async def test_get_contraindicated_ids_returns_set() -> None:
    """Returns a set of exercise IDs from query results."""
    driver = _make_driver(
        run_return=[{"exercise_id": "ex-1"}, {"exercise_id": "ex-2"}]
    )

    result = await get_contraindicated_exercise_ids("member-1", driver)

    assert result == {"ex-1", "ex-2"}
    assert isinstance(result, set)


async def test_get_contraindicated_ids_empty_when_no_injuries() -> None:
    """Returns an empty set when the member has no active injuries."""
    driver = _make_driver(run_return=[])

    result = await get_contraindicated_exercise_ids("member-1", driver)

    assert result == set()


async def test_get_contraindicated_ids_deduplicates() -> None:
    """DISTINCT in Cypher is relied upon; result set never has duplicates."""
    driver = _make_driver(
        run_return=[{"exercise_id": "ex-1"}, {"exercise_id": "ex-1"}]
    )

    result = await get_contraindicated_exercise_ids("member-1", driver)

    assert result == {"ex-1"}
    assert len(result) == 1


# ---------------------------------------------------------------------------
# get_safe_exercises
# ---------------------------------------------------------------------------


async def test_get_safe_exercises_returns_list_of_dicts() -> None:
    """Returns a list of exercise dicts with expected keys."""
    sample_exercises = [
        {
            "id": "ex-10",
            "name": "Push-up",
            "muscle_groups": ["chest", "triceps"],
            "movement_patterns": ["push"],
            "equipment_required": [],
            "priority_tier": 1,
            "is_reps": True,
            "is_duration": False,
            "supports_weight": False,
        },
        {
            "id": "ex-11",
            "name": "Squat",
            "muscle_groups": ["quads", "glutes"],
            "movement_patterns": ["squat"],
            "equipment_required": [],
            "priority_tier": 1,
            "is_reps": True,
            "is_duration": False,
            "supports_weight": True,
        },
    ]
    driver = _make_driver(run_return=sample_exercises)

    result = await get_safe_exercises("member-1", driver)

    assert len(result) == 2
    for item in result:
        assert "id" in item
        assert "name" in item
        assert "muscle_groups" in item


async def test_get_safe_exercises_empty_when_all_contraindicated() -> None:
    """Returns an empty list when all exercises are contraindicated."""
    driver = _make_driver(run_return=[])

    result = await get_safe_exercises("member-1", driver)

    assert result == []


# ---------------------------------------------------------------------------
# get_member_profile
# ---------------------------------------------------------------------------


async def test_get_member_profile_returns_dict() -> None:
    """Returns a dict with member profile fields when member is found."""
    record_data = {
        "id": "member-1",
        "name": "Alice",
        "goals": ["strength"],
        "equipment": ["barbell"],
        "availability": 4,
        "fitness_level": "intermediate",
        "injury_names": ["knee tendinopathy"],
    }
    # neo4j Record supports dict() — simulate with a dict directly
    mock_record = MagicMock()
    mock_record.__iter__ = MagicMock(return_value=iter(record_data))
    mock_record.keys = MagicMock(return_value=list(record_data.keys()))
    # dict(record) calls record.keys() then record[key] for each key
    mock_record.__getitem__ = MagicMock(side_effect=record_data.__getitem__)

    driver = _make_driver(single_return=mock_record)

    result = await get_member_profile("member-1", driver)

    assert result is not None
    assert result["id"] == "member-1"


async def test_get_member_profile_returns_none_when_not_found() -> None:
    """Returns None (not an exception) when the member node does not exist."""
    driver = _make_driver(single_return=None)

    result = await get_member_profile("nonexistent-member", driver)

    assert result is None


async def test_get_member_profile_passes_member_id_as_parameter() -> None:
    """Verifies the query is called with the correct parameterized member_id."""
    driver = _make_driver(single_return=None)

    await get_member_profile("member-abc", driver)

    # Extract the session mock from the driver to verify run was called
    session_cm = driver.session.return_value
    session = session_cm.__aenter__.return_value
    call_kwargs = session.run.call_args
    # The member_id parameter must be passed as a keyword arg
    assert call_kwargs is not None
    assert "member-abc" in str(call_kwargs)


# ---------------------------------------------------------------------------
# get_preferred_exercises
# ---------------------------------------------------------------------------


async def test_get_preferred_exercises_returns_list() -> None:
    """Happy path: returns a list when rated exercises exist."""
    records = [
        {"id": "ex-1", "name": "Squat", "muscle_groups": ["quads"], "avg_rating": 4.5, "feedback_count": 2},
        {"id": "ex-2", "name": "Deadlift", "muscle_groups": ["hamstrings"], "avg_rating": 5.0, "feedback_count": 1},
    ]
    driver = _make_driver(run_return=records)

    result = await get_preferred_exercises("member-1", driver)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["avg_rating"] == 4.5
    assert result[1]["avg_rating"] == 5.0


async def test_get_preferred_exercises_empty_when_no_feedback() -> None:
    """Returns an empty list when the member has no qualifying ratings."""
    driver = _make_driver(run_return=[])

    result = await get_preferred_exercises("member-1", driver)

    assert result == []


async def test_get_preferred_exercises_uses_min_rating_param() -> None:
    """Verifies min_rating is forwarded as a query parameter."""
    driver = _make_driver(run_return=[])

    await get_preferred_exercises("member-1", driver, min_rating=5)

    session_cm = driver.session.return_value
    session = session_cm.__aenter__.return_value
    call_kwargs = session.run.call_args
    assert call_kwargs is not None
    assert "5" in str(call_kwargs) or call_kwargs.kwargs.get("min_rating") == 5 or 5 in call_kwargs.args


# ---------------------------------------------------------------------------
# get_performed_exercises
# ---------------------------------------------------------------------------


async def test_get_performed_exercises_returns_list() -> None:
    """Happy path: returns a list of recently performed exercises."""
    records = [
        {"id": "ex-1", "name": "Bench Press", "last_performed_at": "2026-05-01T10:00:00"},
        {"id": "ex-2", "name": "Squat", "last_performed_at": "2026-04-28T09:00:00"},
        {"id": "ex-3", "name": "Row", "last_performed_at": "2026-04-25T08:30:00"},
    ]
    driver = _make_driver(run_return=records)

    result = await get_performed_exercises("member-1", driver)

    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["last_performed_at"] == "2026-05-01T10:00:00"


async def test_get_performed_exercises_empty_when_no_history() -> None:
    """Returns an empty list when the member has no workout history."""
    driver = _make_driver(run_return=[])

    result = await get_performed_exercises("member-1", driver)

    assert result == []


async def test_get_performed_exercises_uses_limit_param() -> None:
    """Verifies the limit parameter is forwarded to the query."""
    driver = _make_driver(run_return=[])

    await get_performed_exercises("member-1", driver, limit=5)

    session_cm = driver.session.return_value
    session = session_cm.__aenter__.return_value
    call_kwargs = session.run.call_args
    assert call_kwargs is not None
    assert "5" in str(call_kwargs) or call_kwargs.kwargs.get("limit") == 5 or 5 in call_kwargs.args


# ---------------------------------------------------------------------------
# get_exercises_targeting_muscle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_exercises_targeting_muscle_returns_list() -> None:
    """Returns canned list for a known muscle name."""
    canned = [
        {"id": "ex-1", "name": "Squat", "priority_tier": 1},
        {"id": "ex-2", "name": "Leg Press", "priority_tier": 2},
    ]
    driver = _make_driver(run_return=canned)

    result = await get_exercises_targeting_muscle("quadriceps", driver)

    assert result == canned


@pytest.mark.asyncio
async def test_get_exercises_targeting_muscle_passes_param() -> None:
    """The muscle_name argument is forwarded as a query parameter."""
    driver = _make_driver(run_return=[{"id": "ex-1", "name": "Squat", "priority_tier": 1}])

    await get_exercises_targeting_muscle("glutes", driver)

    session_cm = driver.session.return_value
    session = session_cm.__aenter__.return_value
    call_args = session.run.call_args
    assert call_args is not None
    # muscle_name should appear in kwargs or args
    assert (
        call_args.kwargs.get("muscle_name") == "glutes"
        or "glutes" in str(call_args)
    )


@pytest.mark.asyncio
async def test_get_exercises_targeting_muscle_empty_when_no_match() -> None:
    """Returns [] when driver returns no records."""
    driver = _make_driver(run_return=[])

    result = await get_exercises_targeting_muscle("quadriceps", driver)

    assert result == []


# ---------------------------------------------------------------------------
# get_exercises_by_equipment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_exercises_by_equipment_returns_list() -> None:
    """Returns canned list for a known equipment name."""
    canned = [
        {"id": "ex-3", "name": "Barbell Bench Press", "priority_tier": 1},
    ]
    driver = _make_driver(run_return=canned)

    result = await get_exercises_by_equipment("Barbell", driver)

    assert result == canned


@pytest.mark.asyncio
async def test_get_exercises_by_equipment_passes_param() -> None:
    """The equipment_name argument is forwarded as a query parameter."""
    driver = _make_driver(run_return=[{"id": "ex-3", "name": "Barbell Bench Press", "priority_tier": 1}])

    await get_exercises_by_equipment("Dumbbell", driver)

    session_cm = driver.session.return_value
    session = session_cm.__aenter__.return_value
    call_args = session.run.call_args
    assert call_args is not None
    assert (
        call_args.kwargs.get("equipment_name") == "Dumbbell"
        or "Dumbbell" in str(call_args)
    )


@pytest.mark.asyncio
async def test_get_exercises_by_equipment_empty_when_no_match() -> None:
    """Returns [] when driver returns no records."""
    driver = _make_driver(run_return=[])

    result = await get_exercises_by_equipment("Barbell", driver)

    assert result == []
