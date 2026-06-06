"""Idempotent ingestion of workout session history into Neo4j."""
import logging
from typing import Any

import neo4j

from app.config import settings

logger = logging.getLogger(__name__)


def _merge_session(tx: Any, session: dict[str, Any]) -> None:
    """Write a single WorkoutSession node plus its edges within one transaction."""
    session_id = session["id"]
    member_id = session["member_id"]

    logger.debug("Processing session %s for member %s", session_id, member_id)

    # Upsert the WorkoutSession node
    tx.run(
        """
        MERGE (ws:WorkoutSession {id: $id})
        SET ws += {started_at: $started_at, ended_at: $ended_at}
        """,
        id=session_id,
        started_at=session["started_at"],
        ended_at=session.get("ended_at"),
    )

    # PERFORMED edge: Member → WorkoutSession
    tx.run(
        """
        MATCH (m:Member {id: $member_id})
        MATCH (ws:WorkoutSession {id: $session_id})
        MERGE (m)-[:PERFORMED]->(ws)
        """,
        member_id=member_id,
        session_id=session_id,
    )

    # INCLUDED edges: WorkoutSession → Exercise (with performance properties)
    for exercise in session.get("exercises", []):
        tx.run(
            """
            MATCH (ws:WorkoutSession {id: $session_id})
            MATCH (e:Exercise {id: $exercise_id})
            MERGE (ws)-[r:INCLUDED]->(e)
            SET r += {sets: $sets, reps: $reps, weight_kg: $weight_kg, duration_s: $duration_s}
            """,
            session_id=session_id,
            exercise_id=exercise["exercise_id"],
            sets=exercise.get("sets"),
            reps=exercise.get("reps"),
            weight_kg=exercise.get("weight_kg"),
            duration_s=exercise.get("duration_s"),
        )


def ingest_workout_history(
    driver: neo4j.Driver,
    sessions: list[dict[str, Any]],
) -> int:
    """Ingest a list of workout session dicts into Neo4j.

    Each session dict must have the shape::

        {
            "id": str,
            "member_id": str,
            "started_at": str,   # ISO-8601
            "ended_at": str | None,
            "exercises": [
                {
                    "exercise_id": str,
                    "sets": int,
                    "reps": list[int] | None,
                    "weight_kg": float | None,
                    "duration_s": list[int] | None,
                },
                ...
            ],
        }

    Returns the number of sessions processed.
    Raises ValueError if *sessions* is empty.
    """
    if not sessions:
        raise ValueError("sessions list must not be empty")

    for session in sessions:
        with driver.session() as neo_session:
            neo_session.execute_write(_merge_session, session)

    count = len(sessions)
    logger.info("Ingested %d workout sessions into Neo4j.", count)
    return count


if __name__ == "__main__":
    import uuid
    from datetime import datetime, timezone

    logging.basicConfig(level=logging.INFO)

    _smoke_session: dict[str, object] = {
        "id": str(uuid.uuid4()),
        "member_id": str(uuid.uuid4()),
        "started_at": datetime.now(tz=timezone.utc).isoformat(),
        "ended_at": None,
        "exercises": [],
    }

    _driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        ingest_workout_history(_driver, [_smoke_session])
    finally:
        _driver.close()
