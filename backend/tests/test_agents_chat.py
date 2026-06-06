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


def _mock_hub_return(reply: str = "Hello!") -> dict:
    return {
        "messages": [AIMessage(content=reply)],
        "route_decision": None,
        "user_id": str(_MOCK_USER.id),
        "session_id": "test-session",
        "audit_log": [],
    }


def test_chat_returns_session_id():
    with patch("app.routers.chat.hub") as mock_hub:
        mock_hub.invoke.return_value = _mock_hub_return("Hi there!")
        resp = client.post("/chat/", json={"message": "hi"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["reply"] == "Hi there!"


def test_chat_reuses_session():
    with patch("app.routers.chat.hub") as mock_hub:
        mock_hub.invoke.return_value = _mock_hub_return("ok")
        r1 = client.post("/chat/", json={"message": "hello", "session_id": "my-session"})
        r2 = client.post("/chat/", json={"message": "again", "session_id": "my-session"})
    assert r1.json()["session_id"] == "my-session"
    assert r2.json()["session_id"] == "my-session"
    assert mock_hub.invoke.call_count == 2


def test_chat_user_id_comes_from_jwt():
    with patch("app.routers.chat.hub") as mock_hub:
        mock_hub.invoke.return_value = _mock_hub_return()
        client.post("/chat/", json={"message": "test"})
    call_state = mock_hub.invoke.call_args[0][0]
    assert call_state["user_id"] == str(_MOCK_USER.id)


def test_clear_session():
    _sessions["to-clear"] = {}
    resp = client.delete("/chat/session/to-clear")
    assert resp.status_code == 204
    assert "to-clear" not in _sessions
