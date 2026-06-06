import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from workout_wiz.main import app, _sessions

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


def test_audit_endpoint_returns_log():
    session_id = "audit-test-sess"
    _sessions[session_id] = {
        "messages": [],
        "audit_log": [
            {"event": "router", "model": "claude-haiku-4-5-20251001", "route": "COACH", "confidence": 0.9,
             "latency_ms": 150, "tokens_in": 100, "tokens_out": 20, "user_id": "u1", "provider": "anthropic"},
        ],
    }
    resp = client.get(f"/audit/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_entries"] == 1
    assert data["audit_log"][0]["event"] == "router"
    assert "tokens_in" in data["audit_log"][0]


def test_audit_404_unknown_session():
    resp = client.get("/audit/nonexistent-session")
    assert resp.status_code == 404


def test_chat_response_includes_audit():
    with patch("workout_wiz.main.hub") as mock_hub:
        mock_hub.invoke.return_value = {
            "messages": [AIMessage(content="ok")],
            "route_decision": None,
            "user_id": "u1",
            "session_id": "s",
            "audit_log": [
                {"event": "router", "route": "COACH", "confidence": 0.85,
                 "tokens_in": 50, "tokens_out": 10, "latency_ms": 100, "provider": "anthropic",
                 "model": "claude-haiku-4-5-20251001", "user_id": "u1"},
            ],
        }
        resp = client.post("/chat", json={"message": "hi"})
    data = resp.json()
    assert len(data["audit_log"]) == 1
    assert data["audit_log"][0]["tokens_in"] == 50
    assert data["route"] == "COACH"
    assert data["confidence"] == 0.85
