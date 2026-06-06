from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    route: Optional[str] = None
    confidence: Optional[float] = None
    audit_log: list[dict] = []
