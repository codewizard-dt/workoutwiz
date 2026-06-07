"""Injury ingestor: MERGE Injury nodes, HAS_INJURY edges, and CONTRAINDICATED_BY edges.

Public API
----------
ingest_injuries(driver, records) -> None

Each record in ``records`` must have the shape::

    {
        "id": "<uuid str>",
        "member_id": "<uuid str matching a Member node>",
        "name": "Knee Tendinopathy",
        "affected_joints": ["knee"],
        "severity": "moderate",       # mild | moderate | severe
        "onset_date": "2024-03-15",   # ISO date string or None
        "status": "active",           # active | resolved
    }

Only active injuries produce CONTRAINDICATED_BY edges.

The module is also runnable standalone::

    python -m app.knowledge_graph.ingest_injuries
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import neo4j
import neo4j.exceptions

from app.knowledge_graph.seed import PERSONAS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private transaction helpers
# ---------------------------------------------------------------------------


def _merge_injury_node(tx: neo4j.ManagedTransaction, record: dict[str, Any]) -> None:
    """MERGE an Injury node and set its properties (idempotent)."""
    tx.run(
        """
        MERGE (i:Injury {id: $id})
        SET i.name           = $name,
            i.affected_joints = $affected_joints,
            i.severity        = $severity,
            i.onset_date      = $onset_date,
            i.status          = $status,
            i.region          = $region,
            i.notes           = $notes,
            i.snomedct_hint   = $snomedct_hint
        """,
        id=record["id"],
        name=record["name"],
        affected_joints=record["affected_joints"],
        severity=record["severity"],
        onset_date=record.get("onset_date"),
        status=record["status"],
        region=record.get("region"),
        notes=record.get("notes"),
        snomedct_hint=record.get("snomedct_hint"),
    )


def _merge_has_injury_edge(
    tx: neo4j.ManagedTransaction, member_id: str, injury_id: str
) -> None:
    """MERGE a (Member)-[:HAS_INJURY]->(Injury) edge (idempotent)."""
    tx.run(
        """
        MATCH (m:Member {id: $member_id})
        MATCH (i:Injury {id: $injury_id})
        MERGE (m)-[:HAS_INJURY]->(i)
        """,
        member_id=member_id,
        injury_id=injury_id,
    )


def _merge_contraindicated_by_edges(
    tx: neo4j.ManagedTransaction, injury_id: str, affected_joints: list[str]
) -> int:
    """MERGE (Exercise)-[:CONTRAINDICATED_BY]->(Injury) for all joint-overlapping exercises.

    Returns the count of exercises matched (not necessarily newly created edges).
    """
    result = tx.run(
        """
        MATCH (e:Exercise)
        WHERE ANY(j IN e.joints_loaded WHERE j IN $affected_joints)
        MATCH (i:Injury {id: $injury_id})
        MERGE (e)-[:CONTRAINDICATED_BY]->(i)
        RETURN count(e) AS cnt
        """,
        injury_id=injury_id,
        affected_joints=affected_joints,
    )
    record = result.single()
    return record["cnt"] if record else 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ingest_injuries(driver: neo4j.Driver, records: list[dict[str, Any]]) -> None:
    """MERGE Injury nodes and their edges for each record.

    Args:
        driver:  An active Neo4j driver instance.
        records: List of injury dicts (see module docstring for shape).
    """
    for record in records:
        injury_id = record["id"]
        member_id = record["member_id"]
        affected_joints = record.get("affected_joints") or []

        try:
            with driver.session() as session:
                session.execute_write(_merge_injury_node, record)
                session.execute_write(_merge_has_injury_edge, member_id, injury_id)

                contraindication_count = 0
                if record.get("status") == "active" and affected_joints:
                    contraindication_count = session.execute_write(
                        _merge_contraindicated_by_edges, injury_id, affected_joints
                    )

                logger.info(
                    "Merged Injury '%s' (id=%s) → %d CONTRAINDICATED_BY edge(s).",
                    record["name"],
                    injury_id,
                    contraindication_count,
                )
        except neo4j.exceptions.Neo4jError:
            logger.warning(
                "Neo4j error while ingesting injury '%s' (id=%s).",
                record.get("name", "?"),
                injury_id,
                exc_info=True,
            )
            raise


# ---------------------------------------------------------------------------
# Helpers: build flat records from PERSONAS seed data
# ---------------------------------------------------------------------------


def build_injury_records(
    member_map: dict[str, uuid.UUID],
) -> list[dict[str, Any]]:
    """Convert PERSONAS seed data into flat injury records for ingest_injuries().

    Args:
        member_map: Mapping of {email: postgres_uuid} — must already exist.

    Returns:
        List of injury dicts compatible with ``ingest_injuries()``.
    """
    records: list[dict[str, Any]] = []
    for persona in PERSONAS:
        email = str(persona["email"])
        member_id = str(member_map[email])
        injuries: list[dict[str, Any]] = persona["injuries"]
        for injury in injuries:
            injury_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{email}:{injury['name']}")
            )
            records.append(
                {
                    "id": injury_id,
                    "member_id": member_id,
                    "name": injury["name"],
                    "affected_joints": injury["affected_joints"],
                    "severity": injury["severity"],
                    "onset_date": injury.get("onset_date"),
                    "status": injury["status"],
                    "region": injury.get("region"),
                    "notes": injury.get("notes"),
                    "snomedct_hint": injury.get("snomedct_hint"),
                }
            )
    return records


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging as _logging
    import sys

    import sqlalchemy
    import sqlalchemy.orm

    from app.config import settings
    from app.knowledge_graph.seed import seed_postgres_users

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )

    # Derive member_map from PostgreSQL (upsert is idempotent)
    _engine = sqlalchemy.create_engine(
        settings.database_url.replace("+asyncpg", "")
    )
    with sqlalchemy.orm.Session(_engine) as _pg_session:
        _member_map = seed_postgres_users(_pg_session)
        _pg_session.commit()

    _records = build_injury_records(_member_map)

    _neo4j_driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        ingest_injuries(_neo4j_driver, _records)
        print(f"Done. {len(_records)} injury record(s) ingested.")
    finally:
        _neo4j_driver.close()
