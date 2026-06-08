"""KG router: /kg/recommend, /kg/explain, /kg/feedback, /kg/audit."""
from __future__ import annotations

import logging
from typing import Any

import neo4j
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.kg.driver import get_neo4j_driver
from app.kg.explainability import explain_skipped_exercise
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
