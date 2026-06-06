"""Neo4j schema initialization script.

Creates all uniqueness constraints, lookup indexes, and the Exercise embedding
vector index. Safe to run multiple times — all DDL uses ``IF NOT EXISTS``.

Usage::

    python -m app.knowledge_graph.init_schema

Or programmatically::

    from neo4j import GraphDatabase
    from app.knowledge_graph.init_schema import init_neo4j_schema

    driver = GraphDatabase.driver(uri, auth=(user, password))
    init_neo4j_schema(driver)
    driver.close()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import neo4j

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Uniqueness constraints
# ---------------------------------------------------------------------------
CONSTRAINTS: list[str] = [
    """
    CREATE CONSTRAINT member_id IF NOT EXISTS
    FOR (m:Member) REQUIRE m.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT exercise_id IF NOT EXISTS
    FOR (e:Exercise) REQUIRE e.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT injury_id IF NOT EXISTS
    FOR (i:Injury) REQUIRE i.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT workout_session_id IF NOT EXISTS
    FOR (ws:WorkoutSession) REQUIRE ws.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT feedback_event_id IF NOT EXISTS
    FOR (f:FeedbackEvent) REQUIRE f.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT set_id IF NOT EXISTS
    FOR (s:Set) REQUIRE s.id IS UNIQUE
    """,
]

# ---------------------------------------------------------------------------
# Standard indexes
# ---------------------------------------------------------------------------
INDEXES: list[str] = [
    """
    CREATE INDEX exercise_name IF NOT EXISTS
    FOR (e:Exercise) ON (e.name)
    """,
    """
    CREATE INDEX member_email IF NOT EXISTS
    FOR (m:Member) ON (m.email)
    """,
    """
    CREATE INDEX feedback_event_created_at IF NOT EXISTS
    FOR (f:FeedbackEvent) ON (f.created_at)
    """,
    """
    CREATE INDEX workout_session_started_at IF NOT EXISTS
    FOR (ws:WorkoutSession) ON (ws.started_at)
    """,
]

# ---------------------------------------------------------------------------
# Vector indexes
# ---------------------------------------------------------------------------
VECTOR_INDEXES: list[str] = [
    """
    CREATE VECTOR INDEX exercise_embeddings IF NOT EXISTS
    FOR (e:Exercise) ON (e.description_embedding)
    OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}
    """,
]


def init_neo4j_schema(driver: "neo4j.Driver") -> None:
    """Create all constraints, indexes, and vector indexes in Neo4j.

    Idempotent — uses ``IF NOT EXISTS`` on every DDL statement so it is safe
    to call on every application startup or as a one-off CLI command.

    Args:
        driver: An open ``neo4j.Driver`` instance.
    """
    with driver.session() as session:
        for cypher in CONSTRAINTS:
            name = _extract_name(cypher, "CONSTRAINT")
            logger.info("Creating constraint: %s", name)
            session.run(cypher)

        for cypher in INDEXES:
            name = _extract_name(cypher, "INDEX")
            logger.info("Creating index: %s", name)
            session.run(cypher)

        for cypher in VECTOR_INDEXES:
            name = _extract_name(cypher, "INDEX")
            logger.info("Creating vector index: %s", name)
            session.run(cypher)

    logger.info("Neo4j schema initialization complete.")


def _extract_name(cypher: str, keyword: str) -> str:
    """Extract the constraint/index name from a Cypher DDL string."""
    tokens = cypher.split()
    try:
        idx = tokens.index(keyword)
        return tokens[idx + 1]
    except (ValueError, IndexError):
        return "<unknown>"


if __name__ == "__main__":
    import logging as _logging

    import neo4j as _neo4j

    from app.config import settings

    _logging.basicConfig(level=_logging.INFO, format="%(levelname)s %(message)s")

    _driver = _neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        init_neo4j_schema(_driver)
    finally:
        _driver.close()
