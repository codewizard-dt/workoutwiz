"""KG router: /kg/recommend, /kg/explain, /kg/feedback, /kg/audit."""
from __future__ import annotations

import logging
from typing import Any

import neo4j
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.kg.driver import get_neo4j_driver
from app.kg.explainability import explain_skipped_exercise
from app.knowledge_graph.traversal import get_contraindicated_provenance
from app.kg.feedback_service import write_feedback
from app.kg.generation_graph import RecommendedExercise, build_generation_graph
from app.kg.retrieval_graph import build_retrieval_graph
from app.models.audit_log import AuditLogEntry
from app.models.feedback import ExerciseFeedback
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.kg import FeedbackPayload, KGExplainRequest, KGRecommendRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kg", tags=["knowledge-graph"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class KGRecommendResponse(BaseModel):
    member_id: str
    exercises: list[RecommendedExercise]
    overall_reasoning: str
    skipped_exercise_ids: list[str]
    fallback_used: bool


class KGExplainResponse(BaseModel):
    exercise_id: str
    explanation: str
    confidence: float


class KGFeedbackResponse(BaseModel):
    feedback_id: str
    message: str


class KGFeedbackItem(BaseModel):
    exercise_id: str
    rating: int
    workout_set_id: str | None = None
    context_type: str


class KGFeedbackListResponse(BaseModel):
    workout_id: str
    items: list[KGFeedbackItem]


class KgAuditResponse(BaseModel):
    session_id: str
    audit_log: list[dict[str, Any]]
    total_entries: int


class ContraindicationItem(BaseModel):
    exercise_id: str
    reason: str
    confidence: float
    injuries: list[str]


class ContraindicationListResponse(BaseModel):
    member_id: str
    items: list[ContraindicationItem]


class FeedbackSummaryItem(BaseModel):
    exercise_id: str
    avg_rating: float
    count: int
    last_rated_at: str | None = None


class FeedbackSummaryResponse(BaseModel):
    items: list[FeedbackSummaryItem]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/recommend",
    response_model=KGRecommendResponse,
    summary="KG exercise recommendation",
    description=(
        "Run the full retrieval → generation pipeline for a member. "
        "Returns a personalised workout recommendation based on the member's "
        "injury history, preferences, and the supplied query."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal pipeline error"},
    },
)
async def kg_recommend(
    request: KGRecommendRequest,
    user: User = Depends(current_active_user),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> KGRecommendResponse:
    """Run retrieval + generation graphs and return workout recommendations."""
    member_id = request.member_id or str(user.id)

    try:
        # Step 1: retrieval graph → ContextSlice
        retrieval_graph = build_retrieval_graph(driver)
        retrieval_result = await retrieval_graph.ainvoke(
            {"member_id": member_id, "query": request.query}
        )
        context = retrieval_result.get("context")

        # Step 2: generation graph → WorkoutRecommendation
        generation_graph = build_generation_graph()
        gen_result = await generation_graph.ainvoke(
            {"member_id": member_id, "query": request.query, "context": context}
        )

        recommendation = gen_result.get("recommendation")
        if recommendation is None:
            raise HTTPException(status_code=500, detail="Generation graph returned no recommendation")

        fallback_used = bool(gen_result.get("fallback_triggered", False))

        return KGRecommendResponse(
            member_id=member_id,
            exercises=recommendation.exercises,
            overall_reasoning=recommendation.overall_reasoning,
            skipped_exercise_ids=recommendation.skipped_exercise_ids,
            fallback_used=fallback_used,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in /kg/recommend for member %s", member_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/explain",
    response_model=KGExplainResponse,
    summary="Explain skipped exercise",
    description=(
        "Return a human-readable explanation for why a specific exercise was "
        "excluded from a member's recommendations."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Neo4j query error"},
    },
)
async def kg_explain(
    request: KGExplainRequest,
    user: User = Depends(current_active_user),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> KGExplainResponse:
    """Explain why an exercise was skipped for a given member."""
    member_id = request.member_id or str(user.id)

    try:
        explanation, audit_entry, confidence = await explain_skipped_exercise(
            member_id=member_id,
            exercise_id=request.exercise_id,
            driver=driver,
        )
        logger.debug("kg_explain audit: %s", audit_entry)
        return KGExplainResponse(
            exercise_id=request.exercise_id,
            explanation=explanation,
            confidence=confidence,
        )
    except Exception as exc:
        logger.exception(
            "Error in /kg/explain for member %s, exercise %s",
            member_id,
            request.exercise_id,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/feedback",
    response_model=KGFeedbackResponse,
    summary="Submit workout feedback",
    description="Write post-workout exercise feedback to the knowledge graph.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Neo4j write error"},
    },
)
async def kg_feedback(
    payload: FeedbackPayload,
    user: User = Depends(current_active_user),
    pg_session: AsyncSession = Depends(get_async_session),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> KGFeedbackResponse:
    """Persist feedback event to Neo4j + PostgreSQL and return the created feedback_id."""
    try:
        feedback_id = await write_feedback(
            payload=payload,
            driver=driver,
            pg_session=pg_session,
        )
        return KGFeedbackResponse(
            feedback_id=feedback_id,
            message="Feedback recorded successfully",
        )
    except Exception as exc:
        logger.exception(
            "Error in /kg/feedback for member %s, exercise %s",
            payload.member_id,
            payload.exercise_id,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/feedback",
    response_model=KGFeedbackListResponse,
    summary="List a member's saved feedback for a workout",
    description=(
        "Return the current member's most recent rating for each workout set in "
        "the given workout, so the UI can restore previously submitted ratings."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def list_kg_feedback(
    workout_id: str = Query(..., description="Workout whose saved feedback should be returned"),
    user: User = Depends(current_active_user),
    pg_session: AsyncSession = Depends(get_async_session),
) -> KGFeedbackListResponse:
    """Return the latest rating per workout set for the current member + workout."""
    stmt = (
        select(ExerciseFeedback)
        .where(
            ExerciseFeedback.user_id == user.id,
            ExerciseFeedback.workout_id == workout_id,
        )
        .order_by(ExerciseFeedback.created_at)
    )
    result = await pg_session.execute(stmt)
    rows = result.scalars().all()

    # Rows are ordered oldest → newest, so the last write per set wins.
    latest: dict[str, KGFeedbackItem] = {}
    for row in rows:
        key = str(row.workout_set_id) if row.workout_set_id is not None else str(row.exercise_id)
        latest[key] = KGFeedbackItem(
            exercise_id=str(row.exercise_id),
            rating=row.rating,
            workout_set_id=str(row.workout_set_id) if row.workout_set_id is not None else None,
            context_type=row.context_type.value,
        )

    return KGFeedbackListResponse(workout_id=workout_id, items=list(latest.values()))


@router.get(
    "/audit/{session_id}",
    response_model=KgAuditResponse,
    summary="Get KG session audit log",
    description=(
        "Retrieve knowledge graph-specific audit log entries for a session. "
        "Returns ordered KG layer events (kg_*, retrieval_*) excluding chat routing events."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found or no KG audit entries exist"},
    },
)
async def get_kg_audit(
    session_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> KgAuditResponse:
    """Retrieve KG-specific audit log entries for a session.
    
    Filters audit entries to only include those with event starting with 'kg_'
    or 'retrieval_', excluding chat router entries and other non-KG events.
    """
    # Query audit_log table for this session with KG-specific events
    stmt = select(AuditLogEntry).where(
        AuditLogEntry.session_id == session_id
    ).order_by(AuditLogEntry.created_at)
    
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    # Filter to only KG-related events
    kg_entries = [
        e for e in entries
        if e.event.startswith(("kg_", "retrieval_"))
    ]
    
    # Convert to dict format for response
    audit_log = []
    for entry in kg_entries:
        entry_dict: dict[str, Any] = {
            "event": entry.event,
            "session_id": entry.session_id,
        }
        # Add known fields if they exist
        if entry.model:
            entry_dict["model"] = entry.model
        if entry.provider:
            entry_dict["provider"] = entry.provider
        if entry.latency_ms is not None:
            entry_dict["latency_ms"] = entry.latency_ms
        if entry.tokens_in is not None:
            entry_dict["tokens_in"] = entry.tokens_in
        if entry.tokens_out is not None:
            entry_dict["tokens_out"] = entry.tokens_out
        if entry.node_name:
            entry_dict["node_name"] = entry.node_name
        if entry.source_type:
            entry_dict["source_type"] = entry.source_type
        if entry.source_id:
            entry_dict["source_id"] = entry.source_id
        if entry.extra:
            entry_dict.update(entry.extra)
        entry_dict["created_at"] = entry.created_at.isoformat()
        audit_log.append(entry_dict)
    
    if not kg_entries and not entries:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    
    return KgAuditResponse(
        session_id=session_id,
        audit_log=audit_log,
        total_entries=len(audit_log),
    )



async def _resolve_member_id(
    driver: neo4j.AsyncDriver, member_id: str | None, email: str
) -> str | None:
    """Resolve a graph Member id from an explicit id or the caller's email."""
    if member_id:
        return member_id
    async with driver.session() as session:
        result = await session.run(
            "MATCH (m:Member {email: $email}) RETURN m.id AS id", email=email
        )
        record = await result.single()
    return record["id"] if record else None


@router.get(
    "/contraindications",
    response_model=ContraindicationListResponse,
    summary="List contraindicated exercises for a member",
    description=(
        "Return every exercise that is contraindicated for the member, each with a "
        "graph-grounded reason (loaded joints + offending injuries) and a confidence "
        "score. One round-trip for the whole catalog, powering the 'Safe for me' lens."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Neo4j query error"},
    },
)
async def kg_contraindications(
    member_id: str | None = Query(
        None, description="Member to evaluate; defaults to the authenticated user"
    ),
    user: User = Depends(current_active_user),
    driver: neo4j.AsyncDriver = Depends(get_neo4j_driver),
) -> ContraindicationListResponse:
    """Aggregate SNOMED-grounded provenance into per-exercise contraindications."""
    try:
        resolved = await _resolve_member_id(driver, member_id, user.email)
        if not resolved:
            return ContraindicationListResponse(member_id="", items=[])

        records = await get_contraindicated_provenance(resolved, driver)

        by_exercise: dict[str, dict[str, set[str]]] = {}
        for record in records:
            exercise_id = record.get("exercise_id")
            if not exercise_id:
                continue
            entry = by_exercise.setdefault(
                exercise_id, {"injuries": set(), "joints": set()}
            )
            if record.get("injury_name"):
                entry["injuries"].add(record["injury_name"])
            if record.get("matched_joint"):
                entry["joints"].add(record["matched_joint"])

        items: list[ContraindicationItem] = []
        for exercise_id, entry in by_exercise.items():
            injuries = sorted(entry["injuries"])
            joints = sorted(entry["joints"])
            joint_part = f"loads {', '.join(joints)}; " if joints else ""
            injury_part = (
                f"contraindicated for {', '.join(injuries)}"
                if injuries
                else "contraindicated"
            )
            reason = f"{joint_part}{injury_part}".capitalize()
            # Mirror explain_skipped_exercise scoring: 2-hop depth (0.5) + injury coverage.
            coverage = min(max(len(injuries), 1), 4) / 4 * 0.5
            confidence = min(1.0, 0.5 + coverage)
            items.append(
                ContraindicationItem(
                    exercise_id=exercise_id,
                    reason=reason,
                    confidence=round(confidence, 3),
                    injuries=injuries,
                )
            )

        return ContraindicationListResponse(member_id=resolved, items=items)
    except Exception as exc:
        logger.exception("Error in /kg/contraindications for member %s", member_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/feedback/summary",
    response_model=FeedbackSummaryResponse,
    summary="Per-exercise feedback summary for the current member",
    description=(
        "Return the authenticated member's aggregated rating per exercise "
        "(average rating, number of ratings, and most recent rating timestamp) "
        "across all workouts, for surfacing 'you rated this' signals."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def kg_feedback_summary(
    user: User = Depends(current_active_user),
    pg_session: AsyncSession = Depends(get_async_session),
) -> FeedbackSummaryResponse:
    """Aggregate exercise_feedback rows for the current user, grouped by exercise."""
    stmt = (
        select(
            ExerciseFeedback.exercise_id,
            func.avg(ExerciseFeedback.rating),
            func.count(ExerciseFeedback.id),
            func.max(ExerciseFeedback.created_at),
        )
        .where(ExerciseFeedback.user_id == user.id)
        .group_by(ExerciseFeedback.exercise_id)
    )
    rows = (await pg_session.execute(stmt)).all()
    items = [
        FeedbackSummaryItem(
            exercise_id=str(exercise_id),
            avg_rating=round(float(avg_rating), 2),
            count=int(count),
            last_rated_at=last_rated.isoformat() if last_rated else None,
        )
        for exercise_id, avg_rating, count, last_rated in rows
    ]
    return FeedbackSummaryResponse(items=items)
