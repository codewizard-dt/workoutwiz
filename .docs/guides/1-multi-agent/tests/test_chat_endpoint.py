import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from workout_wiz.main import app, _sessions

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_returns_session_id():
    with patch("workout_wiz.main.hub") as mock_hub:
        mock_hub.invoke.return_value = {
            "messages": [AIMessage(content="Hello!")],
            "route_decision": None,
            "user_id": "anonymous",
            "session_id": "sess-1",
            "audit_log": [],
        }
        resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["reply"] == "Hello!"


def test_chat_reuses_session():
    mock_state = {
        "messages": [AIMessage(content="Hi there!")],
        "route_decision": None,
        "user_id": "anonymous",
        "session_id": "test-session",
        "audit_log": [],
    }
    with patch("workout_wiz.main.hub") as mock_hub:
        mock_hub.invoke.return_value = mock_state
        r1 = client.post("/chat", json={"message": "hi", "session_id": "test-session"})
        r2 = client.post("/chat", json={"message": "hello again", "session_id": "test-session"})
    assert r1.json()["session_id"] == "test-session"
    assert r2.json()["session_id"] == "test-session"
    # hub.invoke called twice
    assert mock_hub.invoke.call_count == 2


def test_chat_user_id_header():
    with patch("workout_wiz.main.hub") as mock_hub:
        mock_hub.invoke.return_value = {
            "messages": [AIMessage(content="ok")],
            "route_decision": None,
            "user_id": "user-123",
            "session_id": "s",
            "audit_log": [],
        }
        resp = client.post(
            "/chat",
            json={"message": "test"},
            headers={"X-User-ID": "user-123"},
        )
    assert resp.status_code == 200
    call_args = mock_hub.invoke.call_args[0][0]
    assert call_args["user_id"] == "user-123"


def test_clear_session():
    _sessions["to-clear"] = {}
    resp = client.delete("/session/to-clear")
    assert resp.status_code == 200
    assert "to-clear" not in _sessions


def test_ui_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Workout Wiz" in resp.text
