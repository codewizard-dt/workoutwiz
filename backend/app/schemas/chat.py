from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    route: str | None = None
    confidence: float | None = None
    audit_log: list[dict[str, Any]] = []
