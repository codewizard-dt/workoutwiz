"""Coach copilot router — /coach/brief and /coach/chat.

Surfaces Jordan Rivera's full member context from Neo4j for the coach UI demo.
The demo member is identified by email; all data originates from the KG seed.
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

import neo4j
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.auth import current_active_user
from app.config import settings
from app.kg.driver import get_neo4j_driver
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.coach_draft import CoachDraft, CoachDraftContentType, CoachDraftStatus
from app.schemas.coach import (
    AdherenceWeek,
    ChurnRisk,
    CoachBriefResponse,
    CoachChatRequest,
    CoachChatResponse,
    CoachDraftSchema,
    CoachMemberSummary,
    GoalItem,
    InjuryItem,
    MessagePatternPoint,
    MorningTask,
    NudgeRequest,
    NudgeResponse,
    WeeklyComparisonPoint,
)
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coach", tags=["coach"])


def _draft_to_schema(draft: CoachDraft) -> CoachDraftSchema:
    import json
    grounded_on: list[str] = []
    if draft.grounded_on:
        try:
            grounded_on = json.loads(draft.grounded_on)
        except (ValueError, TypeError):
            grounded_on = [draft.grounded_on]
    return CoachDraftSchema(
        id=str(draft.id),
        member_id=draft.member_id,
        member_name=draft.member_name,
        content_type=draft.content_type.value,
        body=draft.body,
        grounded_on=grounded_on,
        status=draft.status.value,
        created_by=draft.created_by,
        approved_by=draft.approved_by,
        approved_at=draft.approved_at.isoformat() if draft.approved_at else None,
        sent_at=draft.sent_at.isoformat() if draft.sent_at else None,
        created_at=draft.created_at.isoformat(),
    )





# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



async def _fetch_member_context(
    driver: neo4j.AsyncDriver,
    email: str,
    member_id: str | None = None,
) -> dict[str, Any]:
    """Query Neo4j for the full member context by email or member_id."""
    async with driver.session() as session:
        if member_id is not None:
            result = await session.run(
                """
                MATCH (m:Member {id: $member_id})
                OPTIONAL MATCH (m)-[:HAS_GOAL]->(g:Goal)
                OPTIONAL MATCH (m)-[:HAS_INJURY]->(i:Injury)
                OPTIONAL MATCH (m)-[:REPORTED_ADHERENCE]->(a:AdherenceWeek)
                OPTIONAL MATCH (m)-[:HAS_COACH_BRIEF]->(cb:CoachBrief)
                OPTIONAL MATCH (m)-[:HAS_BIOMARKER]->(b:BiomarkerSnapshot)
                OPTIONAL MATCH (m)-[:HAS_LAB_RESULT]->(l:LabResult)
                OPTIONAL MATCH (m)-[:HAD_WORKOUT]->(w:AssessmentWorkout)
                OPTIONAL MATCH (m)-[:SENT_MESSAGE]->(cm:ChatMessage)
                OPTIONAL MATCH (m)-[:SENT_COACH_MESSAGE]->(ccm:ChatMessage)
                RETURN
                    m,
                    collect(DISTINCT g) AS goals,
                    collect(DISTINCT i) AS injuries,
                    collect(DISTINCT a) AS adherence,
                    cb,
                    b AS biomarkers,
                    collect(DISTINCT l) AS labs,
                    collect(DISTINCT w) AS workouts,
                    collect(DISTINCT cm) AS chat_messages,
                    collect(DISTINCT ccm) AS coach_messages
                """,
                member_id=member_id,
            )
        else:
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
            OPTIONAL MATCH (m)-[:SENT_COACH_MESSAGE]->(ccm:ChatMessage)
            RETURN
                m,
                collect(DISTINCT g) AS goals,
                collect(DISTINCT i) AS injuries,
                collect(DISTINCT a) AS adherence,
                cb,
                b AS biomarkers,
                collect(DISTINCT l) AS labs,
                collect(DISTINCT w) AS workouts,
                collect(DISTINCT cm) AS chat_messages,
                collect(DISTINCT ccm) AS coach_messages
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
            "coach_messages": sorted(
                [node_props(ccm) for ccm in record["coach_messages"] if ccm is not None],
                key=lambda x: x.get("ts", ""),
                reverse=True,
            ),
        }


def _build_context_audit(ctx: dict[str, Any], retrieval_ms: int) -> list[dict[str, Any]]:
    """Agent-step trace reflecting the Neo4j member-context graph traversal.

    Member context is assembled in a single Cypher query that fans out across
    the member's relationships. The measured latency is attributed to that
    graph lookup, and each relationship that actually surfaced data is emitted
    as a sub-step so the trace mirrors the traversal the graph performed.
    """
    steps: list[dict[str, Any]] = [
        {
            "event": "graph_member_lookup",
            "provider": "neo4j",
            "latency_ms": retrieval_ms,
            "detail": "MATCH (m:Member) — context traversal",
        }
    ]

    sections: list[tuple[str, str, int]] = [
        ("graph_goals", "HAS_GOAL → Goal", len(ctx.get("goals", []))),
        ("graph_injuries", "HAS_INJURY → Injury", len(ctx.get("injuries", []))),
        ("graph_adherence", "REPORTED_ADHERENCE → AdherenceWeek", len(ctx.get("adherence", []))),
        ("graph_workouts", "HAD_WORKOUT → AssessmentWorkout", len(ctx.get("workouts", []))),
        ("graph_labs", "HAS_LAB_RESULT → LabResult", len(ctx.get("labs", []))),
        ("graph_chat_history", "SENT_MESSAGE → ChatMessage", len(ctx.get("chat_messages", []))),
        ("graph_coach_messages", "SENT_COACH_MESSAGE → ChatMessage", len(ctx.get("coach_messages", []))),
    ]
    for event, rel, count in sections:
        if count > 0:
            steps.append(
                {
                    "event": event,
                    "provider": "neo4j",
                    "detail": f"{rel} · {count} node{'s' if count != 1 else ''}",
                }
            )

    if ctx.get("coach_brief"):
        steps.append(
            {"event": "graph_coach_brief", "provider": "neo4j", "detail": "HAS_COACH_BRIEF → CoachBrief"}
        )
    if ctx.get("biomarkers"):
        steps.append(
            {"event": "graph_biomarkers", "provider": "neo4j", "detail": "HAS_BIOMARKER → BiomarkerSnapshot"}
        )

    return steps


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

    # Recent Conversations (merged member + coach messages, newest first, up to 10)
    all_msgs = sorted(
        ctx.get("chat_messages", []) + ctx.get("coach_messages", []),
        key=lambda x: x.get("ts", ""),
        reverse=True,
    )[:10]
    if all_msgs:
        lines += ["", "--- Recent Conversations ---"]
        for msg in all_msgs:
            ts = msg.get("ts", "")
            date_str = ts[:10] if ts else "?"
            speaker = msg.get("sender", "?")
            text = msg.get("text", "")
            lines.append(f"[{date_str} {speaker}]: {text}")

    return "\n".join(lines)


def _iso_to_week(ts: str) -> str:
    """Return the ISO week-start date string (Monday) for a timestamp string."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""
    # Subtract to Monday of the week
    monday = dt.date() - __import__("datetime").timedelta(days=dt.weekday())
    return str(monday)


def _build_message_pattern(
    chat_messages: list[dict[str, Any]],
    coach_messages: list[dict[str, Any]],
) -> list[MessagePatternPoint]:
    """Bucket member and coach messages by ISO week (last 8 weeks)."""
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"member": 0, "coach": 0})
    for msg in chat_messages:
        week = _iso_to_week(msg.get("ts", ""))
        if week:
            buckets[week]["member"] += 1
    for msg in coach_messages:
        week = _iso_to_week(msg.get("ts", ""))
        if week:
            buckets[week]["coach"] += 1

    sorted_weeks = sorted(buckets.keys())[-8:]
    return [
        MessagePatternPoint(
            week_of=w,
            member_count=buckets[w]["member"],
            coach_count=buckets[w]["coach"],
        )
        for w in sorted_weeks
    ]


def _build_weekly_comparison(
    adherence: list[dict[str, Any]],
    workouts: list[dict[str, Any]],
    chat_messages: list[dict[str, Any]],
    coach_messages: list[dict[str, Any]],
) -> list[WeeklyComparisonPoint]:
    """Build per-week comparison data (last 4 weeks) across adherence, workouts, and messages."""
    # Build adherence lookup by week_of
    adherence_by_week: dict[str, int] = {
        a.get("week_of", ""): int(a.get("pct", 0)) for a in adherence if a.get("week_of")
    }

    # Count completed workouts by week
    workout_counts: dict[str, int] = defaultdict(int)
    for w in workouts:
        week = w.get("date", "")[:10]  # already a date string
        if week:
            # Get Monday of that week
            try:
                import datetime as _dt
                d = _dt.date.fromisoformat(week)
                monday = str(d - _dt.timedelta(days=d.weekday()))
            except (ValueError, AttributeError):
                monday = week
            if w.get("completed", False):
                workout_counts[monday] += 1

    # Count messages by week (both sides)
    message_counts: dict[str, int] = defaultdict(int)
    for msg in chat_messages + coach_messages:
        week = _iso_to_week(msg.get("ts", ""))
        if week:
            message_counts[week] += 1

    # Collect all known weeks and take last 4
    all_weeks = sorted(
        set(list(adherence_by_week.keys()) + list(workout_counts.keys()) + list(message_counts.keys()))
    )[-4:]

    return [
        WeeklyComparisonPoint(
            week_of=w,
            adherence_pct=adherence_by_week.get(w, 0),
            workouts_completed=workout_counts.get(w, 0),
            messages_sent=message_counts.get(w, 0),
        )
        for w in all_weeks
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/members",
    response_model=list[CoachMemberSummary],
    summary="List all coach members",
    description="Returns all seeded members (id, name, tier, age) for the member switcher.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Neo4j query error"},
    },
)
async def get_coach_members(
    user: User = Depends(current_active_user),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> list[CoachMemberSummary]:
    try:
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (m:Member)
                RETURN m.id AS id, m.display_name AS display_name, m.name AS name,
                       m.tier AS tier, m.age AS age
                ORDER BY m.display_name, m.name
                """
            )
            records = await result.data()
        return [
            CoachMemberSummary(
                member_id=r["id"] or "",
                member_name=r["display_name"] or r["name"] or "",
                tier=r["tier"],
                member_age=r["age"],
            )
            for r in records
            if r.get("id")
        ]
    except Exception as exc:
        logger.exception("Error in /coach/members")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
    member_id: str | None = None,
) -> CoachBriefResponse:
    try:
        t_ctx = time.monotonic()
        ctx = await _fetch_member_context(driver, user.email, member_id=member_id)
        retrieval_ms = int((time.monotonic() - t_ctx) * 1000)
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

        chat_messages = ctx.get("chat_messages", [])
        coach_messages = ctx.get("coach_messages", [])
        adherence = ctx.get("adherence", [])
        workouts = ctx.get("workouts", [])

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
                for a in adherence
            ],
            equipment=list(m.get("equipment_available", [])),
            message_pattern=_build_message_pattern(chat_messages, coach_messages),
            weekly_comparison=_build_weekly_comparison(
                adherence, workouts, chat_messages, coach_messages
            ),
            audit_log=_build_context_audit(ctx, retrieval_ms),
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
        t_ctx = time.monotonic()
        ctx = await _fetch_member_context(driver, user.email, member_id=request.member_id)
        retrieval_ms = int((time.monotonic() - t_ctx) * 1000)
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

    audit_log = _build_context_audit(ctx, retrieval_ms)

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

    audit_log.append(
        {
            "event": "coach_copilot_llm",
            "model": settings.coach_model,
            "provider": "anthropic",
            "latency_ms": latency_ms,
            "detail": "Grounded copilot answer from member context",
        }
    )

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
        audit_log=audit_log,
    )


@router.post(
    "/nudge",
    response_model=NudgeResponse,
    summary="Draft a nudge message for a flagged member",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"model": ErrorResponse, "description": "Invalid action item"},
        500: {"model": ErrorResponse, "description": "LLM error"},
    },
)
async def coach_nudge(
    body: NudgeRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> NudgeResponse:
    import json as _json

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=256)
        system = (
            "You are a fitness coach assistant. Write a warm, personal, 1-3 sentence check-in message "
            "to send to a member. Be specific about their situation — reference the reason you are reaching out. "
            "Do not use generic motivational phrases. Sign off as 'Your Coach'."
        )
        grounded_on = [body.action_item.reason]
        human = (
            f"Member: {body.member_name}\n"
            f"Reason for nudge: {body.action_item.reason}\n"
            f"Context: {body.action_item.context}\n\n"
            "Write the nudge message now."
        )
        response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        message_text = str(response.content)

        draft_id: str | None = None
        try:
            draft = CoachDraft(
                member_id=body.member_id,
                member_name=body.member_name,
                content_type=CoachDraftContentType.nudge,
                body=message_text,
                grounded_on=_json.dumps(grounded_on),
                status=CoachDraftStatus.draft,
                created_by=user.email,
            )
            db.add(draft)
            await db.commit()
            await db.refresh(draft)
            draft_id = str(draft.id)
        except Exception:
            await db.rollback()
            logger.exception("Error persisting nudge draft; continuing without draft_id")

        return NudgeResponse(
            draft_message=message_text,
            grounded_on=grounded_on,
            draft_id=draft_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in POST /coach/nudge")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class CreateDraftRequest(BaseModel):
    member_id: str
    member_name: str
    content_type: str  # "nudge" | "recommendation"
    body: str
    grounded_on: list[str] = []


@router.post(
    "/draft",
    response_model=CoachDraftSchema,
    summary="Save an AI-generated draft for coach review",
    status_code=201,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "DB error"},
    },
)
async def create_coach_draft(
    body: CreateDraftRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> CoachDraftSchema:
    import json
    try:
        draft = CoachDraft(
            member_id=body.member_id,
            member_name=body.member_name,
            content_type=CoachDraftContentType(body.content_type),
            body=body.body,
            grounded_on=json.dumps(body.grounded_on) if body.grounded_on else None,
            status=CoachDraftStatus.draft,
            created_by=user.email,
        )
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        return _draft_to_schema(draft)
    except Exception as exc:
        await db.rollback()
        logger.exception("Error creating coach draft")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class PatchDraftRequest(BaseModel):
    action: str  # "approve" | "edit" | "send"
    body: str | None = None  # required when action == "edit"


@router.patch(
    "/draft/{draft_id}",
    response_model=CoachDraftSchema,
    summary="Approve, edit, or send a coach draft",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
        409: {"model": ErrorResponse, "description": "Invalid status transition"},
        500: {"model": ErrorResponse, "description": "DB error"},
    },
)
async def patch_coach_draft(
    draft_id: str,
    body: PatchDraftRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> CoachDraftSchema:
    from datetime import UTC, datetime
    from sqlalchemy import select

    try:
        result = await db.execute(
            select(CoachDraft).where(CoachDraft.id == uuid.UUID(draft_id))
        )
        draft = result.scalar_one_or_none()
        if draft is None:
            raise HTTPException(status_code=404, detail="Draft not found")

        if body.action == "approve":
            if draft.status == CoachDraftStatus.sent:
                raise HTTPException(status_code=409, detail="Cannot approve a sent draft")
            draft.status = CoachDraftStatus.approved
            draft.approved_by = user.email
            draft.approved_at = datetime.now(UTC)

        elif body.action == "edit":
            if draft.status == CoachDraftStatus.sent:
                raise HTTPException(status_code=409, detail="Cannot edit a sent draft")
            if not body.body:
                raise HTTPException(status_code=422, detail="body is required for edit action")
            draft.body = body.body
            if draft.status == CoachDraftStatus.approved:
                draft.status = CoachDraftStatus.draft
                draft.approved_by = None
                draft.approved_at = None

        elif body.action == "send":
            if draft.status != CoachDraftStatus.approved:
                raise HTTPException(
                    status_code=409,
                    detail="Draft must be approved before it can be sent",
                )
            draft.status = CoachDraftStatus.sent
            draft.sent_at = datetime.now(UTC)

        else:
            raise HTTPException(status_code=422, detail=f"Unknown action: {body.action}")

        await db.commit()
        await db.refresh(draft)
        return _draft_to_schema(draft)

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Error patching coach draft")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/draft",
    response_model=list[CoachDraftSchema],
    summary="List all coach drafts for the current coach",
    responses={401: {"model": ErrorResponse, "description": "Not authenticated"}},
)
async def list_coach_drafts(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    status: str | None = None,
) -> list[CoachDraftSchema]:
    from sqlalchemy import select
    try:
        q = select(CoachDraft).order_by(CoachDraft.created_at.desc())
        if status:
            q = q.where(CoachDraft.status == CoachDraftStatus(status))
        result = await db.execute(q)
        return [_draft_to_schema(d) for d in result.scalars().all()]
    except Exception as exc:
        logger.exception("Error listing coach drafts")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
