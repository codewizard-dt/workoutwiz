import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

# In-memory session store: session_id -> AgentState snapshot
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


# Serve demo UI — compute path relative to this file
_DEMO_DIR = Path(__file__).parent.parent.parent / "demo"


@app.get("/", response_class=HTMLResponse)
async def ui():
    """Serve the chat UI."""
    index = _DEMO_DIR / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>Demo UI not found</h1>", status_code=404)
    return HTMLResponse(index.read_text())


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"cleared": session_id}


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
