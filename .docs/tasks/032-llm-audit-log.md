# 032 — Per-Call LLM Audit Log

> **Depends on**: [030-chat-endpoint](030-chat-endpoint.md)
> **Blocks**: none
> **Parallel-safe with**: [031-web-ui](031-web-ui.md)

## Objective

Finalize the per-call LLM audit log so every invocation records tokens in/out, model name, provider, user ID, route taken, and latency — and expose this data in the `/chat` response and a dedicated `GET /audit/{session_id}` endpoint.

## Approach

The router node already appends a basic audit entry in task 024. This task extends it: adds token counts using LangChain's callback mechanism (`get_openai_callback` equivalent for Anthropic), ensures all three sub-agent nodes (coach, generator, logger) also append their own audit entries, and adds a `/audit/{session_id}` endpoint that returns the full audit trail for a session. The audit log stays in memory (no persistence) — appropriate for a demo system.

## Steps

### 1. Add token counting to router node  <!-- agent: general-purpose -->

Modify `_router_node` in `src/workout_wiz/hub.py` to capture token usage via `anthropic_usage` metadata from the LangChain response. After the `llm.invoke()` call:

```python
# Get token usage from the response metadata (LangChain stores it there)
usage = getattr(response, "usage_metadata", None) or {}
audit_entry = {
    "event": "router",
    "model": model_name,
    "provider": "anthropic",
    "route": route_decision.intent.value,
    "confidence": route_decision.confidence,
    "latency_ms": latency_ms,
    "user_id": state.get("user_id"),
    "tokens_in": usage.get("input_tokens", 0),
    "tokens_out": usage.get("output_tokens", 0),
}
```

Note: `ChatAnthropic`'s response object has `response_metadata` with token counts. Check the actual field name by printing `response.response_metadata` and adjust accordingly. Common keys: `input_tokens`, `output_tokens`.

- [ ] Router audit entry includes `tokens_in` and `tokens_out` fields
- [ ] Tokens default to 0 if metadata not available (defensive)

### 2. Add audit entries to sub-agent nodes  <!-- agent: general-purpose -->

Add audit logging to coach, generator, and logger nodes. Each node should append an audit entry after its LLM call:

**In `src/workout_wiz/agents/coach.py`** (`_chat_node`):
```python
usage = getattr(response, "response_metadata", {})
audit_entry = {
    "event": "coach",
    "model": model_name,
    "provider": "anthropic",
    "latency_ms": latency_ms,  # add time.monotonic() timing
    "tokens_in": usage.get("usage", {}).get("input_tokens", 0),
    "tokens_out": usage.get("usage", {}).get("output_tokens", 0),
}
return {
    "messages": [response],
    "audit_log": list(state.get("audit_log", [])) + [audit_entry],
}
```

Apply the same pattern to `_generate_node` in `workout_generator.py` and `_log_node` in `workout_logger.py`. Add `import time` to each file if not present. Wrap the LLM call with `t0 = time.monotonic()` / `latency_ms = int((time.monotonic() - t0) * 1000)`.

- [ ] `_chat_node` in `coach.py` returns `audit_log` with an appended entry
- [ ] `_generate_node` in `workout_generator.py` returns `audit_log` with an appended entry
- [ ] `_log_node` in `workout_logger.py` returns `audit_log` with an appended entry
- [ ] All entries include: event, model, provider, latency_ms, tokens_in, tokens_out

### 3. Add /audit endpoint  <!-- agent: general-purpose -->

Add to `src/workout_wiz/main.py`:

```python
@app.get("/audit/{session_id}")
async def get_audit(session_id: str):
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {
        "session_id": session_id,
        "audit_log": state.get("audit_log", []),
        "total_entries": len(state.get("audit_log", [])),
    }
```

- [ ] `GET /audit/{session_id}` returns full audit log for a session
- [ ] Returns 404 for unknown session IDs

### 4. Write audit tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_audit.py`:

```python
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
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_audit.py -v`

- [ ] All 3 tests pass

## Acceptance Criteria

- [ ] Router audit entry includes `tokens_in` and `tokens_out` (defaults to 0 if unavailable)
- [ ] Coach, generator, and logger nodes each append an audit entry with event, model, provider, latency_ms, tokens_in, tokens_out
- [ ] `GET /audit/{session_id}` returns the full audit log for a session
- [ ] `GET /audit/{unknown}` returns 404
- [ ] `pytest tests/test_audit.py` passes (3/3)
