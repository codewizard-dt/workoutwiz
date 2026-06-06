# 030 — POST /chat Endpoint with Session Support

> **Depends on**: [024-router-node](024-router-node.md), [027-coach-sub-agent](027-coach-sub-agent.md), [028-workout-generator-sub-agent](028-workout-generator-sub-agent.md), [029-workout-logger-sub-agent](029-workout-logger-sub-agent.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Implement a `POST /chat` FastAPI endpoint that accepts user messages with a session/thread ID, invokes the hub `StateGraph` with multi-turn conversation history, and returns the agent's response — the primary integration point between the web UI and the multi-agent system.

## Approach

The FastAPI app lives at `src/workout_wiz/main.py`. The `/chat` endpoint uses an in-memory session store (dict keyed by `session_id`) that accumulates `AgentState` across turns. Each request: appends the new user message to session history, invokes `hub` with the full state, and returns the last AI message. A `user_id` is extracted from a simple `X-User-ID` header (no JWT for this assessment). The endpoint also returns the audit log entry from the last turn.

## Steps

### 1. Create src/workout_wiz/main.py  <!-- agent: general-purpose -->

Create `.docs/guides/1-multi-agent/src/workout_wiz/main.py`:

```python
import uuid
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from workout_wiz.hub import hub

app = FastAPI(title="Workout Wiz Multi-Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id → AgentState snapshot
_sessions: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    route: Optional[str] = None
    confidence: Optional[float] = None
    audit_log: list[dict] = []


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
):
    session_id = request.session_id or str(uuid.uuid4())

    # Load or initialize session state
    state = _sessions.get(session_id, {
        "messages": [],
        "route_decision": None,
        "user_id": x_user_id,
        "session_id": session_id,
        "audit_log": [],
    })

    # Append new user message
    state["messages"] = list(state["messages"]) + [HumanMessage(content=request.message)]

    # Invoke the hub
    result = hub.invoke(state)

    # Persist updated state
    _sessions[session_id] = result

    # Extract reply (last AI message)
    ai_messages = [m for m in result["messages"] if hasattr(m, "type") and m.type == "ai"]
    reply = ai_messages[-1].content if ai_messages else "(no response)"

    # Extract routing info from audit log
    router_entries = [e for e in result.get("audit_log", []) if e.get("event") == "router"]
    last_route = router_entries[-1] if router_entries else {}

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        route=last_route.get("route"),
        confidence=last_route.get("confidence"),
        audit_log=result.get("audit_log", []),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"cleared": session_id}
```

- [ ] `src/workout_wiz/main.py` exists with `app = FastAPI(...)`
- [ ] `POST /chat` accepts `ChatRequest` with `message` and optional `session_id`
- [ ] Session history is accumulated in `_sessions` dict across turns
- [ ] `X-User-ID` header populates `user_id` in state (defaults to "anonymous")
- [ ] Response includes `session_id`, `reply`, `route`, `confidence`, `audit_log`
- [ ] `GET /health` returns `{"status": "ok"}`

### 2. Write endpoint tests  <!-- agent: general-purpose -->

Create `.docs/guides/1-multi-agent/tests/test_chat_endpoint.py`:

```python
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
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_chat_endpoint.py -v`

- [ ] All 5 tests pass (mocked hub — no real LLM calls)

### 3. Verify server starts  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent
source .venv/bin/activate
timeout 5 python -c "
import uvicorn, threading, time, httpx
def run(): uvicorn.run('workout_wiz.main:app', port=18001, log_level='error')
t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(2)
r = httpx.get('http://localhost:18001/health')
print('Health:', r.json())
" || true
```

- [ ] Server starts without import errors (even if timeout kills it, the Health check must print)

## Acceptance Criteria

- [ ] `src/workout_wiz/main.py` with `POST /chat`, `GET /health`, `DELETE /session/{id}`
- [ ] Session state persists across turns within the same `session_id`
- [ ] `X-User-ID` header flows through to `AgentState.user_id`
- [ ] Response includes `route` and `confidence` from the audit log
- [ ] `pytest tests/test_chat_endpoint.py` passes (5/5)
