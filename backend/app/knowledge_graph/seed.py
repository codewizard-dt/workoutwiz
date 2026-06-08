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
from fastapi_users.password import PasswordHelper as _PasswordHelper
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
    # Assessment demo member — seeded from candidate-assessment-main/data/member-context.json
    # Uses a distinct email from the generic "Jordan Rivera" persona above
    {
        "name": "Jordan Rivera (Demo)",
        "email": "jordan.rivera@workoutwiz.demo",
        "password": "password123",
        "goals": ["strength", "rehabilitation"],
        "equipment": ["Dumbbell", "Kettlebell", "Yoga Mat", "Resistance Band - Loop", "Flat Bench"],
        "sessions_per_week": 4,
        "injuries": [
            {
                "name": "Patellofemoral pain syndrome (left knee)",
                "affected_joints": ["knee"],
                "severity": "mild",
                "status": "recovering",
                "onset_date": "2026-05-10",
                "region": "left knee",
                "notes": "Patellofemoral pain after hiking trip. Cleared for low-impact loading; avoid deep knee flexion under load and plyometrics.",
                "snomedct_hint": "Patellofemoral pain syndrome",
            }
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




# Human-readable goal texts for the goal keys used in PERSONAS
_GOAL_TEXT: dict[str, str] = {
    "strength": "Build overall strength",
    "muscle_gain": "Increase lean muscle mass",
    "fat_loss": "Reduce body fat",
    "endurance": "Improve cardiovascular endurance",
    "athletic_performance": "Improve athletic performance",
    "rehabilitation": "Recover safely from current injuries",
    "general_fitness": "Improve overall fitness",
    "mobility": "Improve joint mobility and flexibility",
    "posture": "Correct postural imbalances",
    "hypertrophy": "Maximize muscle hypertrophy",
    "upper_body_strength": "Build upper body strength",
}


def seed_coaching_context_all(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
    fake: Faker,
) -> None:
    """Generate AdherenceWeek, CoachBrief, BiomarkerSnapshot, and Goal nodes for EVERY persona.

    Produces realistic but synthetic coaching signals for each member so the
    /coach/brief endpoint returns meaningful data regardless of which account is
    used during a demo.  Jordan Rivera (Demo)'s assessment-specific data is
    applied afterwards by seed_assessment_member_context() and overwrites these
    defaults.
    """
    # Fixed reference date so re-runs stay idempotent (data won't change)
    ref_weeks = ["2026-05-12", "2026-05-19", "2026-05-26", "2026-06-02"]

    with driver.session() as session:
        for persona in PERSONAS:
            member_id = str(member_map[persona["email"]])
            has_active_injury = any(i["status"] == "active" for i in persona["injuries"])
            sessions_pw = persona["sessions_per_week"]

            # --- Adherence (4 weeks) -----------------------------------------
            # Members with active injuries or fewer sessions tend to miss more
            base_pct = 90 if not has_active_injury else 70
            pcts = []
            for i in range(4):
                jitter = random.randint(-15, 10)
                trend = -5 * i if has_active_injury else 0  # slight decline when injured
                pct = max(0, min(100, base_pct + jitter + trend))
                # Round to nearest 25 for visual clarity
                pct = round(pct / 25) * 25
                pcts.append(pct)

            for week_of, pct in zip(ref_weeks, pcts, strict=True):
                week_id = f"{member_id}:adherence:{week_of}"
                session.run(
                    """
                    MERGE (a:AdherenceWeek {id: $id})
                    SET a += {week_of: $week_of, pct: $pct}
                    WITH a
                    MATCH (m:Member {id: $member_id})
                    MERGE (m)-[:REPORTED_ADHERENCE]->(a)
                    """,
                    id=week_id, week_of=week_of, pct=pct, member_id=member_id,
                )

            # --- Churn risk (derived from adherence trend) -------------------
            trend_delta = pcts[-1] - pcts[0]
            if trend_delta <= -25 or pcts[-1] < 50:
                churn_level = "elevated"
                churn_reasons = [
                    f"Weekly adherence dropped to {pcts[-1]}%",
                    "One or more missed sessions with no reschedule",
                ]
            elif trend_delta < 0 or pcts[-1] < 75:
                churn_level = "moderate"
                churn_reasons = [f"Adherence slipped to {pcts[-1]}% this week"]
            else:
                churn_level = "low"
                churn_reasons = [f"Consistent {pcts[-1]}% adherence last week"]

            # --- Morning tasks ------------------------------------------------
            morning_task_types = ["review"]
            morning_task_texts = [
                f"Review {persona['name'].split()[0]}'s last session and plan this week's progression."
            ]
            if has_active_injury:
                morning_task_types.append("review_risk")
                injury_name = persona["injuries"][0]["name"]
                morning_task_texts.append(
                    f"Check recovery status: {injury_name} — confirm pain-free range before loading."
                )
            if pcts[-1] >= 100:
                morning_task_types.insert(0, "celebrate")
                morning_task_texts.insert(
                    0, f"{persona['name'].split()[0]} hit 100% adherence last week — acknowledge the streak!"
                )

            brief_id = f"{member_id}:coach_brief:2026-06-04"
            session.run(
                """
                MERGE (cb:CoachBrief {id: $id})
                SET cb += {
                    generated_for: '2026-06-04',
                    churn_risk_level: $churn_risk_level,
                    churn_risk_reasons: $churn_risk_reasons,
                    morning_task_types: $morning_task_types,
                    morning_task_texts: $morning_task_texts
                }
                WITH cb
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAS_COACH_BRIEF]->(cb)
                """,
                id=brief_id,
                churn_risk_level=churn_level,
                churn_risk_reasons=churn_reasons,
                morning_task_types=morning_task_types,
                morning_task_texts=morning_task_texts,
                member_id=member_id,
            )

            # --- Biomarker snapshot ------------------------------------------
            bio_id = f"{member_id}:biomarkers:2026-06-04"
            resting_hr = random.randint(52, 75)
            hrv = random.randint(30, 70)
            sleep_7d = [round(random.uniform(5.5, 8.5), 1) for _ in range(7)]
            base_weight = random.uniform(62.0, 95.0)
            weight_trend = [round(base_weight + random.uniform(-0.5, 0.5), 1) for _ in range(3)]
            session.run(
                """
                MERGE (b:BiomarkerSnapshot {id: $id})
                SET b += {
                    date: '2026-06-04',
                    resting_hr_bpm: $resting_hr_bpm,
                    hrv_ms: $hrv_ms,
                    sleep_hours_last_7_days: $sleep_hours_last_7_days,
                    weight_trend_dates: $weight_trend_dates,
                    weight_trend_kg: $weight_trend_kg
                }
                WITH b
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAS_BIOMARKER]->(b)
                """,
                id=bio_id,
                resting_hr_bpm=resting_hr,
                hrv_ms=hrv,
                sleep_hours_last_7_days=sleep_7d,
                weight_trend_dates=["2026-05-05", "2026-05-19", "2026-06-02"],
                weight_trend_kg=weight_trend,
                member_id=member_id,
            )

            # --- Goal nodes (from persona goal keys) -------------------------
            for i, goal_key in enumerate(persona.get("goals", [])):
                goal_text = _GOAL_TEXT.get(goal_key, goal_key.replace("_", " ").title())
                goal_node_id = f"{member_id}:goal:{goal_key}"
                session.run(
                    """
                    MERGE (g:Goal {id: $id})
                    SET g += {text: $text, priority: $priority, target_date: null}
                    WITH g
                    MATCH (m:Member {id: $member_id})
                    MERGE (m)-[:HAS_GOAL]->(g)
                    """,
                    id=goal_node_id,
                    text=goal_text,
                    priority=1 if i == 0 else 2,
                    member_id=member_id,
                )

            # --- Preference node ---------------------------------------------
            pref_id = f"{member_id}:preferences"
            session.run(
                """
                MERGE (p:Preference {id: $id})
                SET p += {
                    preferred_session_minutes: $session_min,
                    training_days_per_week: $sessions_pw,
                    preferred_days: [],
                    dislikes: [],
                    notes: $notes
                }
                WITH p
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAS_PREFERENCE]->(p)
                """,
                id=pref_id,
                session_min=45 + (sessions_pw * 2),
                sessions_pw=sessions_pw,
                notes=f"Trains {sessions_pw}x/week. Available equipment: {', '.join(persona['equipment'][:3])}{'…' if len(persona['equipment']) > 3 else ''}.",
                member_id=member_id,
            )

    logger.info("Seeded coaching context (adherence, brief, biomarkers, goals) for all %d members.", len(PERSONAS))
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
    """Upsert users and return {email: uuid} map.

    Uses ON CONFLICT (email) DO UPDATE so re-runs refresh the password hash
    and always return the canonical id — no separate SELECT needed.
    """
    member_map: dict[str, uuid.UUID] = {}
    for persona in PERSONAS:
        hashed = _PasswordHelper().hash(persona["password"])
        user_id = uuid.uuid4()
        result = session.execute(
            text(
                """
                INSERT INTO "user" (id, email, hashed_password, is_active, is_superuser, is_verified)
                VALUES (:id, :email, :hashed_password, true, false, true)
                ON CONFLICT (email) DO UPDATE SET
                    hashed_password = EXCLUDED.hashed_password,
                    is_active       = true,
                    is_verified     = true
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
        assert row is not None
        member_map[persona["email"]] = row[0]
        logger.info("Upserted user: %s (%s)", persona["email"], row[0])

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
    """20 FeedbackEvent nodes per member, written to both PostgreSQL and Neo4j.

    Feedback IDs are deterministic (uuid5) so re-running the seed upserts
    existing rows rather than accumulating duplicates.
    """
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

                # Deterministic UUID — same member + exercise + index always yields the same row
                feedback_id = uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"feedback:{persona['email']}:{ex['id']}:{_i}",
                )

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
                        ON CONFLICT (id) DO UPDATE SET
                            rating        = EXCLUDED.rating,
                            feedback_text = EXCLUDED.feedback_text,
                            created_at    = EXCLUDED.created_at
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
# ---------------------------------------------------------------------------
# Rich member context seeding (all personas)
# ---------------------------------------------------------------------------

_DEMO_MEMBER_EMAIL = "jordan.rivera@workoutwiz.demo"

# Equipment → exercise name mappings for synthetic workout titles
_EQUIPMENT_EXERCISES: dict[str, list[str]] = {
    "Barbell": ["Barbell Back Squat", "Barbell Bench Press", "Barbell Row", "Barbell RDL"],
    "Dumbbell": ["DB Goblet Squat", "DB Bench Press", "DB Row", "DB Romanian Deadlift", "DB Shoulder Press"],
    "Kettlebell": ["KB Swing", "KB Goblet Squat", "KB Romanian Deadlift", "KB Press"],
    "Resistance Band - Loop": ["Banded Glute Bridge", "Banded Lateral Walk", "Banded Hip Abduction"],
    "Resistance Band - With Handles": ["Band Pull-Apart", "Band Overhead Press", "Banded Row"],
    "Pull-Up Bar": ["Pull-Up", "Chin-Up", "Hanging Knee Raise"],
    "Cable Resistance Machine": ["Cable Row", "Cable Fly", "Cable Pushdown", "Cable Curl"],
    "Yoga Mat": ["Dead Bug", "Bird Dog", "Hollow Body Hold", "Plank"],
    "Jump Rope": ["Jump Rope Intervals"],
    "Box": ["Box Squat", "Step-Up", "Box Jump"],
    "Suspension Trainer": ["TRX Row", "TRX Push-Up", "TRX Squat"],
    "Stability Ball": ["Stability Ball Plank", "Stability Ball Pass"],
    "Medicine Ball": ["Med Ball Slam", "Med Ball Rotational Throw"],
}

_WORKOUT_TITLES_BY_GOAL: dict[str, list[str]] = {
    "strength": ["Lower Body Strength", "Upper Body Push", "Upper Body Pull", "Full Body Strength"],
    "muscle_gain": ["Hypertrophy Upper", "Hypertrophy Lower", "Push Day", "Pull Day"],
    "fat_loss": ["Metabolic Circuit", "HIIT Finisher", "Full Body Fat Burn"],
    "endurance": ["Cardio Intervals", "Aerobic Base", "Tempo Circuit"],
    "athletic_performance": ["Power Block", "Speed & Agility", "Athletic Conditioning"],
    "rehabilitation": ["Mobility & Activation", "Corrective Session", "Low-Load Recovery"],
    "general_fitness": ["Full Body Circuit", "Functional Training", "Active Recovery"],
    "mobility": ["Flexibility & Mobility", "Joint Prep", "Recovery Yoga"],
    "posture": ["Postural Correction", "Core & Posture", "Scapular Health"],
    "hypertrophy": ["Volume Upper", "Volume Lower", "Arm Hypertrophy"],
    "upper_body_strength": ["Pressing Block", "Pulling Block", "Shoulder Stability"],
}

_CHAT_TEMPLATES_BY_GOAL: dict[str, list[tuple[str, str]]] = {
    "strength": [
        ("member", "Finished today's squat session — hit a small PR on box squats!"),
        ("coach", "Nice work! How did your joints feel during the heavier sets?"),
        ("member", "Knees were solid, just a bit tight in the hips at the bottom."),
    ],
    "fat_loss": [
        ("member", "Got through the full circuit today, felt strong."),
        ("coach", "Great effort — did you track your session time?"),
        ("member", "About 35 min, felt like a good pace."),
    ],
    "rehabilitation": [
        ("member", "Did the mobility work, but it felt uncomfortable on the affected side."),
        ("coach", "Stay within a pain-free range — back off if it's above a 3/10."),
        ("member", "Okay, I'll be conservative. Thanks for the guidance."),
    ],
    "endurance": [
        ("member", "Completed the interval session but had to cut the last set short."),
        ("coach", "That's totally fine — listen to your body. How's your recovery?"),
        ("member", "Sleeping okay, just a bit sore in the calves."),
    ],
    "general_fitness": [
        ("member", "Finished the full body session — felt great!"),
        ("coach", "Excellent! Consistency is key. Same time next week?"),
        ("member", "Planning on it!"),
    ],
    "muscle_gain": [
        ("member", "Pumps were good today, tried the higher-rep finisher you suggested."),
        ("coach", "Perfect — that's the stimulus we're after. Protein intake on point?"),
        ("member", "Working on it, hitting around 140g most days."),
    ],
    "mobility": [
        ("member", "Hip opener felt much better this session."),
        ("coach", "Progress! Keep doing the daily activation drills."),
        ("member", "Will do, they only take 10 minutes so easy to stick to."),
    ],
}


def seed_rich_member_context_all(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
    fake: Faker,
) -> None:
    """Seed rich Member profile props, LabResult, ChatMessage, and AssessmentWorkout
    for EVERY persona that is not the demo member (jordan.rivera@workoutwiz.demo).

    Jordan Rivera (Demo) is skipped here because seed_assessment_member_context()
    runs afterwards and applies hand-authored values from member-context.json.

    Data is synthetic, varied, and deterministic (random/Faker seeded in main()).
    """
    with driver.session() as session:
        for persona in PERSONAS:
            email = persona["email"]

            # Skip the demo member — seed_assessment_member_context() handles it
            if email == _DEMO_MEMBER_EMAIL:
                continue

            if email not in member_map:
                logger.warning("Persona %s not in member_map; skipping rich context", email)
                continue

            member_id = str(member_map[email])
            has_active_injury = any(i["status"] == "active" for i in persona["injuries"])
            sessions_pw = persona["sessions_per_week"]
            goals = persona.get("goals", ["general_fitness"])
            primary_goal = goals[0] if goals else "general_fitness"
            equipment = persona.get("equipment", ["Dumbbell"])

            # ---- Rich Member profile properties ----------------------------
            sexes = ["male", "female", "non-binary"]
            sex = random.choice(sexes)
            age = random.randint(24, 58)
            height_cm = random.randint(158, 193)
            weight_kg = round(random.uniform(58.0, 102.0), 1)
            tiers = ["Self-Guided", "Group Coaching", "1:1 Coaching"]
            tier = tiers[min(sessions_pw - 1, 2)]  # more sessions → higher tier
            session.run(
                """
                MATCH (m:Member {id: $id})
                SET m += {
                    display_name: $display_name,
                    age: $age,
                    sex: $sex,
                    height_cm: $height_cm,
                    weight_kg: $weight_kg,
                    timezone: $timezone,
                    member_since: $member_since,
                    tier: $tier,
                    coach_id: $coach_id
                }
                """,
                id=member_id,
                display_name=persona["name"],
                age=age,
                sex=sex,
                height_cm=height_cm,
                weight_kg=weight_kg,
                timezone=fake.timezone(),
                member_since=fake.date_between(start_date="-2y", end_date="-3m").isoformat(),
                tier=tier,
                coach_id=f"coach_{fake.lexify('??????', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}",
            )

            # ---- LabResult: blood panel ------------------------------------
            blood_id = f"{member_id}:labs:blood_panel"
            # Vary ranges by injury/goal state
            ldl_base = 100 if not has_active_injury else 115
            session.run(
                """
                MERGE (l:LabResult {id: $id})
                SET l += {
                    type: 'blood_panel', date: $date,
                    ldl_mg_dl: $ldl_mg_dl, hdl_mg_dl: $hdl_mg_dl,
                    triglycerides_mg_dl: $triglycerides_mg_dl, hba1c_pct: $hba1c_pct,
                    vitamin_d_ng_ml: $vitamin_d_ng_ml, ferritin_ng_ml: $ferritin_ng_ml,
                    crp_mg_l: $crp_mg_l
                }
                WITH l
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAS_LAB_RESULT]->(l)
                """,
                id=blood_id,
                date=fake.date_between(start_date="-6m", end_date="-1m").isoformat(),
                ldl_mg_dl=ldl_base + random.randint(-15, 25),
                hdl_mg_dl=random.randint(45, 75),
                triglycerides_mg_dl=random.randint(80, 160),
                hba1c_pct=round(random.uniform(4.8, 5.8), 1),
                vitamin_d_ng_ml=random.randint(18, 45),
                ferritin_ng_ml=random.randint(20, 80),
                crp_mg_l=round(random.uniform(0.4, 3.5), 1) if has_active_injury else round(random.uniform(0.2, 1.5), 1),
                member_id=member_id,
            )

            # ---- LabResult: DEXA scan --------------------------------------
            dexa_id = f"{member_id}:labs:dexa_scan"
            body_fat = round(random.uniform(14.0, 36.0), 1)
            lean_mass = round(weight_kg * (1 - body_fat / 100), 1)
            fat_mass = round(weight_kg * body_fat / 100, 1)
            session.run(
                """
                MERGE (l:LabResult {id: $id})
                SET l += {
                    type: 'dexa_scan', date: $date,
                    body_fat_pct: $body_fat_pct, lean_mass_kg: $lean_mass_kg,
                    fat_mass_kg: $fat_mass_kg, bone_density_z_score: $bone_density_z_score,
                    visceral_fat_cm2: $visceral_fat_cm2
                }
                WITH l
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAS_LAB_RESULT]->(l)
                """,
                id=dexa_id,
                date=fake.date_between(start_date="-8m", end_date="-2m").isoformat(),
                body_fat_pct=body_fat,
                lean_mass_kg=lean_mass,
                fat_mass_kg=fat_mass,
                bone_density_z_score=round(random.uniform(-0.5, 1.5), 1),
                visceral_fat_cm2=random.randint(55, 130),
                member_id=member_id,
            )

            # ---- ChatMessage nodes -----------------------------------------
            templates = _CHAT_TEMPLATES_BY_GOAL.get(
                primary_goal, _CHAT_TEMPLATES_BY_GOAL["general_fitness"]
            )
            if has_active_injury:
                templates = _CHAT_TEMPLATES_BY_GOAL.get(
                    "rehabilitation", _CHAT_TEMPLATES_BY_GOAL["general_fitness"]
                )
            # Add an injury-aware extra message for injured personas
            msgs: list[dict[str, str]] = []
            for sender, text in templates:
                msgs.append({"sender": sender, "text": text})
            if has_active_injury:
                injury_name = persona["injuries"][0]["name"]
                msgs.append({
                    "sender": "member",
                    "text": f"Still managing the {injury_name} — keeping loads conservative this week.",
                })
            elif sessions_pw >= 5:
                msgs.append({
                    "sender": "member",
                    "text": f"Hit all {sessions_pw} sessions this week, feeling strong!",
                })

            base_ts = "2026-06-03T18:00:00+00:00"
            for i, msg in enumerate(msgs):
                msg_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{member_id}:chat:{i}"))
                rel_type = "SENT_MESSAGE" if msg["sender"] == "member" else "SENT_COACH_MESSAGE"
                session.run(
                    f"""
                    MERGE (cm:ChatMessage {{id: $id}})
                    SET cm += {{ts: $ts, sender: $sender, text: $text}}
                    WITH cm
                    MATCH (m:Member {{id: $member_id}})
                    MERGE (m)-[:{rel_type}]->(cm)
                    """,
                    id=msg_id,
                    ts=base_ts,
                    sender=msg["sender"],
                    text=msg["text"],
                    member_id=member_id,
                )

            # ---- AssessmentWorkout nodes -----------------------------------
            # Number of workouts scales with sessions_per_week; injured personas
            # may have fewer completed workouts
            num_workouts = min(sessions_pw + 1, 5)
            title_pool = _WORKOUT_TITLES_BY_GOAL.get(
                primary_goal, _WORKOUT_TITLES_BY_GOAL["general_fitness"]
            )
            # Gather equipment-based exercise names
            exercise_pool: list[str] = []
            for eq in equipment[:4]:
                exercise_pool.extend(_EQUIPMENT_EXERCISES.get(eq, []))
            if not exercise_pool:
                exercise_pool = ["Bodyweight Squat", "Push-Up", "Plank"]

            # Reference dates for recent workouts
            workout_dates = [
                "2026-06-03", "2026-06-01", "2026-05-29", "2026-05-27", "2026-05-25"
            ][:num_workouts]

            for j, wdate in enumerate(workout_dates):
                title = title_pool[j % len(title_pool)]
                # Injured personas have lower completion rates
                completed = not (has_active_injury and j == num_workouts - 1)
                duration = 0 if not completed else random.randint(22, 45)
                rpe = None if not completed else random.randint(5, 8)
                exercises = random.sample(exercise_pool, min(3, len(exercise_pool))) if completed else []

                wh_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{member_id}:workout:{wdate}:{title}"))
                session.run(
                    """
                    MERGE (w:AssessmentWorkout {id: $id})
                    SET w += {
                        date: $date, title: $title, completed: $completed,
                        duration_min: $duration_min, rpe: $rpe, exercises: $exercises
                    }
                    WITH w
                    MATCH (m:Member {id: $member_id})
                    MERGE (m)-[:HAD_WORKOUT]->(w)
                    """,
                    id=wh_id,
                    date=wdate,
                    title=title,
                    completed=completed,
                    duration_min=duration,
                    rpe=rpe,
                    exercises=exercises,
                    member_id=member_id,
                )

    logger.info(
        "Seeded rich member context (profile, labs, chat, workouts) for %d non-demo personas.",
        sum(1 for p in PERSONAS if p["email"] != _DEMO_MEMBER_EMAIL),
    )


# ---------------------------------------------------------------------------
# Assessment member context seeding (Jordan Rivera demo)
# ---------------------------------------------------------------------------

_ASSESSMENT_MEMBER_EMAIL = "jordan.rivera@workoutwiz.demo"


def seed_assessment_member_context(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
) -> None:
    """Seed extended member context for the assessment demo member (Jordan Rivera).

    Adds Goal, Preference, AdherenceWeek, BiomarkerSnapshot, LabResult,
    AssessmentWorkout, ChatMessage, and CoachBrief nodes linked to the Member node
    created by the normal persona seeding. Data sourced from member-context.json.
    """
    email = _ASSESSMENT_MEMBER_EMAIL
    if email not in member_map:
        logger.warning("Assessment member %s not in member_map; skipping context seed", email)
        return

    member_id = str(member_map[email])

    with driver.session() as session:
        # Extend Member node with rich profile properties
        session.run(
            """
            MATCH (m:Member {id: $id})
            SET m += {
                display_name: $display_name,
                age: $age,
                sex: $sex,
                height_cm: $height_cm,
                weight_kg: $weight_kg,
                timezone: $timezone,
                member_since: $member_since,
                tier: $tier,
                coach_id: $coach_id
            }
            """,
            id=member_id,
            display_name="Jordan Rivera",
            age=41,
            sex="female",
            height_cm=168,
            weight_kg=71.2,
            timezone="America/Los_Angeles",
            member_since="2024-09-15",
            tier="1:1 Coaching",
            coach_id="coach_01HXSAM",
        )

        # Goal nodes (3)
        for goal in [
            {"id": "goal_strength", "text": "Build lower-body strength", "priority": 1, "target_date": "2026-09-01"},
            {"id": "goal_knee", "text": "Return to pain-free squatting after left-knee flare-up", "priority": 1, "target_date": "2026-07-15"},
            {"id": "goal_sleep", "text": "Average 7+ hours of sleep on weeknights", "priority": 2, "target_date": None},
        ]:
            goal_node_id = f"{member_id}:{goal['id']}"
            session.run(
                """
                MERGE (g:Goal {id: $id})
                SET g += {text: $text, priority: $priority, target_date: $target_date}
                WITH g
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAS_GOAL]->(g)
                """,
                id=goal_node_id,
                text=goal["text"],
                priority=goal["priority"],
                target_date=goal.get("target_date"),
                member_id=member_id,
            )

        # Preference node
        pref_id = f"{member_id}:preferences"
        session.run(
            """
            MERGE (p:Preference {id: $id})
            SET p += {
                preferred_session_minutes: $preferred_session_minutes,
                training_days_per_week: $training_days_per_week,
                preferred_days: $preferred_days,
                dislikes: $dislikes,
                notes: $notes
            }
            WITH p
            MATCH (m:Member {id: $member_id})
            MERGE (m)-[:HAS_PREFERENCE]->(p)
            """,
            id=pref_id,
            preferred_session_minutes=50,
            training_days_per_week=4,
            preferred_days=["Mon", "Wed", "Thu", "Sat"],
            dislikes=["Deadlift", "Burpees"],
            notes="Prefers dumbbell and kettlebell work; trains at home. Dislikes high-impact jumping.",
            member_id=member_id,
        )

        # AdherenceWeek nodes (4 weeks, declining trend)
        for week in [
            {"week_of": "2026-05-12", "pct": 100},
            {"week_of": "2026-05-19", "pct": 100},
            {"week_of": "2026-05-26", "pct": 75},
            {"week_of": "2026-06-02", "pct": 50},
        ]:
            week_id = f"{member_id}:adherence:{week['week_of']}"
            session.run(
                """
                MERGE (a:AdherenceWeek {id: $id})
                SET a += {week_of: $week_of, pct: $pct}
                WITH a
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:REPORTED_ADHERENCE]->(a)
                """,
                id=week_id,
                week_of=week["week_of"],
                pct=week["pct"],
                member_id=member_id,
            )

        # BiomarkerSnapshot node
        bio_id = f"{member_id}:biomarkers:2026-06-04"
        session.run(
            """
            MERGE (b:BiomarkerSnapshot {id: $id})
            SET b += {
                date: $date,
                resting_hr_bpm: $resting_hr_bpm,
                hrv_ms: $hrv_ms,
                sleep_hours_last_7_days: $sleep_hours_last_7_days,
                weight_trend_dates: $weight_trend_dates,
                weight_trend_kg: $weight_trend_kg
            }
            WITH b
            MATCH (m:Member {id: $member_id})
            MERGE (m)-[:HAS_BIOMARKER]->(b)
            """,
            id=bio_id,
            date="2026-06-04",
            resting_hr_bpm=58,
            hrv_ms=47,
            sleep_hours_last_7_days=[6.1, 5.4, 7.2, 6.0, 5.1, 7.8, 6.3],
            weight_trend_dates=["2026-05-05", "2026-05-19", "2026-06-02"],
            weight_trend_kg=[72.4, 71.9, 71.2],
            member_id=member_id,
        )

        # LabResult — blood panel
        blood_id = f"{member_id}:labs:blood_panel"
        session.run(
            """
            MERGE (l:LabResult {id: $id})
            SET l += {
                type: 'blood_panel', date: $date,
                ldl_mg_dl: $ldl_mg_dl, hdl_mg_dl: $hdl_mg_dl,
                triglycerides_mg_dl: $triglycerides_mg_dl, hba1c_pct: $hba1c_pct,
                vitamin_d_ng_ml: $vitamin_d_ng_ml, ferritin_ng_ml: $ferritin_ng_ml,
                crp_mg_l: $crp_mg_l
            }
            WITH l
            MATCH (m:Member {id: $member_id})
            MERGE (m)-[:HAS_LAB_RESULT]->(l)
            """,
            id=blood_id, date="2026-04-20",
            ldl_mg_dl=118, hdl_mg_dl=61, triglycerides_mg_dl=96,
            hba1c_pct=5.3, vitamin_d_ng_ml=28, ferritin_ng_ml=41, crp_mg_l=1.2,
            member_id=member_id,
        )

        # LabResult — DEXA scan
        dexa_id = f"{member_id}:labs:dexa_scan"
        session.run(
            """
            MERGE (l:LabResult {id: $id})
            SET l += {
                type: 'dexa_scan', date: $date,
                body_fat_pct: $body_fat_pct, lean_mass_kg: $lean_mass_kg,
                fat_mass_kg: $fat_mass_kg, bone_density_z_score: $bone_density_z_score,
                visceral_fat_cm2: $visceral_fat_cm2
            }
            WITH l
            MATCH (m:Member {id: $member_id})
            MERGE (m)-[:HAS_LAB_RESULT]->(l)
            """,
            id=dexa_id, date="2026-03-30",
            body_fat_pct=29.4, lean_mass_kg=47.1, fat_mass_kg=21.0,
            bone_density_z_score=0.4, visceral_fat_cm2=78,
            member_id=member_id,
        )

        # ChatMessage nodes (member↔coach conversation history)
        for i, msg in enumerate([
            {"ts": "2026-06-03T18:42:00-07:00", "from_": "member", "text": "Knocked out the lower body session! Knee felt okay with the box squats."},
            {"ts": "2026-06-03T19:05:00-07:00", "from_": "coach", "text": "Love it — that's the green light we wanted. How's the knee this morning vs. after?"},
            {"ts": "2026-05-30T08:12:00-07:00", "from_": "member", "text": "Skipped Thursday, work blew up and I was wiped. Sorry!"},
            {"ts": "2026-05-22T07:50:00-07:00", "from_": "member", "text": "Still no barbell at home btw — only DBs and a kettlebell."},
        ]):
            msg_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{member_id}:chat:{i}"))
            rel_type = "SENT_MESSAGE" if msg["from_"] == "member" else "SENT_COACH_MESSAGE"
            session.run(
                f"""
                MERGE (cm:ChatMessage {{id: $id}})
                SET cm += {{ts: $ts, sender: $sender, text: $text}}
                WITH cm
                MATCH (m:Member {{id: $member_id}})
                MERGE (m)-[:{rel_type}]->(cm)
                """,
                id=msg_id,
                ts=msg["ts"],
                sender=msg["from_"],
                text=msg["text"],
                member_id=member_id,
            )

        # AssessmentWorkout nodes (recent session history)
        for wh in [
            {"date": "2026-06-03", "title": "Lower Body - Bands & DB", "completed": True, "duration_min": 28, "rpe": 6, "exercises": ["Goblet Squat (box-supported)", "Hip Thrust", "Banded Lateral Walk"]},
            {"date": "2026-06-01", "title": "Upper Body Push", "completed": True, "duration_min": 31, "rpe": 7, "exercises": ["DB Floor Press", "Half-Kneeling DB Press", "Band Pull-Apart"]},
            {"date": "2026-05-29", "title": "Full Body", "completed": False, "duration_min": 0, "rpe": None, "exercises": []},
            {"date": "2026-05-27", "title": "Lower Body", "completed": True, "duration_min": 26, "rpe": 6, "exercises": ["Step-Up", "KB Romanian Deadlift", "Wall Sit"]},
        ]:
            wh_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{member_id}:workout:{wh['date']}:{wh['title']}"))
            session.run(
                """
                MERGE (w:AssessmentWorkout {id: $id})
                SET w += {
                    date: $date, title: $title, completed: $completed,
                    duration_min: $duration_min, rpe: $rpe, exercises: $exercises
                }
                WITH w
                MATCH (m:Member {id: $member_id})
                MERGE (m)-[:HAD_WORKOUT]->(w)
                """,
                id=wh_id,
                date=wh["date"],
                title=wh["title"],
                completed=wh["completed"],
                duration_min=wh["duration_min"],
                rpe=wh.get("rpe"),
                exercises=wh["exercises"],
                member_id=member_id,
            )

        # CoachBrief node — morning tasks and churn risk
        brief_id = f"{member_id}:coach_brief:2026-06-04"
        session.run(
            """
            MERGE (cb:CoachBrief {id: $id})
            SET cb += {
                generated_for: $generated_for,
                churn_risk_level: $churn_risk_level,
                churn_risk_reasons: $churn_risk_reasons,
                morning_task_types: $morning_task_types,
                morning_task_texts: $morning_task_texts
            }
            WITH cb
            MATCH (m:Member {id: $member_id})
            MERGE (m)-[:HAS_COACH_BRIEF]->(cb)
            """,
            id=brief_id,
            generated_for="2026-06-04",
            churn_risk_level="elevated",
            churn_risk_reasons=[
                "Weekly adherence fell from 100% to 50% over 2 weeks",
                "One skipped session with a fatigue/work explanation",
                "Login frequency down vs. prior month",
            ],
            morning_task_types=["celebrate", "review_risk"],
            morning_task_texts=[
                "Congratulate Jordan on completing yesterday's lower-body session — first pain-free squat work since the knee flare-up.",
                "Check churn risk: adherence dropped 100% → 50% over the last two weeks.",
            ],
            member_id=member_id,
        )

    logger.info("Seeded extended assessment member context for %s (id=%s)", email, member_id)


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

        # 3a. Seed coaching context (adherence, brief, biomarkers, goals) for ALL members
        seed_coaching_context_all(driver, member_map, fake)

        # 3b. Seed rich context (profile props, labs, chat, workouts) for all non-demo members
        seed_rich_member_context_all(driver, member_map, fake)

        # 3c. Override with rich assessment-specific data for Jordan Rivera (Demo)
        seed_assessment_member_context(driver, member_map)

        # 4. Feedback needs both connections
        with Session(engine) as pg_session:
            seed_feedback(pg_session, driver, member_map, exercises, fake)
            pg_session.commit()

    # 5. Re-ingest all feedback from PostgreSQL → Neo4j via ingest_all_feedback
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
