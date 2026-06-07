"""Pydantic schemas for the coach copilot endpoints."""
from __future__ import annotations

from pydantic import BaseModel


class MorningTask(BaseModel):
    type: str
    text: str


class ChurnRisk(BaseModel):
    level: str
    reasons: list[str]


class AdherenceWeek(BaseModel):
    week_of: str
    pct: int


class GoalItem(BaseModel):
    id: str
    text: str
    priority: int
    target_date: str | None


class InjuryItem(BaseModel):
    name: str
    region: str
    severity: str
    status: str
    notes: str | None


class CoachBriefResponse(BaseModel):
    member_id: str
    member_name: str
    member_age: int | None
    tier: str | None
    goals: list[GoalItem]
    injuries: list[InjuryItem]
    morning_tasks: list[MorningTask]
    churn_risk: ChurnRisk
    adherence_weeks: list[AdherenceWeek]
    equipment: list[str]


class CoachChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class CoachChatResponse(BaseModel):
    reply: str
    grounded_facts: list[str]
    session_id: str
