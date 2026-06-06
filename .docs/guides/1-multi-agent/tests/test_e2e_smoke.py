"""
End-to-end smoke tests: golden path for each HTTP route.

Uses FastAPI TestClient — no real LLM calls, no running server.
Hub is mocked at the workout_wiz.main module level.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from workout_wiz.main import app, _sessions

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


def _mock_hub_state(session_id: str, reply: str, route: str = "COACH") -> dict:
    """Return a minimal hub output state."""
    return {
        "messages": [AIMessage(content=reply)],
        "route_decision": None,
        "user_id": "smoke-user",
        "session_id": session_id,
        "audit_log": [
            {
                "event": "router",
                "route": route,
                "confidence": 0.9,
                "model": "claude-haiku-4-5-20251001",
                "provider": "anthropic",
                "latency_ms": 120,
                "tokens_in": 80,
                "tokens_out": 15,
                "user_id": "smoke-user",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Route: GET /health
# ---------------------------------------------------------------------------

def test_health_returns_200():
    """GET /health must return HTTP 200 with status=ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Route: GET /
# ---------------------------------------------------------------------------

def test_root_returns_html_with_app_title():
    """GET / must return HTML containing 'Workout Wiz'."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "Workout Wiz" in resp.text


# ---------------------------------------------------------------------------
# Route: POST /chat
# ---------------------------------------------------------------------------

def test_chat_creates_session_and_returns_reply():
    """POST /chat must return a session_id and a non-empty reply."""
    with patch("workout_wiz.main.hub") as mock_hub:
        session_id = "smoke-sess-chat"
        mock_hub.invoke.return_value = _mock_hub_state(session_id, "Here is your coaching advice.")
        resp = client.post(
            "/chat",
            json={"message": "How many rest days should I take?"},
            headers={"X-User-ID": "smoke-user"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["reply"] == "Here is your coaching advice."
    assert data["route"] == "COACH"
    assert isinstance(data["audit_log"], list)
    assert len(data["audit_log"]) == 1


# ---------------------------------------------------------------------------
# Route: GET /audit/{session_id}
# ---------------------------------------------------------------------------

def test_audit_returns_session_audit_log():
    """GET /audit/{session_id} must return the stored audit log for a known session."""
    session_id = "smoke-sess-audit"
    _sessions[session_id] = {
        "messages": [],
        "audit_log": [
            {
                "event": "router",
                "route": "WORKOUT_GENERATE",
                "confidence": 0.88,
                "model": "claude-haiku-4-5-20251001",
                "provider": "anthropic",
                "latency_ms": 95,
                "tokens_in": 60,
                "tokens_out": 10,
                "user_id": "smoke-user",
            }
        ],
    }

    resp = client.get(f"/audit/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["total_entries"] == 1
    assert data["audit_log"][0]["route"] == "WORKOUT_GENERATE"


# ---------------------------------------------------------------------------
# Route: DELETE /session/{session_id}
# ---------------------------------------------------------------------------

def test_delete_session_clears_state():
    """DELETE /session/{id} must remove the session from the in-memory store."""
    session_id = "smoke-sess-delete"
    _sessions[session_id] = {"messages": [], "audit_log": []}

    resp = client.delete(f"/session/{session_id}")
    assert resp.status_code == 200
    assert session_id not in _sessions
