"""Feedback ingestion: load ExerciseFeedback rows from PostgreSQL into Neo4j.

Creates ``FeedbackEvent`` nodes and edges to ``Exercise``, ``WorkoutSession``,
and ``Set`` nodes. Also writes the denormalized ``(Member)-[:RATED]->(Exercise)``
relationship used for fast preference traversal.

All Cypher uses MERGE / ON CREATE SET / ON MATCH SET so the script is idempotent.

Usage::

    python -m app.knowledge_graph.ingest_feedback
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.models.feedback import ExerciseFeedback, FeedbackContextType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cypher helpers
# ---------------------------------------------------------------------------

_MERGE_FEEDBACK_EVENT = """
MERGE (f:FeedbackEvent {id: $id})
ON CREATE SET
  f.rating = $rating,
  f.feedback_text = $feedback_text,
  f.context_type = $context_type,
  f.created_at = $created_at
ON MATCH SET
  f.rating = $rating,
  f.feedback_text = $feedback_text
"""

_EDGE_EXERCISE_ABOUT = """
MATCH (f:FeedbackEvent {id: $feedback_id})
MATCH (e:Exercise {id: $exercise_id})
MERGE (f)-[:ABOUT]->(e)
"""

_EDGE_MEMBER_RATED = """
MATCH (m:Member {id: $member_id})
MATCH (e:Exercise {id: $exercise_id})
MERGE (m)-[r:RATED]->(e)
ON CREATE SET r.rating = $rating, r.feedback_text = $feedback_text, r.created_at = $created_at
ON MATCH SET r.rating = $rating, r.feedback_text = $feedback_text, r.created_at = $created_at
"""

_EDGE_WORKOUT_ABOUT = """
MATCH (f:FeedbackEvent {id: $feedback_id})
MATCH (ws:WorkoutSession {id: $workout_id})
MERGE (f)-[:ABOUT]->(ws)
"""

_EDGE_SET_ABOUT = """
MERGE (s:Set {id: $workout_set_id})
WITH s
MATCH (f:FeedbackEvent {id: $feedback_id})
MERGE (f)-[:ABOUT]->(s)
"""


# ---------------------------------------------------------------------------
# Transaction helper
# ---------------------------------------------------------------------------


async def _run_write_tx(tx: object, cypher: str, params: dict[str, object]) -> None:
    """Execute a single Cypher statement inside an existing write transaction."""
    # tx is neo4j.AsyncManagedTransaction — typed as object to avoid import cycle
    await tx.run(cypher, **params)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Core ingestion functions
# ---------------------------------------------------------------------------


async def _upsert_feedback_batch(
    neo4j_session: object,
    rows: list[ExerciseFeedback],
) -> None:
    """Upsert a batch of ExerciseFeedback rows into Neo4j.

    Each row is written inside a single write transaction that MERGEs the
    ``FeedbackEvent`` node and then creates the appropriate context edge.
    """
    for row in rows:
        feedback_id = str(row.id)
        exercise_id = str(row.exercise_id)
        user_id = str(row.user_id)
        created_at_str: str | None = (
            row.created_at.isoformat() if row.created_at else None
        )

        async def _write(  # noqa: E501
            tx: object,
            _row: ExerciseFeedback = row,
            _feedback_id: str = feedback_id,
            _exercise_id: str = exercise_id,
            _user_id: str = user_id,
            _created_at_str: str | None = created_at_str,
        ) -> None:
            # Step A: MERGE FeedbackEvent node
            await _run_write_tx(tx, _MERGE_FEEDBACK_EVENT, {
                "id": _feedback_id,
                "rating": _row.rating,
                "feedback_text": _row.feedback_text,
                "context_type": str(_row.context_type),
                "created_at": _created_at_str,
            })

            # Step B: context-specific edge
            if _row.context_type == FeedbackContextType.EXERCISE:
                await _run_write_tx(tx, _EDGE_EXERCISE_ABOUT, {
                    "feedback_id": _feedback_id,
                    "exercise_id": _exercise_id,
                })
                await _run_write_tx(tx, _EDGE_MEMBER_RATED, {
                    "member_id": _user_id,
                    "exercise_id": _exercise_id,
                    "rating": _row.rating,
                    "feedback_text": _row.feedback_text,
                    "created_at": _created_at_str,
                })

            elif _row.context_type == FeedbackContextType.WORKOUT:
                workout_id: str | None = (
                    str(_row.workout_id) if _row.workout_id else None
                )
                await _run_write_tx(tx, _EDGE_WORKOUT_ABOUT, {
                    "feedback_id": _feedback_id,
                    "workout_id": workout_id,
                })

            elif _row.context_type == FeedbackContextType.SET:
                workout_set_id: str | None = (
                    str(_row.workout_set_id) if _row.workout_set_id else None
                )
                await _run_write_tx(tx, _EDGE_SET_ABOUT, {
                    "feedback_id": _feedback_id,
                    "workout_set_id": workout_set_id,
                })

        await neo4j_session.execute_write(_write)  # type: ignore[attr-defined]


async def ingest_all_feedback(
    pg_session: AsyncSession,
    neo4j_driver: object,
) -> int:
    """Load all ExerciseFeedback rows from PostgreSQL and upsert into Neo4j.

    Args:
        pg_session: An open SQLAlchemy async session connected to PostgreSQL.
        neo4j_driver: An open ``neo4j.AsyncDriver`` instance.

    Returns:
        Total number of FeedbackEvent nodes processed.
    """
    result = await pg_session.execute(select(ExerciseFeedback))
    rows: list[ExerciseFeedback] = list(result.scalars().all())

    async with neo4j_driver.session() as neo4j_session:  # type: ignore[attr-defined]
        await _upsert_feedback_batch(neo4j_session, rows)

    logger.info("Ingested %d FeedbackEvent nodes into Neo4j.", len(rows))
    return len(rows)


# ---------------------------------------------------------------------------
# __main__ entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from neo4j import AsyncGraphDatabase

    async def _main() -> None:
        engine = create_async_engine(settings.database_url)
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with AsyncSession(engine) as pg_session:
            count = await ingest_all_feedback(pg_session, driver)
            print(f"Ingested {count} FeedbackEvent nodes")
        await driver.close()

    asyncio.run(_main())
