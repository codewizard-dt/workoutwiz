import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.main import app
from app.routers.chat import _sessions

_MOCK_USER = MagicMock()
_MOCK_USER.id = uuid.UUID("00000000-0000-0000-0000-000000000001")

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture(autouse=True)
def mock_auth():
    from app.auth import current_active_user
    app.dependency_overrides[current_active_user] = lambda: _MOCK_USER
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def populate_exercise_cache():
    from app.agents import exercises as ex_module
    fake = MagicMock()
    fake.id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    fake.name = "Squat"
    fake.muscle_groups = ["quadriceps"]
    fake.equipment_required = ["barbell"]
    fake.movement_patterns = ["squat"]
    fake.is_reps = True
    fake.is_duration = False
    fake.supports_weight = True
    fake.priority_tier = 1
    ex_module._cache = [fake]
    yield
    ex_module._cache = []


def test_health():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_demo_ui_served():
    """The / route always returns HTML — 200 when demo/index.html exists, 404 otherwise."""
    resp = client.get("/")
    assert "text/html" in resp.headers["content-type"]
    assert resp.status_code in (200, 404)


def test_chat_golden_path():
    with patch("app.routers.chat.hub") as mock_hub:
        mock_hub.invoke.return_value = {
            "messages": [AIMessage(content="Great question about squats!")],
            "route_decision": None,
            "user_id": str(_MOCK_USER.id),
            "session_id": "e2e-session",
            "audit_log": [{"event": "router", "route": "COACH", "confidence": 0.9,
                           "tokens_in": 50, "tokens_out": 20, "latency_ms": 100,
                           "provider": "anthropic", "model": "claude-haiku-4-5-20251001",
                           "user_id": str(_MOCK_USER.id)}],
        }
        resp = client.post("/chat/", json={"message": "How do I squat?", "session_id": "e2e-session"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "e2e-session"
    assert "squat" in data["reply"].lower()
    assert data["route"] == "COACH"


def test_audit_golden_path():
    session_id = "e2e-audit"
    _sessions[session_id] = {
        "messages": [],
        "audit_log": [{"event": "router", "route": "COACH", "confidence": 0.9}],
    }
    resp = client.get(f"/chat/audit/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["total_entries"] == 1


def test_clear_session_golden_path():
    _sessions["to-clear"] = {}
    resp = client.delete("/chat/session/to-clear")
    assert resp.status_code == 204
    assert "to-clear" not in _sessions
