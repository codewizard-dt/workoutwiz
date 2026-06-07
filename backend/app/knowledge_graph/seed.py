"""Faker-based seed script for the knowledge graph.

Populates PostgreSQL (users, exercise_feedback) and Neo4j (Member, Exercise,
Injury, WorkoutSession, FeedbackEvent nodes + edges) with 15 fixed personas
and reproducible synthetic data.

Usage::

    python -m app.knowledge_graph.seed
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import neo4j
from faker import Faker
import bcrypt as _bcrypt_lib
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.knowledge_graph.init_schema import init_neo4j_schema
from app.knowledge_graph.ingest_exercises import ingest_exercises
from app.knowledge_graph.ingest_feedback import ingest_all_feedback
from app.knowledge_graph.ingest_workout_history import ingest_workout_history

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixed personas
# ---------------------------------------------------------------------------

PERSONAS: list[dict[str, Any]] = [
    {
        "name": "Alex Chen",
        "email": "alex@example.com",
        "password": "password123",
        "goals": ["muscle_gain", "strength"],
        "equipment": ["Barbell", "Plate", "Rack", "Flat Bench", "Dumbbell", "Cable Resistance Machine", "Handle Attachment"],
        "sessions_per_week": 4,
        "injuries": [
            {
                "name": "Left knee tendinopathy",
                "affected_joints": ["knee"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2025-11-15",
                "region": "left knee",
                "notes": "Patellar/quadriceps tendon irritation. Avoid heavy loading and deep knee flexion under load. Box squats with limited depth and hip-dominant patterns tolerated.",
                "snomedct_hint": "Patellar tendinopathy",
            }
        ],
    },
    {
        "name": "Jordan Rivera",
        "email": "jordan@example.com",
        "password": "password123",
        "goals": ["fat_loss", "general_fitness"],
        "equipment": ["Dumbbell", "Resistance Band - With Handles", "Pull-Up Bar", "Yoga Mat"],
        "sessions_per_week": 3,
        "injuries": [
            {
                "name": "Right shoulder impingement",
                "affected_joints": ["shoulder"],
                "severity": "mild",
                "status": "active",
                "onset_date": "2026-01-20",
                "region": "right shoulder",
                "notes": "Subacromial impingement. Avoid overhead pressing and internal rotation under load. Rows, band pull-aparts, and external rotation exercises tolerated.",
                "snomedct_hint": "Shoulder impingement syndrome",
            },
            {
                "name": "Lower back strain",
                "affected_joints": ["lumbar spine"],
                "severity": "mild",
                "status": "resolved",
                "onset_date": "2025-08-01",
                "region": "lumbar spine",
                "notes": "Resolved lumbar muscular strain. No current loading restrictions. Monitor for recurrence with high-volume deadlifts or heavy spinal loading.",
                "snomedct_hint": "Lumbar muscle strain",
            },
        ],
    },
    {
        "name": "Sam Nakamura",
        "email": "sam@example.com",
        "password": "password123",
        "goals": ["endurance", "athletic_performance"],
        "equipment": ["Barbell", "Plate", "Rack", "Box", "Jump Rope", "Yoga Mat"],
        "sessions_per_week": 5,
        "injuries": [
            {
                "name": "Achilles tendinopathy",
                "affected_joints": ["ankle"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2026-02-10",
                "region": "ankle",
                "notes": "Mid-portion Achilles tendinopathy. Avoid plyometrics, jump rope, and high-impact running. Loaded calf raises with pain monitoring tolerated.",
                "snomedct_hint": "Achilles tendinopathy",
            }
        ],
    },
    {
        "name": "Morgan Lee",
        "email": "morgan@example.com",
        "password": "password123",
        "goals": ["general_fitness", "mobility"],
        "equipment": ["Dumbbell", "Flat Bench", "Pull-Up Bar", "Resistance Band - Loop", "Yoga Mat"],
        "sessions_per_week": 3,
        "injuries": [],  # NO INJURIES — baseline full pool
    },
    {
        "name": "Casey Williams",
        "email": "casey@example.com",
        "password": "password123",
        "goals": ["upper_body_strength", "hypertrophy"],
        "equipment": ["Dumbbell", "EZ Bar", "Preacher Curl Bench", "Flat Bench", "Cable Resistance Machine", "Handle Attachment"],
        "sessions_per_week": 4,
        "injuries": [
            {
                "name": "Wrist tendinopathy",
                "affected_joints": ["wrist"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2026-03-05",
                "region": "wrist",
                "notes": "Flexor/extensor tendinopathy at wrist. Avoid heavy wrist loading and barbell pressing with excessive wrist extension. Neutral-grip and banded movements tolerated.",
                "snomedct_hint": "Wrist tendinopathy",
            }
        ],
    },
    {
        "name": "Riley Thompson",
        "email": "riley@example.com",
        "password": "password123",
        "goals": ["posture", "general_fitness"],
        "equipment": ["Dumbbell", "Resistance Band - With Handles", "Stability Ball", "Yoga Mat"],
        "sessions_per_week": 3,
        "injuries": [
            {
                "name": "C5-C6 cervical disc herniation",
                "affected_joints": ["cervical spine"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2025-10-01",
                "region": "cervical spine",
                "notes": "Cervical disc herniation at C5-C6 with possible radiculopathy. Avoid heavy overhead loading, barbell back squat, and cervical compression. Neutral-spine movements tolerated with close monitoring.",
                "snomedct_hint": "C5-C6 cervical disc herniation",
            }
        ],
    },
    {
        "name": "Devon Martinez",
        "email": "devon@example.com",
        "password": "password123",
        "goals": ["fat_loss", "mobility"],
        "equipment": ["Barbell", "Plate", "Rack", "Dumbbell", "Cable Resistance Machine", "Handle Attachment", "Horizontal Leg Press Machine"],
        "sessions_per_week": 4,
        "injuries": [
            {
                "name": "Hip flexor tear",
                "affected_joints": ["hip"],
                "severity": "severe",
                "status": "active",
                "onset_date": "2026-04-01",
                "region": "hip",
                "notes": "Acute hip flexor muscle tear. Avoid hip flexion under load, high knee drives, and kicking patterns. Upper body and limited lower body work with minimal hip flexion tolerated.",
                "snomedct_hint": "Hip flexor strain",
            }
        ],
    },
    {
        "name": "Quinn Anderson",
        "email": "quinn@example.com",
        "password": "password123",
        "goals": ["hypertrophy", "upper_body_strength"],
        "equipment": ["Dumbbell", "Cable Resistance Machine", "Handle Attachment", "Flat Bench", "Seated Lat Pulldown Machine"],
        "sessions_per_week": 4,
        "injuries": [
            {
                "name": "Lateral epicondylitis (tennis elbow)",
                "affected_joints": ["elbow"],
                "severity": "mild",
                "status": "active",
                "onset_date": "2026-02-28",
                "region": "elbow",
                "notes": "Lateral epicondylitis. Avoid heavy grip loading, wrist extension under load, and barbell curls. Neutral-grip pulling and band exercises tolerated.",
                "snomedct_hint": "Lateral epicondylitis",
            }
        ],
    },
    {
        "name": "Avery Jackson",
        "email": "avery@example.com",
        "password": "password123",
        "goals": ["posture", "mobility", "strength"],
        "equipment": ["Dumbbell", "Barbell", "Plate", "Rack", "Flat Bench", "Suspension Trainer", "Yoga Mat"],
        "sessions_per_week": 3,
        "injuries": [
            {
                "name": "Thoracic compression",
                "affected_joints": ["thoracic spine"],
                "severity": "mild",
                "status": "active",
                "onset_date": "2025-12-01",
                "region": "thoracic spine",
                "notes": "Thoracic vertebral compression. Avoid axial spinal loading such as barbell back squat and heavy deadlift. Upper body push/pull and hip-dominant patterns with neutral spine tolerated.",
                "snomedct_hint": "Thoracic compression fracture",
            }
        ],
    },
    {
        "name": "Skyler Brown",
        "email": "skyler@example.com",
        "password": "password123",
        "goals": ["strength", "muscle_gain"],
        "equipment": ["Barbell", "Plate", "Rack", "Dumbbell", "Flat Bench", "Cable Resistance Machine", "Handle Attachment", "Adjustable Bench - Incline"],
        "sessions_per_week": 5,
        "injuries": [  # ALL RESOLVED — must NOT create CONTRAINDICATED_BY edges
            {
                "name": "Knee sprain",
                "affected_joints": ["knee"],
                "severity": "moderate",
                "status": "resolved",
                "onset_date": "2025-01-01",
                "region": "knee",
                "notes": "Resolved ligamentous knee sprain. No current restrictions. Graduated return to full loading completed.",
                "snomedct_hint": "Knee sprain",
            },
            {
                "name": "Shoulder impingement (resolved)",
                "affected_joints": ["shoulder"],
                "severity": "mild",
                "status": "resolved",
                "onset_date": "2024-09-01",
                "region": "shoulder",
                "notes": "Resolved subacromial impingement. No current restrictions. Maintain rotator cuff prehab exercises.",
                "snomedct_hint": "Shoulder impingement syndrome",
            },
            {
                "name": "Elbow strain (resolved)",
                "affected_joints": ["elbow"],
                "severity": "mild",
                "status": "resolved",
                "onset_date": "2024-06-01",
                "region": "elbow",
                "notes": "Resolved elbow musculotendinous strain. No current restrictions.",
                "snomedct_hint": "Elbow strain",
            },
        ],
    },
    {
        "name": "Reese Garcia",
        "email": "reese@example.com",
        "password": "password123",
        "goals": ["rehabilitation"],
        "equipment": ["Dumbbell", "Resistance Band - Loop", "Miniband", "Yoga Mat"],
        "sessions_per_week": 2,
        "injuries": [  # 4 CONCURRENT ACTIVE — tests heavy filtering / fallback
            {
                "name": "Knee osteoarthritis",
                "affected_joints": ["knee"],
                "severity": "severe",
                "status": "active",
                "onset_date": "2025-06-01",
                "region": "knee",
                "notes": "Degenerative knee osteoarthritis. Avoid deep knee flexion, plyometrics, and high-impact activities. Low-load high-rep patterns, seated movements, and aquatic-style exercises tolerated.",
                "snomedct_hint": "Knee osteoarthritis",
            },
            {
                "name": "Hip labral tear",
                "affected_joints": ["hip"],
                "severity": "severe",
                "status": "active",
                "onset_date": "2025-07-15",
                "region": "hip",
                "notes": "Acetabular labral tear. Avoid deep hip flexion past 90 degrees and impingement positions (flexion + adduction + internal rotation). Limited-ROM hip patterns and upper body work tolerated.",
                "snomedct_hint": "Hip labral tear",
            },
            {
                "name": "Lumbar disc herniation",
                "affected_joints": ["lumbar spine"],
                "severity": "severe",
                "status": "active",
                "onset_date": "2025-05-01",
                "region": "lumbar spine",
                "notes": "Lumbar disc herniation with potential radicular symptoms. Avoid lumbar flexion under load, heavy deadlifts, and deep squats. Extension-biased movements and upper body work tolerated with pain monitoring.",
                "snomedct_hint": "Lumbar disc herniation",
            },
            {
                "name": "Shoulder bursitis",
                "affected_joints": ["shoulder"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2025-09-01",
                "region": "shoulder",
                "notes": "Subacromial bursitis. Avoid overhead pressing, lateral raises above 90 degrees, and internal rotation under load. Rows, external rotation, and below-shoulder movements tolerated.",
                "snomedct_hint": "Shoulder bursitis",
            },
        ],
    },
    {
        "name": "Parker Wilson",
        "email": "parker@example.com",
        "password": "password123",
        "goals": ["mobility", "posture"],
        "equipment": ["Dumbbell", "Resistance Band - With Handles", "Stability Ball", "Yoga Mat", "Lacrosse Ball"],
        "sessions_per_week": 3,
        "injuries": [  # 3 JOINTS upper body
            {
                "name": "Wrist fracture recovery",
                "affected_joints": ["wrist"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2026-01-10",
                "region": "wrist",
                "notes": "Post-fracture wrist recovery. Avoid weight-bearing through the wrist and gripping under load. Upper body pulling, banded movements, and lower body work tolerated.",
                "snomedct_hint": "Wrist fracture",
            },
            {
                "name": "Cervical stenosis",
                "affected_joints": ["cervical spine"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2025-11-01",
                "region": "cervical spine",
                "snomedct_hint": "Cervical stenosis",
            },
            {
                "name": "Thoracic kyphosis",
                "affected_joints": ["thoracic spine"],
                "severity": "mild",
                "status": "active",
                "onset_date": "2025-08-01",
                "region": "thoracic spine",
                "notes": "Postural thoracic kyphosis. Emphasize thoracic extension and scapular retraction. Avoid heavy spinal loading in kyphotic posture. Posterior chain, core, and postural exercises well tolerated.",
                "snomedct_hint": "Thoracic kyphosis",
            },
        ],
    },
    {
        "name": "Taylor Davis",
        "email": "taylor@example.com",
        "password": "password123",
        "goals": ["fat_loss", "endurance"],
        "equipment": ["Dumbbell", "Resistance Band - With Handles", "Jump Rope", "Box", "Yoga Mat"],
        "sessions_per_week": 4,
        "injuries": [  # DOUBLE LOWER EXTREMITY — knee + ankle
            {
                "name": "Patellar tendinopathy",
                "affected_joints": ["knee"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2026-03-01",
                "region": "knee",
                "notes": "Patellar tendinopathy (jumper's knee). Avoid plyometrics, jumping, and high-speed knee flexion. Isometric holds and slow eccentric loading tolerated as part of graded rehabilitation.",
                "snomedct_hint": "Patellar tendinopathy",
            },
            {
                "name": "Ankle sprain",
                "affected_joints": ["ankle"],
                "severity": "mild",
                "status": "active",
                "onset_date": "2026-04-15",
                "region": "ankle",
                "notes": "Lateral ligament ankle sprain. Avoid single-leg stance on unstable surfaces and high-impact activities. Bilateral and seated movements tolerated; graduated proprioception loading.",
                "snomedct_hint": "Ankle sprain",
            },
        ],
    },
    {
        "name": "Cameron Harris",
        "email": "cameron@example.com",
        "password": "password123",
        "goals": ["strength", "muscle_gain"],
        "equipment": ["Barbell", "Plate", "Rack", "Dumbbell", "Flat Bench", "Adjustable Bench - Incline", "Cable Resistance Machine"],
        "sessions_per_week": 4,
        "injuries": [  # BILATERAL SHOULDER — both sides
            {
                "name": "Left shoulder impingement",
                "affected_joints": ["shoulder"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2026-01-05",
                "region": "left shoulder",
                "notes": "Left subacromial impingement. Avoid overhead pressing and internal rotation under load on the left side. Rows, band pull-aparts, and external rotation exercises tolerated.",
                "snomedct_hint": "Shoulder impingement syndrome",
            },
            {
                "name": "Right shoulder impingement",
                "affected_joints": ["shoulder"],
                "severity": "moderate",
                "status": "active",
                "onset_date": "2026-01-05",
                "region": "right shoulder",
                "notes": "Right subacromial impingement. Avoid overhead pressing and internal rotation under load on the right side. Rows, band pull-aparts, and external rotation exercises tolerated.",
                "snomedct_hint": "Shoulder impingement syndrome",
            },
        ],
    },
    {
        "name": "Drew Robinson",
        "email": "drew@example.com",
        "password": "password123",
        "goals": ["strength", "muscle_gain", "fat_loss", "athletic_performance"],
        "equipment": [  # ALL equipment — full commercial gym
            "Barbell", "Plate", "Rack", "Flat Bench", "Adjustable Bench - Incline",
            "Adjustable Bench - Decline", "Dumbbell", "Cable Resistance Machine",
            "Handle Attachment", "EZ Bar", "Preacher Curl Bench", "Seated Lat Pulldown Machine",
            "Chest Supported Row Machine", "Horizontal Leg Press Machine", "Kettlebell",
            "Pull-Up Bar", "Box", "Jump Rope", "Resistance Band - Loop",
            "Resistance Band - With Handles", "Suspension Trainer", "Stability Ball",
            "Medicine Ball", "Sandbag", "BOSU", "Slant Board", "Yoga Mat", "Miniband",
        ],
        "sessions_per_week": 5,
        "injuries": [],  # NO INJURIES — max variety
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXERCISES_PATH = Path(__file__).parent.parent.parent / "exercises.json"


def load_exercises() -> list[dict[str, Any]]:
    with open(_EXERCISES_PATH) as f:
        return json.load(f)  # type: ignore[no-any-return]


def _safe_pool(persona: dict[str, Any], exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return exercises NOT contraindicated by this persona's active injuries."""
    active_joints: set[str] = set()
    for injury in persona["injuries"]:
        if injury["status"] == "active":
            active_joints.update(injury["affected_joints"])

    if not active_joints:
        return exercises

    safe = []
    for ex in exercises:
        loaded = set(ex.get("joints_loaded") or [])
        if not loaded & active_joints:
            safe.append(ex)
    return safe


def _now_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# PostgreSQL seeding
# ---------------------------------------------------------------------------

def seed_postgres_users(session: Session) -> dict[str, uuid.UUID]:
    """Insert users and return {email: uuid} map."""
    member_map: dict[str, uuid.UUID] = {}
    for persona in PERSONAS:
        hashed = _bcrypt_lib.hashpw(persona["password"].encode(), _bcrypt_lib.gensalt()).decode()
        user_id = uuid.uuid4()
        result = session.execute(
            text(
                """
                INSERT INTO "user" (id, email, hashed_password, is_active, is_superuser, is_verified)
                VALUES (:id, :email, :hashed_password, true, false, true)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
                """
            ),
            {
                "id": user_id,
                "email": persona["email"],
                "hashed_password": hashed,
            },
        )
        row = result.fetchone()
        if row:
            member_map[persona["email"]] = row[0]
            logger.info("Created user: %s (%s)", persona["email"], row[0])
        else:
            # User already exists — fetch the existing id
            existing = session.execute(
                text('SELECT id FROM "user" WHERE email = :email'),
                {"email": persona["email"]},
            ).fetchone()
            assert existing is not None, f"User {persona['email']} not found after conflict"
            member_map[persona["email"]] = existing[0]
            logger.info("Existing user: %s (%s)", persona["email"], existing[0])

    return member_map


# ---------------------------------------------------------------------------
# Neo4j seeding
# ---------------------------------------------------------------------------

def seed_exercises_neo4j(driver: neo4j.Driver, exercises: list[dict[str, Any]]) -> None:
    """Delegate to the standalone ingestion module."""
    ingest_exercises(driver, exercises)


def seed_members_neo4j(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
) -> None:
    """Ingest Member nodes into Neo4j using PostgreSQL UUIDs as the node id."""
    from app.knowledge_graph.ingest_members import ingest_members as _ingest_members

    _ingest_members(driver, member_map)


def seed_injuries_neo4j(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
    exercises: list[dict[str, Any]],
) -> None:
    """MERGE Injury nodes, HAS_INJURY edges, and CONTRAINDICATED_BY edges."""
    with driver.session() as session:
        for persona in PERSONAS:
            member_id = str(member_map[persona["email"]])

            for injury in persona["injuries"]:
                injury_id = str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{persona['email']}:{injury['name']}",
                ))

                # MERGE Injury node
                session.run(
                    """
                    MERGE (i:Injury {id: $id})
                    SET i += {
                        name: $name,
                        affected_joints: $affected_joints,
                        severity: $severity,
                        status: $status,
                        onset_date: $onset_date,
                        region: $region,
                        notes: $notes,
                        snomedct_hint: $snomedct_hint
                    }
                    """,
                    id=injury_id,
                    name=injury["name"],
                    affected_joints=injury["affected_joints"],
                    severity=injury["severity"],
                    status=injury["status"],
                    onset_date=injury["onset_date"],
                    region=injury.get("region"),
                    notes=injury.get("notes"),
                    snomedct_hint=injury.get("snomedct_hint"),
                )

                # MERGE HAS_INJURY edge (Member → Injury)
                session.run(
                    """
                    MATCH (m:Member {id: $member_id})
                    MATCH (i:Injury {id: $injury_id})
                    MERGE (m)-[:HAS_INJURY]->(i)
                    """,
                    member_id=member_id,
                    injury_id=injury_id,
                )

                # CONTRAINDICATED_BY edges — only for active injuries
                if injury["status"] == "active":
                    affected = set(injury["affected_joints"])
                    for ex in exercises:
                        loaded = set(ex.get("joints_loaded") or [])
                        if loaded & affected:
                            session.run(
                                """
                                MATCH (e:Exercise {id: $exercise_id})
                                MATCH (i:Injury {id: $injury_id})
                                MERGE (e)-[:CONTRAINDICATED_BY]->(i)
                                """,
                                exercise_id=str(ex["id"]),
                                injury_id=injury_id,
                            )

    logger.info("Seeded injuries into Neo4j.")


def seed_workout_history_neo4j(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
    exercises: list[dict[str, Any]],
    fake: Faker,
) -> None:
    """15 WorkoutSession nodes per member with 4-6 safe exercises each."""
    sessions_per_member = 15
    sessions: list[dict[str, Any]] = []

    for persona in PERSONAS:
        member_id = str(member_map[persona["email"]])
        safe = _safe_pool(persona, exercises)

        # Fallback: if pool is too small, use the full set
        pool = safe if len(safe) >= 4 else exercises

        for _ in range(sessions_per_member):
            session_id = str(uuid.uuid4())
            started_at = fake.date_time_between(
                start_date="-90d", end_date="now"
            ).replace(tzinfo=UTC)
            ended_at = started_at.replace(
                hour=min(started_at.hour + 1, 23),
                minute=random.randint(0, 59),
            )

            count = random.randint(4, 6)
            chosen = random.sample(pool, min(count, len(pool)))
            exercise_entries = []
            for ex in chosen:
                reps = [random.randint(8, 12) for _ in range(3)]
                props: dict[str, Any] = {"sets": 3, "reps": reps}
                if ex.get("supports_weight"):
                    props["weight_kg"] = round(random.uniform(20.0, 100.0), 1)

                exercise_entries.append(
                    {
                        "exercise_id": str(ex["id"]),
                        "sets": props["sets"],
                        "reps": props["reps"],
                        "weight_kg": props.get("weight_kg"),
                        "duration_s": props.get("duration_s"),
                    }
                )

            sessions.append(
                {
                    "id": session_id,
                    "member_id": member_id,
                    "started_at": started_at.isoformat(),
                    "ended_at": ended_at.isoformat(),
                    "exercises": exercise_entries,
                }
            )

    ingest_workout_history(driver, sessions)
    logger.info("Seeded workout history into Neo4j.")


def seed_feedback(
    pg_session: Session,
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
    exercises: list[dict[str, Any]],
    fake: Faker,
) -> None:
    """20 FeedbackEvent nodes per member, written to both PostgreSQL and Neo4j."""
    feedback_per_member = 20
    with driver.session() as neo_session:
        for persona in PERSONAS:
            member_id = member_map[persona["email"]]
            safe = _safe_pool(persona, exercises)
            pool = safe if safe else exercises

            for _i in range(feedback_per_member):
                ex = random.choice(pool)
                rating = random.choices(
                    [1, 2, 3, 4, 5], weights=[3, 7, 20, 35, 35]
                )[0]
                feedback_text: str | None = None
                if random.random() < 0.60:
                    feedback_text = fake.sentence(
                        nb_words=random.randint(5, 15)
                    )

                # Spread created_at across the last 90 days (deterministic per i)
                created_at = fake.date_time_between(
                    start_date="-90d", end_date="now"
                ).replace(tzinfo=UTC)

                feedback_id = uuid.uuid4()

                # --- PostgreSQL ---
                pg_session.execute(
                    text(
                        """
                        INSERT INTO exercise_feedback
                            (id, user_id, exercise_id, workout_id, workout_set_id,
                             rating, feedback_text, context_type, created_at)
                        VALUES
                            (:id, :user_id, :exercise_id, NULL, NULL,
                             :rating, :feedback_text, 'exercise', :created_at)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {
                        "id": feedback_id,
                        "user_id": member_id,
                        "exercise_id": uuid.UUID(ex["id"]),
                        "rating": rating,
                        "feedback_text": feedback_text,
                        "created_at": created_at,
                    },
                )

                # --- Neo4j ---
                neo_session.run(
                    """
                    MERGE (f:FeedbackEvent {id: $id})
                    SET f += {
                        rating: $rating,
                        feedback_text: $feedback_text,
                        created_at: $created_at
                    }
                    """,
                    id=str(feedback_id),
                    rating=rating,
                    feedback_text=feedback_text,
                    created_at=created_at.isoformat(),
                )

                neo_session.run(
                    """
                    MATCH (m:Member {id: $member_id})
                    MATCH (e:Exercise {id: $exercise_id})
                    MATCH (f:FeedbackEvent {id: $feedback_id})
                    MERGE (m)-[:RATED]->(f)
                    MERGE (f)-[:ABOUT]->(e)
                    """,
                    member_id=str(member_id),
                    exercise_id=str(ex["id"]),
                    feedback_id=str(feedback_id),
                )

    logger.info("Seeded feedback into PostgreSQL and Neo4j.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    # Sync engine — seed scripts should be simple
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    # 1. Seed PostgreSQL users
    with Session(engine) as pg_session:
        member_map = seed_postgres_users(pg_session)
        pg_session.commit()

    # 2. Seed Neo4j
    with neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    ) as driver:
        exercises = load_exercises()

        init_neo4j_schema(driver)
        seed_exercises_neo4j(driver, exercises)
        seed_members_neo4j(driver, member_map)
        seed_injuries_neo4j(driver, member_map, exercises)
        seed_workout_history_neo4j(driver, member_map, exercises, fake)

        # 3. Feedback needs both connections
        with Session(engine) as pg_session:
            seed_feedback(pg_session, driver, member_map, exercises, fake)
            pg_session.commit()

    # 4. Re-ingest all feedback from PostgreSQL → Neo4j via ingest_all_feedback
    #    (idempotent; uses the async driver)
    from neo4j import AsyncGraphDatabase
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as _AsyncSession

    async def _run_ingest() -> int:
        async_engine = create_async_engine(settings.database_url)
        async_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with _AsyncSession(async_engine) as pg_session:
            count = await ingest_all_feedback(pg_session, async_driver)
        await async_driver.close()
        return count

    ingested = asyncio.run(_run_ingest())
    print(f"[seed] ingest_all_feedback: {ingested} FeedbackEvent nodes ingested")
    print("Seed complete.")


if __name__ == "__main__":
    main()
