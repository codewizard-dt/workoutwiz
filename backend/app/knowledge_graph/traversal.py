"""
Graph traversal queries for the GraphRAG retrieval layer.

Provides injury-aware exercise filtering and member profile lookup
via direct Cypher queries against the Neo4j knowledge graph.

Edge direction note (per ingest_injuries.py and ingest_exercises.py):
    (Exercise)-[:CONTRAINDICATED_BY]->(Injury)
So to find exercises contraindicated for a member's injuries:
    MATCH (m:Member)-[:HAS_INJURY]->(i:Injury)<-[:CONTRAINDICATED_BY]-(e:Exercise)
"""

from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncDriver

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cypher queries
# ---------------------------------------------------------------------------

# All exercises contraindicated for a member's active injuries.
# Traversal: Member -[HAS_INJURY]-> Injury <-[CONTRAINDICATED_BY]- Exercise
# (Exercise)-[:CONTRAINDICATED_BY]->(Injury) is the stored edge direction.
# SNOMED-grounded safety traversal.
# Path: Member → HAS_INJURY → Injury → MAPS_TO_DISORDER → Disorder
#       → FINDING_SITE → BodyStructure → PART_OF*0.. → BodyStructure ← MAPS_TO ← Exercise
#
# PART_OF edges are seeded two ways:
#   1. Ontology edges (from SNOMED /children API): sub-structures → joint root
#   2. Bridge edges (added during ingestion): keyword-matched finding sites → catalog joint
#
# Falls back to CONTRAINDICATED_BY if no SNOMED path exists (e.g. legacy data
# with no MAPS_TO_DISORDER edge), ensuring the gate never silently opens.
_CONTRAINDICATED_IDS_QUERY = """
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(inj:Injury {status: 'active'})
OPTIONAL MATCH (inj)-[:MAPS_TO_DISORDER]->(d:Disorder)
              -[:FINDING_SITE]->(bs:BodyStructure)
              -[:PART_OF*0..]->(joint:BodyStructure)
              <-[:MAPS_TO]-(e:Exercise)
WITH m, inj, e
WHERE e IS NOT NULL
RETURN DISTINCT e.id AS exercise_id
UNION
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(inj:Injury {status: 'active'})
WHERE NOT EXISTS { MATCH (inj)-[:MAPS_TO_DISORDER]->() }
MATCH (e:Exercise)-[:CONTRAINDICATED_BY]->(inj)
RETURN DISTINCT e.id AS exercise_id
"""

# Provenance query — returns full SNOMED path for each contraindicated exercise.
# Used by generation_graph to emit PROV-O-aligned traces.
_CONTRAINDICATED_PROVENANCE_QUERY = """
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(inj:Injury {status: 'active'})
      -[:MAPS_TO_DISORDER]->(d:Disorder)
      -[:FINDING_SITE]->(bs:BodyStructure)
      -[:PART_OF*0..]->(joint:BodyStructure)
      <-[:MAPS_TO]-(e:Exercise)
RETURN DISTINCT
    e.id               AS exercise_id,
    inj.name           AS injury_name,
    d.snomed_code      AS disorder_code,
    d.snomed_name      AS disorder_name,
    bs.snomed_code     AS finding_site_code,
    bs.snomed_name     AS finding_site_name,
    joint.catalog_term AS matched_joint,
    joint.snomed_code  AS joint_snomed_code,
    joint.skos_relation AS skos_relation
"""

# All exercises NOT contraindicated for the member via the SNOMED traversal.
# Falls back to excluding CONTRAINDICATED_BY exercises for legacy injury nodes
# (i.e. Injury nodes that predate SNOMED ingestion and have no MAPS_TO_DISORDER edge).
_SAFE_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})
MATCH (e:Exercise)
WHERE NOT EXISTS {
    MATCH (m)-[:HAS_INJURY]->(inj:Injury {status: 'active'})
          -[:MAPS_TO_DISORDER]->(d:Disorder)
          -[:FINDING_SITE]->(bs:BodyStructure)
          -[:PART_OF*0..]->(joint:BodyStructure)
          <-[:MAPS_TO]-(e)
}
AND NOT EXISTS {
    MATCH (m)-[:HAS_INJURY]->(inj:Injury {status: 'active'})
    WHERE NOT EXISTS { MATCH (inj)-[:MAPS_TO_DISORDER]->() }
    MATCH (e)-[:CONTRAINDICATED_BY]->(inj)
}
RETURN
    e.id                 AS id,
    e.name               AS name,
    e.muscle_groups      AS muscle_groups,
    e.movement_patterns  AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier      AS priority_tier,
    e.is_reps            AS is_reps,
    e.is_duration        AS is_duration,
    e.supports_weight    AS supports_weight
ORDER BY e.priority_tier ASC, e.name ASC
"""

# Member profile: goals, equipment, availability, active injuries.
_MEMBER_PROFILE_QUERY = """
MATCH (m:Member {id: $member_id})
OPTIONAL MATCH (m)-[:HAS_INJURY]->(inj:Injury)
RETURN
    m.id           AS id,
    m.name         AS name,
    m.goals        AS goals,
    m.equipment    AS equipment,
    m.availability AS availability,
    m.fitness_level AS fitness_level,
    collect(DISTINCT inj.name) AS injury_names
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_contraindicated_exercise_ids(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> set[str]:
    """
    Return the set of exercise IDs that are contraindicated for this member.

    Used by the Phase 5 injury safety gate to validate generated workouts.
    Returns an empty set if the member has no recorded active injuries.

    The CONTRAINDICATED_BY edge direction in this schema is:
        (Exercise)-[:CONTRAINDICATED_BY]->(Injury)

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A set of exercise UUID strings.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _CONTRAINDICATED_IDS_QUERY, member_id=member_id
        )
        records = await result.data()

    ids = {r["exercise_id"] for r in records}
    logger.debug(
        "Member %s has %d contraindicated exercise(s).", member_id, len(ids)
    )
    return ids


async def get_safe_exercises(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """
    Return all exercises that are NOT contraindicated for this member.

    Results are ordered by priority_tier ASC (lower = higher priority),
    then alphabetically by name.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts, each containing:
            id, name, muscle_groups, movement_patterns,
            equipment_required, priority_tier, is_reps,
            is_duration, supports_weight
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _SAFE_EXERCISES_QUERY, member_id=member_id
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d safe exercise(s) found.", member_id, len(records)
    )
    return records



async def get_contraindicated_provenance(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """Return SNOMED-grounded provenance records for each contraindicated exercise.

    Each record carries the full graph path used to make the safety decision,
    suitable for constructing a PROV-O-aligned provenance trace.

    Returns:
        List of dicts with keys: exercise_id, injury_name, disorder_code,
        disorder_name, finding_site_code, finding_site_name, matched_joint,
        joint_snomed_code, skos_relation.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _CONTRAINDICATED_PROVENANCE_QUERY, member_id=member_id
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d contraindicated provenance record(s).", member_id, len(records)
    )
    return records


async def get_member_profile(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> dict[str, Any] | None:
    """
    Return a member's profile: goals, equipment, availability, injuries.

    Used by the context assembler (TASK-058) to populate the member
    profile section of the retrieval context slice.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A dict with keys: id, name, goals, equipment, availability,
        fitness_level, injury_names. Returns None if the member is not found.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _MEMBER_PROFILE_QUERY, member_id=member_id
        )
        record = await result.single()

    if record is None:
        logger.warning("Member %s not found in Neo4j.", member_id)
        return None

    return dict(record)


# ---------------------------------------------------------------------------
# Preference / feedback traversal
# ---------------------------------------------------------------------------

# Exercises the member has rated >= min_rating via the denormalized RATED edge.
# Traversal: Member -[:RATED {rating}]-> Exercise
# The RATED relationship stores rating, feedback_text, created_at directly
# for fast traversal (see knowledge-graph-schema.md §RATED).
_PREFERRED_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating >= $min_rating
RETURN
    e.id                 AS id,
    e.name               AS name,
    e.muscle_groups      AS muscle_groups,
    e.movement_patterns  AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier      AS priority_tier,
    avg(r.rating)        AS avg_rating,
    count(r)             AS feedback_count
ORDER BY avg_rating DESC, e.name ASC
"""

# Most recently performed exercises per member (distinct, ordered by recency).
# Traversal: Member -[:PERFORMED]-> WorkoutSession -[:INCLUDED]-> Exercise
# Full FeedbackEvent audit trail per member.
# Traversal: FeedbackEvent -[:ABOUT]-> Exercise, filtered by Member -[:RATED]-> FeedbackEvent
# Preserves all ratings across time (unlike the denormalized RATED->Exercise edge which only
# keeps the latest value per member/exercise pair).
_RATING_HISTORY_QUERY = """
MATCH (f:FeedbackEvent)-[:ABOUT]->(e:Exercise)
WHERE EXISTS { MATCH (m:Member {id: $member_id})-[:RATED]->(f) }
RETURN
    e.id             AS exercise_id,
    e.name           AS exercise_name,
    f.rating         AS rating,
    f.feedback_text  AS feedback_text,
    f.created_at     AS created_at,
    f.context_type   AS context_type
ORDER BY f.created_at ASC
"""

# Exercises the member has rated <= max_rating via the denormalized RATED edge.
# Traversal: Member -[:RATED {rating}]-> Exercise
# Mirrors _PREFERRED_EXERCISES_QUERY but filters for low ratings to surface disliked exercises.
_AVOIDED_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating <= $max_rating
RETURN
    e.id                 AS id,
    e.name               AS name,
    e.muscle_groups      AS muscle_groups,
    e.movement_patterns  AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier      AS priority_tier,
    avg(r.rating)        AS avg_rating,
    count(r)             AS feedback_count
ORDER BY avg_rating ASC, e.name ASC
"""

_PERFORMED_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})-[:PERFORMED]->(ws:WorkoutSession)-[:INCLUDED]->(e:Exercise)
RETURN DISTINCT
    e.id                 AS id,
    e.name               AS name,
    e.muscle_groups      AS muscle_groups,
    e.movement_patterns  AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier      AS priority_tier,
    max(ws.started_at)   AS last_performed_at
ORDER BY last_performed_at DESC
LIMIT $limit
"""


async def get_preferred_exercises(
    member_id: str,
    driver: AsyncDriver,
    min_rating: int = 4,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """
    Return exercises the member has rated >= min_rating.

    Uses the denormalized (Member)-[:RATED]->(Exercise) relationship to
    identify exercises the member has positively rated. Results are ordered
    by average rating (DESC), then name (ASC).

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        min_rating: Minimum rating threshold (default: 4, range: 1–5).
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: id, name, muscle_groups,
        movement_patterns, equipment_required, priority_tier,
        avg_rating, feedback_count. Returns [] if no qualifying ratings.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _PREFERRED_EXERCISES_QUERY,
            member_id=member_id,
            min_rating=min_rating,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d preferred exercise(s) (rating >= %d).",
        member_id, len(records), min_rating,
    )
    return records



async def get_rating_history(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """Return each FeedbackEvent the member has submitted, ordered chronologically.

    Uses the FeedbackEvent audit trail (not the denormalized RATED edge) so
    multiple ratings of the same exercise are all preserved.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: exercise_id, exercise_name, rating,
        feedback_text, created_at, context_type. Returns [] if the member
        has submitted no feedback events.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _RATING_HISTORY_QUERY,
            member_id=member_id,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d rating history event(s).",
        member_id, len(records),
    )
    return records


async def get_avoided_exercises(
    member_id: str,
    driver: AsyncDriver,
    max_rating: int = 2,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """Return exercises the member has rated <= max_rating (default: 2).

    These are exercises to down-rank or avoid in recommendations. The list
    is fed to the context assembler so the LLM has explicit signal about
    disliked exercises — not just the absence of a preference.

    Uses the denormalized (Member)-[:RATED]->(Exercise) relationship, same
    as get_preferred_exercises, but with an upper-bound rating filter.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        max_rating: Maximum rating threshold (default: 2, range: 1–5).
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: id, name, muscle_groups,
        movement_patterns, equipment_required, priority_tier,
        avg_rating, feedback_count. Returns [] if no qualifying ratings.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _AVOIDED_EXERCISES_QUERY,
            member_id=member_id,
            max_rating=max_rating,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d avoided exercise(s) (rating <= %d).",
        member_id, len(records), max_rating,
    )
    return records


async def get_performed_exercises(
    member_id: str,
    driver: AsyncDriver,
    limit: int = 20,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """
    Return the most recently performed exercises for a member.

    Traverses WorkoutSession nodes to find distinct exercises the member
    has performed, ordered by the most recent session date (DESC).

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        limit: Maximum number of distinct exercises to return (default: 20).
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: id, name, muscle_groups,
        movement_patterns, equipment_required, priority_tier,
        last_performed_at. Returns [] if the member has no workout history.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _PERFORMED_EXERCISES_QUERY,
            member_id=member_id,
            limit=limit,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d recently performed exercise(s).",
        member_id, len(records),
    )
    return records


_WORKOUT_FEEDBACK_QUERY = """
MATCH (m:Member {id: $member_id})-[:PERFORMED]->(ws:WorkoutSession)
MATCH (f:FeedbackEvent {context_type: 'workout'})-[:ABOUT]->(ws)
RETURN f.rating AS rating, f.feedback_text AS feedback_text,
       f.created_at AS created_at, ws.id AS session_id
ORDER BY f.created_at DESC
LIMIT 5
"""


async def get_workout_feedback(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """Return recent workout-level FeedbackEvent records for a member.

    Fetches FeedbackEvent nodes with context_type='workout' linked to
    WorkoutSession nodes the member has performed, ordered by recency.
    Surfaces how the member generally feels about their workouts so the
    generation agent can factor mood/recovery signals into recommendations.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: rating, feedback_text, created_at,
        session_id. Returns [] if the member has no workout feedback.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _WORKOUT_FEEDBACK_QUERY,
            member_id=member_id,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d recent workout-level feedback record(s).",
        member_id, len(records),
    )
    return records
