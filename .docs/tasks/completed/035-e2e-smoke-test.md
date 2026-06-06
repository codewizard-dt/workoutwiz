# 035 — End-to-End Smoke Test (Golden Path per Route)

> **Depends on**: [030-chat-endpoint](030-chat-endpoint.md), [031-web-ui](031-web-ui.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md), [036-readme-production-eval](036-readme-production-eval.md)

## Objective

Verify the golden path through every HTTP route in the FastAPI app using `TestClient` — no real LLM calls, no running server required. Covers health check, HTML UI response, the `/chat` endpoint (session creation + reply), the `/audit` endpoint, and session deletion.

## Approach

Use FastAPI's `TestClient` (backed by `httpx`) to make synchronous HTTP requests against the app in-process. The hub `StateGraph` is patched at the `workout_wiz.main` module level so no LangGraph or Anthropic imports need to resolve at test time. Each test exercises exactly one route and asserts both status code and response shape. The test file is self-contained — a fresh import of `app` is used, and `_sessions` is cleared between tests via an autouse fixture.

## Steps

### 1. Create tests/test_e2e_smoke.py  <!-- agent: general-purpose -->

Create `.docs/guides/1-multi-agent/tests/test_e2e_smoke.py`:

```python
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
```

- [ ] File exists at `.docs/guides/1-multi-agent/tests/test_e2e_smoke.py`
- [ ] Five test functions defined (one per route in acceptance criteria)
- [ ] Hub is mocked — no real LangGraph or Anthropic calls
- [ ] `autouse` fixture clears `_sessions` before/after each test

### 2. Verify the HTML UI endpoint exists  <!-- agent: general-purpose -->

Confirm `GET /` is defined in `src/workout_wiz/main.py` and returns an HTML response containing "Workout Wiz". If the route exists but returns plain text, update it to return `HTMLResponse` with the correct title:

```python
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def index():
    # Serves the static chat UI — see task 031 for the full template
    with open(Path(__file__).parent / "demo" / "index.html") as f:
        return HTMLResponse(content=f.read())
```

Or if the UI is inline:

```python
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="<html><head><title>Workout Wiz</title></head><body>...</body></html>")
```

- [ ] `GET /` returns `Content-Type: text/html`
- [ ] Response body contains the string "Workout Wiz"

### 3. Run the tests  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent && .venv/bin/pytest tests/test_e2e_smoke.py -v
```

- [ ] All 5 tests pass
- [ ] No real LLM calls are made

### 4. Add to CI pytest run  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent && .venv/bin/pytest --collect-only tests/test_e2e_smoke.py
```

- [ ] pytest collects 5 tests from this file

## Acceptance Criteria

- [ ] `tests/test_e2e_smoke.py` exists with 5 test cases (one per route)
- [ ] `GET /health` returns HTTP 200 with `{"status": "ok"}`
- [ ] `GET /` returns HTML containing "Workout Wiz"
- [ ] `POST /chat` returns `session_id` and a reply (mocked hub)
- [ ] `GET /audit/{session_id}` returns the stored audit log
- [ ] `DELETE /session/{id}` removes the session from the in-memory store
- [ ] `pytest tests/test_e2e_smoke.py` passes (5/5) without an API key

---
**UAT**: [`.docs/uat/035-e2e-smoke-test.uat.md`](../uat/035-e2e-smoke-test.uat.md)
