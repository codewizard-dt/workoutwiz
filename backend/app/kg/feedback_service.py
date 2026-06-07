"""Feedback write-back service — wraps Neo4j FeedbackEvent ingestion."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, UTC

from neo4j import AsyncDriver
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge_graph.ingest_feedback import (
    _EDGE_EXERCISE_ABOUT,
    _EDGE_MEMBER_RATED,
    _EDGE_SET_ABOUT,
    _EDGE_WORKOUT_ABOUT,
    _MERGE_FEEDBACK_EVENT,
    _run_write_tx,
)
from app.models.feedback import ExerciseFeedback, FeedbackContextType
from app.schemas.kg import FeedbackPayload

logger = logging.getLogger(__name__)


async def write_feedback(
    payload: FeedbackPayload,
    driver: AsyncDriver,
    pg_session: AsyncSession,
) -> str:
    """Persist a single feedback event to Neo4j and PostgreSQL.

    Branches on ``payload.context_type`` to create the appropriate graph edges:
      - exercise / default: FeedbackEvent -[:ABOUT]-> Exercise + Member -[:RATED]-> Exercise
      - workout:            FeedbackEvent -[:ABOUT]-> WorkoutSession
      - set:                FeedbackEvent -[:ABOUT]-> Set
                            + FeedbackEvent -[:ABOUT]-> Exercise + Member -[:RATED]-> Exercise

    Also inserts an ``ExerciseFeedback`` row in PostgreSQL whenever ``exercise_id``
    is present (required for the NOT NULL FK constraint).

    Args:
        payload:    Validated feedback data from the API layer.
        driver:     Open ``neo4j.AsyncDriver`` instance.
        pg_session: SQLAlchemy async session for PostgreSQL persistence.

    Returns:
        The ``id`` of the created ``FeedbackEvent`` node.
    """
    feedback_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()

    # Normalise context_type — default to EXERCISE for unknown values
    try:
        ctx = FeedbackContextType(payload.context_type)
    except ValueError:
        ctx = FeedbackContextType.EXERCISE

    async with driver.session() as neo4j_session:

        async def _write(tx: object) -> None:
            # Step A: MERGE FeedbackEvent node
            await _run_write_tx(
                tx,
                _MERGE_FEEDBACK_EVENT,
                {
                    "id": feedback_id,
                    "rating": payload.rating,
                    "feedback_text": payload.text,
                    "context_type": ctx.value,
                    "created_at": created_at,
                },
            )

            if ctx == FeedbackContextType.WORKOUT:
                # Step B: ABOUT->WorkoutSession edge
                await _run_write_tx(
                    tx,
                    _EDGE_WORKOUT_ABOUT,
                    {"feedback_id": feedback_id, "workout_id": payload.workout_id},
                )
            elif ctx == FeedbackContextType.SET:
                # Step B: ABOUT->Set edge
                await _run_write_tx(
                    tx,
                    _EDGE_SET_ABOUT,
                    {"feedback_id": feedback_id, "workout_set_id": payload.workout_set_id},
                )
                # Step C: ABOUT->Exercise + RATED edges (when exercise_id present)
                if payload.exercise_id:
                    await _run_write_tx(
                        tx,
                        _EDGE_EXERCISE_ABOUT,
                        {"feedback_id": feedback_id, "exercise_id": payload.exercise_id},
                    )
                    await _run_write_tx(
                        tx,
                        _EDGE_MEMBER_RATED,
                        {
                            "member_id": payload.member_id,
                            "exercise_id": payload.exercise_id,
                            "rating": payload.rating,
                            "feedback_text": payload.text,
                            "created_at": created_at,
                        },
                    )
            else:
                # EXERCISE context (default)
                if payload.exercise_id:
                    await _run_write_tx(
                        tx,
                        _EDGE_EXERCISE_ABOUT,
                        {"feedback_id": feedback_id, "exercise_id": payload.exercise_id},
                    )
                    await _run_write_tx(
                        tx,
                        _EDGE_MEMBER_RATED,
                        {
                            "member_id": payload.member_id,
                            "exercise_id": payload.exercise_id,
                            "rating": payload.rating,
                            "feedback_text": payload.text,
                            "created_at": created_at,
                        },
                    )

        await neo4j_session.execute_write(_write)

    # ------------------------------------------------------------------
    # PostgreSQL persistence
    # Only insert when exercise_id is present (NOT NULL FK constraint).
    # Workout-only context (no exercise_id) is skipped with a warning.
    # ------------------------------------------------------------------
    if payload.exercise_id:
        try:
            pg_row = ExerciseFeedback(
                user_id=uuid.UUID(payload.member_id),
                exercise_id=uuid.UUID(payload.exercise_id),
                workout_id=uuid.UUID(payload.workout_id) if payload.workout_id else None,
                workout_set_id=uuid.UUID(payload.workout_set_id) if payload.workout_set_id else None,
                context_type=ctx,
                rating=payload.rating,
                feedback_text=payload.text,
            )
            pg_session.add(pg_row)
            await pg_session.commit()
            logger.info(
                "ExerciseFeedback PG row committed: member=%s exercise=%s context=%s",
                payload.member_id,
                payload.exercise_id,
                ctx.value,
            )
        except IntegrityError:
            await pg_session.rollback()
            logger.warning(
                "ExerciseFeedback PG insert skipped (IntegrityError — duplicate or constraint): "
                "member=%s exercise=%s",
                payload.member_id,
                payload.exercise_id,
            )
    else:
        logger.warning(
            "Skipping PostgreSQL ExerciseFeedback insert — exercise_id is None "
            "(context=%s member=%s workout=%s set=%s)",
            ctx.value,
            payload.member_id,
            payload.workout_id,
            payload.workout_set_id,
        )

    logger.info(
        "Feedback %s written: member=%s context=%s exercise=%s workout=%s set=%s",
        feedback_id,
        payload.member_id,
        ctx.value,
        payload.exercise_id,
        payload.workout_id,
        payload.workout_set_id,
    )
    return feedback_id
