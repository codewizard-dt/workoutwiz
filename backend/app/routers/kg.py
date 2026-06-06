"""KG router: /kg/recommend, /kg/explain, /kg/feedback."""
from __future__ import annotations

import logging

import neo4j
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import current_active_user
from app.config import settings
from app.kg.explainability import explain_skipped_exercise
from app.kg.feedback_service import write_feedback
from app.kg.generation_graph import RecommendedExercise, build_generation_graph
from app.kg.retrieval_graph import build_retrieval_graph
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


class KGFeedbackResponse(BaseModel):
    feedback_id: str
    message: str


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
) -> KGRecommendResponse:
    """Run retrieval + generation graphs and return workout recommendations."""
    member_id = request.member_id or str(user.id)

    driver = neo4j.AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
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
    finally:
        await driver.close()


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
) -> KGExplainResponse:
    """Explain why an exercise was skipped for a given member."""
    member_id = request.member_id or str(user.id)

    driver = neo4j.AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        explanation = await explain_skipped_exercise(
            member_id=member_id,
            exercise_id=request.exercise_id,
            driver=driver,
        )
        return KGExplainResponse(exercise_id=request.exercise_id, explanation=explanation)
    except Exception as exc:
        logger.exception(
            "Error in /kg/explain for member %s, exercise %s",
            member_id,
            request.exercise_id,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await driver.close()


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
) -> KGFeedbackResponse:
    """Persist feedback event to Neo4j and return the created feedback_id."""
    driver = neo4j.AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        feedback_id = await write_feedback(payload=payload, driver=driver)
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
    finally:
        await driver.close()
