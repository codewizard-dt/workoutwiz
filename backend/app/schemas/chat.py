from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        description="The user's natural-language message to the fitness coach",
        examples=["Can you suggest a leg workout for today?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session identifier for conversation continuity; auto-generated if omitted",
        examples=[None],
    )


class ChatResponse(BaseModel):
    session_id: str = Field(
        description="Session identifier, echoed back or newly generated",
        examples=["sess_abc123"],
    )
    reply: str = Field(
        description="The coach's natural-language response",
        examples=["Here is a quad-focused workout for you..."],
    )
    route: str | None = Field(
        default=None,
        description="Intent the router classified this message as (COACH, WORKOUT_LOG, KNOWLEDGE_GRAPH, FALLBACK)",
        examples=["COACH"],
    )
    confidence: float | None = Field(
        default=None,
        description="Router confidence score between 0.0 and 1.0 (null if not available)",
        examples=[0.95],
    )
    audit_log: list[dict[str, Any]] = Field(
        default=[],
        description="Ordered list of internal agent reasoning steps for transparency",
        examples=[[]],
    )
    workout_draft: dict[str, Any] | None = Field(
        default=None,
        description="Structured workout plan (legacy field, always null; use kg_result for workout recommendations)",
    )
    kg_result: dict[str, Any] | None = Field(
        default=None,
        description="Raw knowledge graph recommendation returned by the KG pipeline (KNOWLEDGE_GRAPH route only)",
    )
