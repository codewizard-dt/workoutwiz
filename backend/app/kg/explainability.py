"""Explainability: traverse Neo4j to explain why an exercise was skipped."""
import logging
from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


async def explain_skipped_exercise(
    member_id: str,
    exercise_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> str:
    """Return a human-readable reason why the exercise was excluded for this member."""
    query = """
    MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(i:Injury)<-[:CONTRAINDICATED_BY]-(e:Exercise {id: $exercise_id})
    RETURN e.name AS exercise_name, collect(i.name) AS injury_names
    """
    async with driver.session(database=database) as session:
        result = await session.run(query, member_id=member_id, exercise_id=exercise_id)
        record = await result.single()

    if not record or not record["injury_names"]:
        return "This exercise was not included due to insufficient context."

    exercise_name = record["exercise_name"]
    injuries = ", ".join(record["injury_names"])
    return f"'{exercise_name}' was skipped because it is contraindicated for: {injuries}."
