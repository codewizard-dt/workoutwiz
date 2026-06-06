"""Seed loader: orchestrates the full Neo4j (and PostgreSQL user) seed pipeline.

Run with::

    cd backend
    python -m app.knowledge_graph.seed_loader

Each ingestor is idempotent (MERGE-only), so running this multiple times is safe.
"""

from __future__ import annotations

import logging
import sys
import uuid

import neo4j
import sqlalchemy
import sqlalchemy.orm

from app.config import settings
from app.knowledge_graph.init_schema import init_neo4j_schema
from app.knowledge_graph.ingest_exercises import ingest_exercises
from app.knowledge_graph.ingest_members import ingest_members
from app.knowledge_graph.ingest_injuries import build_injury_records, ingest_injuries
from app.knowledge_graph.seed import seed_postgres_users

logger = logging.getLogger(__name__)


def run_seed(driver: neo4j.Driver, member_map: dict[str, uuid.UUID]) -> None:
    """Execute the full Neo4j seed pipeline.

    Args:
        driver:     An active Neo4j driver instance.
        member_map: Mapping of {email: postgres_uuid} built from PostgreSQL users.
                    Pass the return value of ``seed_postgres_users(pg_session)``.

    Calling this function multiple times is idempotent — all writes use MERGE.
    """
    logger.info("Initialising Neo4j schema constraints and indexes …")
    init_neo4j_schema(driver)

    logger.info("Ingesting Exercise nodes …")
    ingest_exercises(driver)

    logger.info("Ingesting Member nodes …")
    ingest_members(driver, member_map)

    logger.info("Ingesting Injury nodes and edges …")
    injury_records = build_injury_records(member_map)
    ingest_injuries(driver, injury_records)

    logger.info("Seed pipeline complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )

    # 1. Seed PostgreSQL users and obtain member_map
    _sync_url = settings.database_url.replace("+asyncpg", "")
    _engine = sqlalchemy.create_engine(_sync_url)
    with sqlalchemy.orm.Session(_engine) as _pg_session:
        _member_map = seed_postgres_users(_pg_session)
        _pg_session.commit()

    # 2. Run Neo4j seed pipeline
    with neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    ) as _driver:
        run_seed(_driver, _member_map)

    print("Seed loader complete.")
