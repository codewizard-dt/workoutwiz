"""Explainability: traverse Neo4j to explain why an exercise was skipped."""
import logging
from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


async def explain_skipped_exercise(
    member_id: str,
    exercise_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> tuple[str, dict[str, object], float]:
    """Return a human-readable reason why the exercise was excluded for this member.

    Returns:
        A (explanation, audit_entry, confidence) tuple where:
        - audit_entry contains observability fields: event, latency_ms, query_count,
          result_count, path_depth, reason_type, confidence.
        - confidence is a float in [0.0, 1.0] indicating explanation quality.

    Confidence scoring (0.0–1.0):
        Derived from traversal depth and corroborating paths (result_count).
        - No path found → 0.0
        - Contraindication found: min(1.0, depth_score + coverage_score)
            depth_score  = path_depth / MAX_PATH_DEPTH  (0.5 for our 2-hop graph)
            coverage_score = min(result_count, MAX_COVERAGE) / MAX_COVERAGE * 0.5
                           (scales from 0.125 for 1 injury up to 0.5 for 4+ injuries)
        Result: 1 injury → 0.625, 2 injuries → 0.75, 3 injuries → 0.875, 4+ → 1.0
    """
    import time

    MAX_PATH_DEPTH = 4   # maximum expected hop depth across the full KG schema
    MAX_COVERAGE = 4     # 4 corroborating paths saturates coverage contribution

    query = """
    MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(i:Injury)<-[:CONTRAINDICATED_BY]-(e:Exercise {id: $exercise_id})
    RETURN e.name AS exercise_name, collect(i.name) AS injury_names
    """
    t0 = time.monotonic()
    async with driver.session(database=database) as session:
        result = await session.run(query, member_id=member_id, exercise_id=exercise_id)
        record = await result.single()
    latency_ms = int((time.monotonic() - t0) * 1000)

    path_depth = 2  # Member -> Injury <- Exercise (fixed traversal depth)

    if not record or not record["injury_names"]:
        explanation = "This exercise was not included due to insufficient context."
        reason_type = "unknown"
        result_count = 0
        confidence = 0.0
    else:
        exercise_name = record["exercise_name"]
        injuries = ", ".join(record["injury_names"])
        explanation = f"'{exercise_name}' was skipped because it is contraindicated for: {injuries}."
        reason_type = "contraindication"
        result_count = len(record["injury_names"])
        depth_score = path_depth / MAX_PATH_DEPTH
        coverage_score = min(result_count, MAX_COVERAGE) / MAX_COVERAGE * 0.5
        confidence = min(1.0, depth_score + coverage_score)

    audit_entry: dict[str, object] = {
        "event": "kg_explainability",
        "latency_ms": latency_ms,
        "user_id": member_id,
        "query_count": 1,
        "result_count": result_count,
        "path_depth": path_depth,
        "reason_type": reason_type,
        "confidence": confidence,
    }

    return explanation, audit_entry, confidence
