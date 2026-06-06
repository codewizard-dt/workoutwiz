"""Standalone exercise ingestion: exercises.json → Neo4j Exercise nodes + CONTRAINDICATED_BY edges."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import neo4j

from app.config import settings

logger = logging.getLogger(__name__)

_EXERCISES_PATH = (
    Path(__file__).resolve().parents[3]
    / ".docs" / "guides" / "1-multi-agent" / "exercises.json"
)


def load_exercises() -> list[dict[str, Any]]:
    with _EXERCISES_PATH.open() as f:
        data: list[dict[str, Any]] = json.load(f)
        return data


def ingest_exercises(driver: neo4j.Driver, exercises: list[dict[str, Any]] | None = None) -> int:
    """MERGE Exercise nodes from exercises.json into Neo4j, then wire CONTRAINDICATED_BY edges.

    Args:
        driver: An active Neo4j driver instance.
        exercises: Optional list of exercise dicts. If None, loads from exercises.json.

    Returns:
        The number of exercises processed.
    """
    if exercises is None:
        exercises = load_exercises()

    with driver.session() as session:
        for ex in exercises:
            session.run(
                """
                MERGE (e:Exercise {id: $id})
                SET e += {
                    name: $name,
                    muscle_groups: $muscle_groups,
                    joints_loaded: $joints_loaded,
                    movement_patterns: $movement_patterns,
                    equipment_required: $equipment_required,
                    is_reps: $is_reps,
                    is_duration: $is_duration,
                    supports_weight: $supports_weight,
                    priority_tier: $priority_tier,
                    is_bilateral: $is_bilateral,
                    bilateral_pair_id: $bilateral_pair_id,
                    side: $side,
                    estimated_rep_duration: $estimated_rep_duration
                }
                """,
                id=str(ex["id"]),
                name=ex["name"],
                muscle_groups=ex.get("muscle_groups") or [],
                joints_loaded=ex.get("joints_loaded") or [],
                movement_patterns=ex.get("movement_patterns") or [],
                equipment_required=ex.get("equipment_required") or [],
                is_reps=ex.get("is_reps", True),
                is_duration=ex.get("is_duration", False),
                supports_weight=ex.get("supports_weight", False),
                priority_tier=ex.get("priority_tier", 3),
                is_bilateral=ex.get("is_bilateral", True),
                bilateral_pair_id=str(ex["bilateral_pair_id"]) if ex.get("bilateral_pair_id") else None,
                side=ex.get("side"),
                estimated_rep_duration=ex.get("estimated_rep_duration"),
            )

        # Wire CONTRAINDICATED_BY edges for any pre-existing active Injury nodes
        # whose affected_joints overlap this exercise's joints_loaded.
        session.run(
            """
            MATCH (e:Exercise), (i:Injury {status: 'active'})
            WHERE ANY(j IN e.joints_loaded WHERE j IN i.affected_joints)
            MERGE (e)-[:CONTRAINDICATED_BY]->(i)
            """
        )

    logger.info("Ingested %d exercises; CONTRAINDICATED_BY edges merged.", len(exercises))
    return len(exercises)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    with neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    ) as _driver:
        count = ingest_exercises(_driver)
    print(f"Done. {count} exercises ingested.")
