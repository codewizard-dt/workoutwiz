"""Member ingestion module for the knowledge graph.

Reads the 15 fixed synthetic personas defined in ``seed.py`` and MERGEs each
as a ``Member`` node in Neo4j with all schema-required properties.

Usage::

    python -m app.knowledge_graph.ingest_members
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, cast

import neo4j

from app.knowledge_graph.seed import PERSONAS  # source of truth for synthetic profiles

logger = logging.getLogger(__name__)


def ingest_members(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
) -> None:
    """MERGE Member nodes in Neo4j for each persona.

    Args:
        driver: Connected Neo4j driver instance.
        member_map: Mapping of {email: postgres_uuid} — determines the Member.id
                    stored in Neo4j, ensuring cross-store consistency.
    """
    with driver.session() as session:
        for _persona in PERSONAS:
            persona: dict[str, Any] = cast("dict[str, Any]", _persona)
            email = str(persona["email"])
            member_id = str(member_map[email])
            name = str(persona["name"])
            goals: list[str] = list(persona["goals"])
            equipment: list[str] = list(persona["equipment"])
            sessions_per_week: int = int(persona["sessions_per_week"])
            session.run(
                """
                MERGE (m:Member {id: $id})
                SET m += {
                    email:               $email,
                    name:                $name,
                    goals:               $goals,
                    equipment_available: $equipment,
                    sessions_per_week:   $sessions_per_week,
                    created_at:          $created_at
                }
                """,
                id=member_id,
                email=email,
                name=name,
                goals=goals,
                equipment=equipment,
                sessions_per_week=sessions_per_week,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.info("Merged Member: %s (%s)", name, email)

    logger.info("Ingested %d Member nodes into Neo4j.", len(PERSONAS))


if __name__ == "__main__":
    import logging as _logging

    import sqlalchemy
    import sqlalchemy.orm

    from app.config import settings
    from app.knowledge_graph.seed import seed_postgres_users  # reuse existing pg upsert

    _logging.basicConfig(level=_logging.INFO, format="%(levelname)s %(message)s")

    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = sqlalchemy.create_engine(sync_url)
    with sqlalchemy.orm.Session(engine) as pg_session:
        member_map = seed_postgres_users(pg_session)
        pg_session.commit()

    neo4j_driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        ingest_members(neo4j_driver, member_map)
    finally:
        neo4j_driver.close()
