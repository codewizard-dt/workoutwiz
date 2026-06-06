from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage

from app.agents.hub import hub
from app.auth import current_active_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory session store: session_id → AgentState snapshot
_sessions: dict[str, dict[str, Any]] = {}


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(current_active_user),
) -> ChatResponse:
    """Send a message to the fitness coaching multi-agent system.

    Requires a valid JWT Bearer token. Session history is preserved
    across calls using the returned session_id.
    """
    session_id = request.session_id or str(uuid.uuid4())

    state = _sessions.get(session_id) or {
        "messages": [],
        "route_decision": None,
        "user_id": str(user.id),
        "session_id": session_id,
        "audit_log": [],
    }

    state["messages"] = list(state["messages"]) + [
        HumanMessage(content=request.message)
    ]

    result = hub.invoke(state)
    _sessions[session_id] = result

    ai_messages = [
        m for m in result["messages"]
        if hasattr(m, "type") and m.type == "ai"
    ]
    reply = ai_messages[-1].content if ai_messages else "(no response)"

    router_entries = [
        e for e in result.get("audit_log", [])
        if e.get("event") == "router"
    ]
    last_route = router_entries[-1] if router_entries else {}

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        route=last_route.get("route"),
        confidence=last_route.get("confidence"),
        audit_log=result.get("audit_log", []),
    )


@router.get("/audit/{session_id}")
async def get_audit(
    session_id: str,
    user: User = Depends(current_active_user),
) -> dict[str, Any]:
    """Retrieve the full LLM audit log for a session."""
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return {
        "session_id": session_id,
        "audit_log": state.get("audit_log", []),
        "total_entries": len(state.get("audit_log", [])),
    }


@router.delete("/session/{session_id}", status_code=204)
async def clear_session(
    session_id: str,
    user: User = Depends(current_active_user),
) -> None:
    """Clear a conversation session."""
    _sessions.pop(session_id, None)
