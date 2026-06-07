from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage, ToolMessage

from app.agents.hub import hub
from app.agents.audit_persist import persist_audit_log
from app.auth import current_active_user
from app.database import get_async_session
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.errors import ErrorResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory session store: session_id → AgentState snapshot
_sessions: dict[str, dict[str, Any]] = {}


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send a chat message",
    description=(
        "Send a natural-language message to the fitness coaching multi-agent system. "
        "The hub router classifies intent (COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK) "
        "using structured LLM output and delegates to the appropriate sub-agent. "
        "Session history is preserved across calls via the returned session_id."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated — valid JWT Bearer token required"},
        422: {"description": "Validation error — request body failed schema validation"},
    },
)
async def chat(
    request: ChatRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
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
        "user_email": user.email,
        "session_id": session_id,
        "audit_log": [],
        "kg_result": None,
    }

    state["messages"] = list(state["messages"]) + [
        HumanMessage(content=request.message)
    ]

    result = await hub.ainvoke(state)
    _sessions[session_id] = result

    await persist_audit_log(
        session_id=session_id,
        entries=result.get("audit_log", []),
        db=db,
    )

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

    workout_draft = None
    if last_route.get("route") == "WORKOUT_GENERATE":
        import json as _json
        for msg in reversed(result["messages"]):
            if isinstance(msg, ToolMessage) and getattr(msg, "name", "") == "build_workout_tool":
                try:
                    content = msg.content
                    workout_draft = _json.loads(content) if isinstance(content, str) else content
                except Exception:
                    pass
                break

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        route=last_route.get("route"),
        confidence=last_route.get("confidence"),
        audit_log=result.get("audit_log", []),
        workout_draft=workout_draft,
        kg_result=result.get("kg_result"),
    )


@router.get(
    "/audit/{session_id}",
    response_model=dict,
    summary="Get session audit log",
    description=(
        "Retrieve the full LLM reasoning audit log for a chat session. "
        "Returns ordered agent events including route decisions, sub-agent calls, and tool invocations."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found — no conversation with this session_id exists in memory"},
        422: {"description": "Validation error"},
    },
)
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


@router.delete(
    "/session/{session_id}",
    status_code=204,
    summary="Clear a session",
    description="Delete all in-memory conversation history for a chat session. Returns 204 with no body.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"description": "Validation error"},
    },
)
async def clear_session(
    session_id: str,
    user: User = Depends(current_active_user),
) -> None:
    """Clear a conversation session."""
    _sessions.pop(session_id, None)
