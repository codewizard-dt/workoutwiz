"""Integration tests for the /kg/* router endpoints.

Uses FastAPI's TestClient with dependency overrides to mock:
- auth (current_active_user)
- retrieval/generation graph invocations
- explain_skipped_exercise
- write_feedback
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ---------------------------------------------------------------------------
# Shared mock user
# ---------------------------------------------------------------------------

_MOCK_USER = MagicMock()
_MOCK_USER.id = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(autouse=True)
def override_auth():
    from app.auth import current_active_user
    from app.kg.driver import get_neo4j_driver

    mock_driver = AsyncMock()

    app.dependency_overrides[current_active_user] = lambda: _MOCK_USER
    app.dependency_overrides[get_neo4j_driver] = lambda: mock_driver
    yield mock_driver
    app.dependency_overrides.clear()


client = TestClient(app)

# ---------------------------------------------------------------------------
# /kg/recommend
# ---------------------------------------------------------------------------


def test_kg_recommend_returns_200(override_auth):
    """Mock retrieval + generation graphs; assert 200 and response shape."""
    mock_context = {
        "safe_exercises": [],
        "preferred_exercises": [],
        "vector_results": [],
        "injuries": [],
        "member_node": None,
        "token_counts": {},
    }
    mock_recommendation = MagicMock()
    mock_recommendation.exercises = []
    mock_recommendation.overall_reasoning = "Test reasoning"
    mock_recommendation.skipped_exercise_ids = []

    mock_retrieval_graph = AsyncMock()
    mock_retrieval_graph.ainvoke = AsyncMock(return_value={"context": mock_context})

    mock_generation_graph = AsyncMock()
    mock_generation_graph.ainvoke = AsyncMock(
        return_value={
            "recommendation": mock_recommendation,
            "fallback_triggered": False,
        }
    )

    with (
        patch("app.routers.kg.build_retrieval_graph", return_value=mock_retrieval_graph),
        patch("app.routers.kg.build_generation_graph", return_value=mock_generation_graph),
    ):
        resp = client.post(
            "/kg/recommend",
            json={"member_id": "member-123", "query": "upper body strength"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "member_id" in data
    assert "exercises" in data
    assert "overall_reasoning" in data
    assert "skipped_exercise_ids" in data
    assert "fallback_used" in data
    assert data["member_id"] == "member-123"
    # Driver is shared — must NOT be closed per-request
    override_auth.close.assert_not_awaited()


# ---------------------------------------------------------------------------
# /kg/explain
# ---------------------------------------------------------------------------


def test_kg_explain_returns_explanation(override_auth):
    """Mock explain_skipped_exercise; assert 200 and explanation string."""
    with (
        patch(
            "app.routers.kg.explain_skipped_exercise",
            new_callable=AsyncMock,
            return_value=(
                "'Barbell Squat' was skipped because it is contraindicated for: knee injury.",
                {
                    "event": "kg_explainability",
                    "latency_ms": 3,
                    "query_count": 1,
                    "result_count": 1,
                    "path_depth": 2,
                    "reason_type": "contraindication",
                    "user_id": "member-123",
                    "confidence": 0.625,
                },
                0.625,
            ),
        ),
    ):
        resp = client.post(
            "/kg/explain",
            json={"member_id": "member-123", "exercise_id": "exercise-abc"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["exercise_id"] == "exercise-abc"
    assert "Barbell Squat" in data["explanation"]
    assert "confidence" in data
    assert isinstance(data["confidence"], float)
    # Driver is shared — must NOT be closed per-request
    override_auth.close.assert_not_awaited()


# ---------------------------------------------------------------------------
# /kg/feedback
# ---------------------------------------------------------------------------


def test_kg_feedback_writes_and_returns_id(override_auth):
    """Mock write_feedback; assert 200 and feedback_id in response."""
    expected_feedback_id = str(uuid.uuid4())

    with (
        patch(
            "app.routers.kg.write_feedback",
            new_callable=AsyncMock,
            return_value=expected_feedback_id,
        ),
    ):
        resp = client.post(
            "/kg/feedback",
            json={
                "member_id": "member-123",
                "exercise_id": "exercise-abc",
                "rating": 5,
                "text": "Great exercise!",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["feedback_id"] == expected_feedback_id
    assert "message" in data
    # Driver is shared — must NOT be closed per-request
    override_auth.close.assert_not_awaited()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_kg_recommend_returns_500_on_error(override_auth):
    """If the pipeline raises, expect a 500 response."""
    mock_retrieval_graph = AsyncMock()
    mock_retrieval_graph.ainvoke = AsyncMock(side_effect=RuntimeError("neo4j down"))

    with (
        patch("app.routers.kg.build_retrieval_graph", return_value=mock_retrieval_graph),
    ):
        resp = client.post(
            "/kg/recommend",
            json={"member_id": "member-123", "query": "legs"},
        )

    assert resp.status_code == 500
    # Driver is shared — must NOT be closed per-request
    override_auth.close.assert_not_awaited()


# ---------------------------------------------------------------------------
# /kg/audit
# ---------------------------------------------------------------------------


def test_kg_audit_returns_404_for_missing_session():
    """Assert 404 when session has no entries."""
    resp = client.get("/kg/audit/nonexistent-session-xyz")
    assert resp.status_code == 404
    data = resp.json()
    assert "not found" in data["detail"].lower()


def test_kg_audit_requires_auth():
    """Assert 401 when JWT is missing."""
    # Clear auth override to test missing auth
    from app.auth import current_active_user
    app.dependency_overrides.clear()

    resp = client.get("/kg/audit/any-session")
    assert resp.status_code == 401

    # Restore auth override
    app.dependency_overrides[current_active_user] = lambda: _MOCK_USER


# ---------------------------------------------------------------------------
# Singleton behaviour
# ---------------------------------------------------------------------------


def test_create_neo4j_driver_returns_singleton():
    """Repeated create_neo4j_driver() calls must return the same driver instance."""
    import app.kg.driver as drv_module

    # Reset singleton so we get a fresh instance in this test
    original = drv_module._driver
    drv_module._driver = None

    try:
        with patch("app.kg.driver.neo4j.AsyncGraphDatabase.driver") as mock_factory:
            mock_instance = MagicMock()
            mock_factory.return_value = mock_instance

            first = drv_module.create_neo4j_driver()
            second = drv_module.create_neo4j_driver()

        assert first is second, "create_neo4j_driver() must return the same instance on repeated calls"
        mock_factory.assert_called_once()  # constructor called exactly once
    finally:
        # Restore whatever was there before (may be None in CI)
        drv_module._driver = original



# ---------------------------------------------------------------------------
# /kg/contraindications
# ---------------------------------------------------------------------------


def test_kg_contraindications_aggregates_provenance(override_auth):
    """Provenance rows are aggregated per exercise into reason + confidence."""
    provenance = [
        {"exercise_id": "ex1", "injury_name": "knee injury", "matched_joint": "knee"},
        {"exercise_id": "ex1", "injury_name": "knee injury", "matched_joint": "patella"},
        {"exercise_id": "ex2", "injury_name": "shoulder injury", "matched_joint": "shoulder"},
    ]
    with (
        patch(
            "app.routers.kg._resolve_member_id",
            new_callable=AsyncMock,
            return_value="member-123",
        ),
        patch(
            "app.routers.kg.get_contraindicated_provenance",
            new_callable=AsyncMock,
            return_value=provenance,
        ),
    ):
        resp = client.get("/kg/contraindications")

    assert resp.status_code == 200
    data = resp.json()
    assert data["member_id"] == "member-123"
    items = {i["exercise_id"]: i for i in data["items"]}
    assert set(items) == {"ex1", "ex2"}
    assert items["ex1"]["injuries"] == ["knee injury"]
    assert "knee, patella" in items["ex1"]["reason"]
    assert "knee injury" in items["ex1"]["reason"]
    # 1 injury → depth 0.5 + coverage 0.125 = 0.625
    assert items["ex1"]["confidence"] == pytest.approx(0.625)


def test_kg_contraindications_empty_when_no_member(override_auth):
    """No graph member resolved → empty result, not an error."""
    with patch(
        "app.routers.kg._resolve_member_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = client.get("/kg/contraindications")

    assert resp.status_code == 200
    data = resp.json()
    assert data == {"member_id": "", "items": []}


# ---------------------------------------------------------------------------
# /kg/feedback/summary
# ---------------------------------------------------------------------------


def test_kg_feedback_summary_aggregates(override_auth):
    """Aggregated feedback rows map to avg_rating/count/last_rated_at."""
    from datetime import datetime

    from app.database import get_async_session

    exercise_id = uuid.uuid4()
    rated_at = datetime(2026, 6, 1, 12, 0, 0)
    mock_result = MagicMock()
    mock_result.all.return_value = [(exercise_id, 4.5, 2, rated_at)]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_async_session] = lambda: mock_session
    try:
        resp = client.get("/kg/feedback/summary")
    finally:
        app.dependency_overrides.pop(get_async_session, None)

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["exercise_id"] == str(exercise_id)
    assert items[0]["avg_rating"] == 4.5
    assert items[0]["count"] == 2
    assert items[0]["last_rated_at"] == rated_at.isoformat()




