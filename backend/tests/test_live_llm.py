"""
Live LLM integration tests — hit real Anthropic API, assert real audit telemetry.

Run with:
    pytest -m live -v

Skipped automatically when ANTHROPIC_API_KEY is absent from the root .env.
"""
import uuid
import pytest
from httpx import AsyncClient

from app.config import settings
from tests.test_auth import register_and_login


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def skip_without_api_key():
    if not settings.anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not set in root .env")


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    email = f"live_{uuid.uuid4().hex[:8]}@example.com"
    token = await register_and_login(client, email, "S3cur3Pass!")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _chat(client: AsyncClient, headers: dict, message: str, session_id: str | None = None):
    payload: dict = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    resp = await client.post("/chat/", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _assert_real_llm(entry: dict) -> None:
    """Verify an audit entry contains real LLM telemetry (not mocked zeros)."""
    assert entry["latency_ms"] > 0, "latency_ms should be > 0 for a real LLM call"
    assert entry["tokens_in"] > 0, "tokens_in should be > 0 for a real LLM call"
    assert entry["tokens_out"] > 0, "tokens_out should be > 0 for a real LLM call"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.live
async def test_coach_route_live(client: AsyncClient, auth_headers: dict):
    data = await _chat(client, auth_headers, "What's the best approach for building upper body strength?")

    assert data["route"] == "COACH"
    assert data["confidence"] is not None and data["confidence"] >= 0.6
    assert data["reply"]

    audit = data["audit_log"]
    events = [e["event"] for e in audit]
    assert "router" in events, f"Expected 'router' in audit events, got: {events}"
    assert "coach" in events, f"Expected 'coach' in audit events, got: {events}"

    _assert_real_llm(next(e for e in audit if e["event"] == "router"))
    _assert_real_llm(next(e for e in audit if e["event"] == "coach"))


@pytest.mark.live
async def test_workout_generate_route_live(client: AsyncClient, auth_headers: dict):
    data = await _chat(client, auth_headers, "Create a 30-minute leg day workout for an intermediate lifter")

    assert data["route"] == "WORKOUT_GENERATE"
    assert data["reply"]

    audit = data["audit_log"]
    events = [e["event"] for e in audit]
    assert "router" in events
    assert "generator" in events, f"Expected 'generator' in audit events, got: {events}"

    _assert_real_llm(next(e for e in audit if e["event"] == "router"))
    _assert_real_llm(next(e for e in audit if e["event"] == "generator"))


@pytest.mark.live
async def test_workout_log_route_live(client: AsyncClient, auth_headers: dict):
    data = await _chat(client, auth_headers, "I did 3 sets of 10 squats at 80kg and ran for 20 minutes")

    assert data["route"] == "WORKOUT_LOG"
    assert data["reply"]

    audit = data["audit_log"]
    events = [e["event"] for e in audit]
    assert "router" in events
    assert "logger" in events, f"Expected 'logger' in audit events, got: {events}"

    _assert_real_llm(next(e for e in audit if e["event"] == "router"))
    _assert_real_llm(next(e for e in audit if e["event"] == "logger"))


@pytest.mark.live
async def test_clarification_route_live(client: AsyncClient, auth_headers: dict):
    # Very short, ambiguous message should hit clarification
    data = await _chat(client, auth_headers, "hey")

    audit = data["audit_log"]
    events = [e["event"] for e in audit]
    assert "router" in events

    _assert_real_llm(next(e for e in audit if e["event"] == "router"))

    # Response should mention coaching or workout options
    reply_lower = data["reply"].lower()
    assert any(word in reply_lower for word in ("coach", "workout", "log", "fitness", "help")), (
        f"Clarification reply should mention fitness options, got: {data['reply']}"
    )


@pytest.mark.live
async def test_audit_endpoint_live(client: AsyncClient, auth_headers: dict):
    # Seed a real chat so the audit log has entries
    first = await _chat(client, auth_headers, "How many rest days per week should I take?")
    session_id = first["session_id"]

    resp = await client.get(f"/chat/audit/{session_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["session_id"] == session_id
    assert body["total_entries"] >= 2  # at minimum: router + sub-agent

    for entry in body["audit_log"]:
        assert "event" in entry
        assert "latency_ms" in entry
        assert "tokens_in" in entry
        assert "tokens_out" in entry
        assert entry["latency_ms"] > 0


@pytest.mark.live
async def test_multi_turn_session_live(client: AsyncClient, auth_headers: dict):
    first = await _chat(client, auth_headers, "What is progressive overload?")
    session_id = first["session_id"]
    first_audit_len = len(first["audit_log"])

    second = await _chat(client, auth_headers, "Give me an example for bench press", session_id=session_id)

    assert second["session_id"] == session_id
    assert len(second["audit_log"]) > first_audit_len, (
        "Audit log should grow across turns in the same session"
    )
    assert second["reply"]
