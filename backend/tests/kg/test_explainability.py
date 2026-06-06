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

    result, audit_entry, _confidence = await explain_skipped_exercise(
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

    result, audit_entry, _confidence = await explain_skipped_exercise(
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

    result, audit_entry, _confidence = await explain_skipped_exercise(
        member_id="member-3",
        exercise_id="exercise-3",
        driver=driver,
    )

    assert "insufficient context" in result.lower()


@pytest.mark.asyncio
async def test_explain_audit_entry_populated() -> None:
    """Audit entry contains required observability fields after a successful query."""
    record = _make_record("Barbell Squat", ["Knee Tendinopathy"])
    driver = _build_driver_mock(record)

    from app.kg.explainability import explain_skipped_exercise

    _result, audit_entry, _confidence = await explain_skipped_exercise(
        member_id="member-audit",
        exercise_id="exercise-audit",
        driver=driver,
    )

    assert audit_entry["event"] == "kg_explainability"
    assert isinstance(audit_entry["latency_ms"], int)
    assert audit_entry["latency_ms"] >= 0
    assert audit_entry["query_count"] == 1
    assert audit_entry["result_count"] == 1
    assert audit_entry["path_depth"] == 2
    assert audit_entry["reason_type"] == "contraindication"
    assert audit_entry["user_id"] == "member-audit"
    assert isinstance(audit_entry["confidence"], float)
    assert 0.0 < audit_entry["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_explain_audit_entry_no_contraindication() -> None:
    """Audit entry has reason_type='unknown' and result_count=0 when no record returned."""
    driver = _build_driver_mock(None)

    from app.kg.explainability import explain_skipped_exercise

    _result, audit_entry, _confidence = await explain_skipped_exercise(
        member_id="member-audit-2",
        exercise_id="exercise-audit-2",
        driver=driver,
    )

    assert audit_entry["event"] == "kg_explainability"
    assert audit_entry["query_count"] == 1
    assert audit_entry["result_count"] == 0
    assert audit_entry["reason_type"] == "unknown"


@pytest.mark.asyncio
async def test_confidence_is_zero_when_no_path() -> None:
    """confidence is 0.0 when no contraindication path exists."""
    driver = _build_driver_mock(None)

    from app.kg.explainability import explain_skipped_exercise

    _result, _audit_entry, confidence = await explain_skipped_exercise(
        member_id="member-conf-1",
        exercise_id="exercise-conf-1",
        driver=driver,
    )

    assert isinstance(confidence, float)
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_confidence_in_valid_range_single_injury() -> None:
    """confidence is a float in (0, 1] when a single contraindication is found."""
    record = _make_record("Barbell Squat", ["Knee Tendinopathy"])
    driver = _build_driver_mock(record)

    from app.kg.explainability import explain_skipped_exercise

    _result, _audit_entry, confidence = await explain_skipped_exercise(
        member_id="member-conf-2",
        exercise_id="exercise-conf-2",
        driver=driver,
    )

    assert isinstance(confidence, float)
    assert 0.0 < confidence <= 1.0


@pytest.mark.asyncio
async def test_confidence_increases_with_more_corroborating_paths() -> None:
    """More corroborating injury paths yield a higher confidence score."""
    record_one = _make_record("Deadlift", ["Lower Back Strain"])
    record_multi = _make_record("Deadlift", ["Lower Back Strain", "Herniated Disc", "Sciatica"])

    driver_one = _build_driver_mock(record_one)
    driver_multi = _build_driver_mock(record_multi)

    from app.kg.explainability import explain_skipped_exercise

    _r1, _a1, confidence_one = await explain_skipped_exercise(
        member_id="member-conf-3",
        exercise_id="exercise-conf-3",
        driver=driver_one,
    )
    _r2, _a2, confidence_multi = await explain_skipped_exercise(
        member_id="member-conf-3",
        exercise_id="exercise-conf-3",
        driver=driver_multi,
    )

    assert confidence_multi > confidence_one
