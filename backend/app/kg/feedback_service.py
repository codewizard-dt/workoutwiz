"""Feedback write-back service — wraps Neo4j FeedbackEvent ingestion."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from neo4j import AsyncDriver

from app.knowledge_graph.ingest_feedback import (
    _EDGE_EXERCISE_ABOUT,
    _EDGE_MEMBER_RATED,
    _MERGE_FEEDBACK_EVENT,
    _run_write_tx,
)
from app.schemas.kg import FeedbackPayload

logger = logging.getLogger(__name__)


async def write_feedback(payload: FeedbackPayload, driver: AsyncDriver) -> str:
    """Persist a single feedback event to Neo4j.

    Reuses the Cypher queries from ``ingest_feedback`` to avoid duplicating
    graph write logic. Creates a ``FeedbackEvent`` node plus the
    ``ABOUT->Exercise`` and ``RATED`` edges (post-workout exercise context).

    Args:
        payload: Validated feedback data from the API layer.
        driver:  Open ``neo4j.AsyncDriver`` instance.

    Returns:
        The ``id`` of the created ``FeedbackEvent`` node.
    """
    feedback_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    async with driver.session() as neo4j_session:  # type: ignore[attr-defined]

        async def _write(tx: object) -> None:
            # Step A: MERGE FeedbackEvent node
            await _run_write_tx(
                tx,
                _MERGE_FEEDBACK_EVENT,
                {
                    "id": feedback_id,
                    "rating": payload.rating,
                    "feedback_text": payload.text,
                    "context_type": payload.context_type,
                    "created_at": created_at,
                },
            )

            # Step B: ABOUT->Exercise edge
            await _run_write_tx(
                tx,
                _EDGE_EXERCISE_ABOUT,
                {
                    "feedback_id": feedback_id,
                    "exercise_id": payload.exercise_id,
                },
            )

            # Step C: (Member)-[:RATED]->(Exercise) denormalized edge
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

    logger.info(
        "Feedback %s written for member %s, exercise %s",
        feedback_id,
        payload.member_id,
        payload.exercise_id,
    )
    return feedback_id
