"""Tests for backend/app/kg/explainability.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _build_driver_mock(record_value):
    """Return a mock AsyncDriver whose session.run returns the given record.

    ``driver.session()`` is called as a synchronous method that returns an
    async context manager (matching the real neo4j AsyncDriver API).
    """
    driver = MagicMock()

    result_mock = AsyncMock()
    result_mock.single = AsyncMock(return_value=record_value)

    session_mock = AsyncMock()
    session_mock.run = AsyncMock(return_value=result_mock)

    ctx_manager = AsyncMock()
    ctx_manager.__aenter__.return_value = session_mock
    ctx_manager.__aexit__.return_value = False
    driver.session.return_value = ctx_manager

    return driver


def _make_record(exercise_name: str, injury_names: list[str]):
    """Build a dict-like record mimicking a neo4j Record."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: (
        exercise_name if key == "exercise_name" else injury_names
    )
    # Make truthiness work: record is truthy, injury_names truthy/falsy per list
    record.__bool__ = lambda self: True
    return record


@pytest.mark.asyncio
async def test_explain_returns_injury_reason() -> None:
    """Happy path: mock returns a record with exercise_name and injury_names."""
    record = _make_record("Barbell Squat", ["Knee Tendinopathy", "Patellofemoral Syndrome"])
    driver = _build_driver_mock(record)

    from app.kg.explainability import explain_skipped_exercise

    result = await explain_skipped_exercise(
        member_id="member-1",
        exercise_id="exercise-1",
        driver=driver,
    )

    assert "Barbell Squat" in result
    assert "Knee Tendinopathy" in result
    assert "contraindicated" in result.lower()


@pytest.mark.asyncio
async def test_explain_returns_fallback_when_no_contraindication() -> None:
    """No record returned from Neo4j → return the graceful fallback string."""
    driver = _build_driver_mock(None)  # result.single() returns None

    from app.kg.explainability import explain_skipped_exercise

    result = await explain_skipped_exercise(
        member_id="member-2",
        exercise_id="exercise-2",
        driver=driver,
    )

    assert "insufficient context" in result.lower()


@pytest.mark.asyncio
async def test_explain_returns_fallback_when_no_injuries() -> None:
    """Record exists but injury_names is empty → return the graceful fallback."""
    record = _make_record("Leg Press", [])
    driver = _build_driver_mock(record)

    from app.kg.explainability import explain_skipped_exercise

    result = await explain_skipped_exercise(
        member_id="member-3",
        exercise_id="exercise-3",
        driver=driver,
    )

    assert "insufficient context" in result.lower()
