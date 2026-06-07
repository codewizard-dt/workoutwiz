"""Coach copilot router — /coach/brief and /coach/chat.

Surfaces Jordan Rivera's full member context from Neo4j for the coach UI demo.
The demo member is identified by email; all data originates from the KG seed.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import neo4j
from fastapi import APIRouter, Depends, HTTPException
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.auth import current_active_user
from app.config import settings
from app.kg.driver import get_neo4j_driver
from app.models.user import User
from app.schemas.coach import (
    AdherenceWeek,
    ChurnRisk,
    CoachBriefResponse,
    CoachChatRequest,
    CoachChatResponse,
    GoalItem,
    InjuryItem,
    MorningTask,
)
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coach", tags=["coach"])




# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



async def _fetch_member_context(driver: neo4j.AsyncDriver, email: str) -> dict[str, Any]:
    """Query Neo4j for the full member context by email."""
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (m:Member {email: $email})
            OPTIONAL MATCH (m)-[:HAS_GOAL]->(g:Goal)
            OPTIONAL MATCH (m)-[:HAS_INJURY]->(i:Injury)
            OPTIONAL MATCH (m)-[:REPORTED_ADHERENCE]->(a:AdherenceWeek)
            OPTIONAL MATCH (m)-[:HAS_COACH_BRIEF]->(cb:CoachBrief)
            OPTIONAL MATCH (m)-[:HAS_BIOMARKER]->(b:BiomarkerSnapshot)
            OPTIONAL MATCH (m)-[:HAS_LAB_RESULT]->(l:LabResult)
            OPTIONAL MATCH (m)-[:HAD_WORKOUT]->(w:AssessmentWorkout)
            OPTIONAL MATCH (m)-[:SENT_MESSAGE]->(cm:ChatMessage)
            RETURN
                m,
                collect(DISTINCT g) AS goals,
                collect(DISTINCT i) AS injuries,
                collect(DISTINCT a) AS adherence,
                cb,
                b AS biomarkers,
                collect(DISTINCT l) AS labs,
                collect(DISTINCT w) AS workouts,
                collect(DISTINCT cm) AS chat_messages
            """,
            email=email,
        )
        record = await result.single()
        if record is None:
            return {}

        def node_props(node: Any) -> dict[str, Any]:
            return dict(node) if node is not None else {}

        return {
            "member": node_props(record["m"]),
            "goals": [node_props(g) for g in record["goals"] if g is not None],
            "injuries": [node_props(i) for i in record["injuries"] if i is not None],
            "adherence": sorted(
                [node_props(a) for a in record["adherence"] if a is not None],
                key=lambda x: x.get("week_of", ""),
            ),
            "coach_brief": node_props(record["cb"]),
            "biomarkers": node_props(record["biomarkers"]),
            "labs": [node_props(l) for l in record["labs"] if l is not None],
            "workouts": sorted(
                [node_props(w) for w in record["workouts"] if w is not None],
                key=lambda x: x.get("date", ""),
                reverse=True,
            ),
            "chat_messages": sorted(
                [node_props(cm) for cm in record["chat_messages"] if cm is not None],
                key=lambda x: x.get("ts", ""),
                reverse=True,
            ),
        }


def _build_context_prompt(ctx: dict[str, Any]) -> str:
    """Assemble a rich context string for the LLM from Neo4j data."""
    m = ctx.get("member", {})
    lines: list[str] = [
        f"MEMBER: {m.get('display_name', m.get('name', 'Unknown'))}, "
        f"age {m.get('age', '?')}, {m.get('sex', '?')}, "
        f"tier: {m.get('tier', '?')}, "
        f"member since: {m.get('member_since', '?')}",
        "",
        "GOALS:",
    ]
    for g in ctx.get("goals", []):
        td = g.get("target_date") or "ongoing"
        lines.append(f"  - (P{g.get('priority', '?')}) {g.get('text', '')} [by {td}]")

    lines += ["", "INJURIES:"]
    for i in ctx.get("injuries", []):
        lines.append(
            f"  - {i.get('name', '')} | {i.get('status', '')} | {i.get('severity', '')} | "
            f"{i.get('notes', '')}"
        )

    lines += ["", "EQUIPMENT: " + ", ".join(m.get("equipment_available", []))]

    lines += ["", "ADHERENCE (last 4 weeks):"]
    for a in ctx.get("adherence", []):
        lines.append(f"  - week of {a.get('week_of', '?')}: {a.get('pct', '?')}%")

    bio = ctx.get("biomarkers", {})
    if bio:
        sleep = bio.get("sleep_hours_last_7_days", [])
        avg_sleep = round(sum(sleep) / len(sleep), 1) if sleep else "?"
        lines += [
            "",
            "BIOMARKERS:",
            f"  Resting HR: {bio.get('resting_hr_bpm', '?')} bpm | HRV: {bio.get('hrv_ms', '?')} ms",
            f"  Avg sleep (7d): {avg_sleep} hrs",
            f"  Weight trend: {' → '.join(str(k) + ' kg' for k in bio.get('weight_trend_kg', []))}",
        ]

    labs = ctx.get("labs", [])
    if labs:
        lines += ["", "LAB RESULTS:"]
        for lab in labs:
            if lab.get("type") == "blood_panel":
                lines.append(
                    f"  Blood panel ({lab.get('date', '?')}): "
                    f"LDL {lab.get('ldl_mg_dl')} | HDL {lab.get('hdl_mg_dl')} | "
                    f"HbA1c {lab.get('hba1c_pct')}% | Vit D {lab.get('vitamin_d_ng_ml')} ng/mL | "
                    f"CRP {lab.get('crp_mg_l')} mg/L"
                )
            elif lab.get("type") == "dexa_scan":
                lines.append(
                    f"  DEXA ({lab.get('date', '?')}): "
                    f"BF% {lab.get('body_fat_pct')} | Lean {lab.get('lean_mass_kg')} kg | "
                    f"Visceral fat {lab.get('visceral_fat_cm2')} cm²"
                )

    lines += ["", "RECENT WORKOUTS:"]
    for w in ctx.get("workouts", [])[:4]:
        status = "✓" if w.get("completed") else "✗ (missed)"
        exs = ", ".join(w.get("exercises", [])) or "—"
        lines.append(
            f"  {w.get('date', '?')} {status} {w.get('title', '')} "
            f"({w.get('duration_min', 0)} min, RPE {w.get('rpe', '?')}): {exs}"
        )

    cb = ctx.get("coach_brief", {})
    if cb:
        lines += [
            "",
            f"CHURN RISK: {cb.get('churn_risk_level', '?').upper()}",
            "  Reasons: " + "; ".join(cb.get("churn_risk_reasons", [])),
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/brief",
    response_model=CoachBriefResponse,
    summary="Get coach morning brief for demo member",
    description=(
        "Returns the morning brief, adherence trend, goals, injuries, and churn risk "
        "for the assessment demo member (Jordan Rivera). Data is retrieved live from Neo4j."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Demo member not found in graph"},
        500: {"model": ErrorResponse, "description": "Neo4j query error"},
    },
)
async def get_coach_brief(
    user: User = Depends(current_active_user),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> CoachBriefResponse:
    try:
        ctx = await _fetch_member_context(driver, user.email)
        if not ctx or not ctx.get("member"):
            raise HTTPException(
                status_code=404,
                detail="No coaching profile found for your account. Ask an admin to seed your member context.",
            )

        m = ctx["member"]
        cb = ctx.get("coach_brief", {})

        task_types = cb.get("morning_task_types", [])
        task_texts = cb.get("morning_task_texts", [])
        morning_tasks = [
            MorningTask(type=t, text=txt)
            for t, txt in zip(task_types, task_texts, strict=False)
        ]

        return CoachBriefResponse(
            member_id=m.get("id", ""),
            member_name=m.get("display_name", m.get("name", "")),
            member_age=m.get("age"),
            tier=m.get("tier"),
            goals=[
                GoalItem(
                    id=g.get("id", ""),
                    text=g.get("text", ""),
                    priority=g.get("priority", 2),
                    target_date=g.get("target_date"),
                )
                for g in ctx.get("goals", [])
            ],
            injuries=[
                InjuryItem(
                    name=i.get("name", ""),
                    region=i.get("region", ""),
                    severity=i.get("severity", ""),
                    status=i.get("status", ""),
                    notes=i.get("notes"),
                )
                for i in ctx.get("injuries", [])
            ],
            morning_tasks=morning_tasks,
            churn_risk=ChurnRisk(
                level=cb.get("churn_risk_level", "unknown"),
                reasons=cb.get("churn_risk_reasons", []),
            ),
            adherence_weeks=[
                AdherenceWeek(
                    week_of=a.get("week_of", ""),
                    pct=int(a.get("pct", 0)),
                )
                for a in ctx.get("adherence", [])
            ],
            equipment=list(m.get("equipment_available", [])),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /coach/brief")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/chat",
    response_model=CoachChatResponse,
    summary="Coach copilot chat grounded in member context",
    description=(
        "Answers coach queries grounded in Jordan Rivera's live member context from Neo4j. "
        "Supports questions about adherence, sleep, goals, injuries, labs, and workout history."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "LLM or Neo4j error"},
    },
)
async def coach_chat(
    request: CoachChatRequest,
    user: User = Depends(current_active_user),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> CoachChatResponse:
    session_id = request.session_id or str(uuid.uuid4())

    try:
        ctx = await _fetch_member_context(driver, user.email)
        if not ctx or not ctx.get("member"):
            raise HTTPException(
                status_code=404,
                detail="No coaching profile found for your account. Ask an admin to seed your member context.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error fetching member context for coach chat")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    member_context = _build_context_prompt(ctx)

    system_prompt = f"""You are an AI fitness coach copilot helping a human coach understand and act on their member's data.

Answer questions concisely using ONLY the member context provided below. Do not invent data.
If the data doesn't contain what's needed, say so explicitly.

When answering, cite the specific facts from the context (e.g., "adherence dropped from 100% to 50%").
For trend questions, describe the direction and magnitude.
Keep answers brief and actionable — the coach is on a morning check-in.

MEMBER CONTEXT:
{member_context}"""

    llm = ChatAnthropic(
        model=settings.coach_model,
        api_key=settings.anthropic_api_key,
    )

    t0 = time.monotonic()
    try:
        response = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=request.message)]
        )
    except Exception as exc:
        logger.exception("LLM error in /coach/chat")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    latency_ms = int((time.monotonic() - t0) * 1000)
    logger.info("coach_chat latency=%d ms", latency_ms)

    reply = str(response.content)

    # Extract grounded facts mentioned in the reply (simple keyword scan)
    grounded_facts: list[str] = []
    cb = ctx.get("coach_brief", {})
    adherence = ctx.get("adherence", [])

    if adherence:
        pcts = [a.get("pct", 0) for a in adherence]
        grounded_facts.append(f"Adherence: {' → '.join(str(p) + '%' for p in pcts)}")
    if cb.get("churn_risk_level"):
        grounded_facts.append(f"Churn risk: {cb['churn_risk_level']}")
    goals = ctx.get("goals", [])
    if goals:
        grounded_facts.append(f"Goals: {', '.join(g.get('text', '') for g in goals[:2])}")
    injuries = ctx.get("injuries", [])
    if injuries:
        grounded_facts.append(f"Active injury: {injuries[0].get('name', '')} ({injuries[0].get('status', '')})")

    return CoachChatResponse(
        reply=reply,
        grounded_facts=grounded_facts,
        session_id=session_id,
    )
