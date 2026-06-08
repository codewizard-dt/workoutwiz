"""
One-time exercise seed script. Run from backend/:
  python scripts/seed_exercises.py
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend/ to sys.path so app imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.schemas.exercise_seed import ExerciseSeedRecord

EXERCISES_JSON = Path(__file__).parent.parent / "exercises.json"


def derive_category(r: ExerciseSeedRecord) -> str:
    """Derive a category from movement_patterns or muscle_groups when JSON lacks one."""
    if r.category:
        return r.category
    if r.movement_patterns:
        # e.g. "upper push - horizontal" -> "upper push"
        pattern = r.movement_patterns[0]
        return pattern.split(" - ")[0].strip() if " - " in pattern else pattern
    if r.muscle_groups:
        return r.muscle_groups[0]
    return "uncategorized"


async def seed():
    data = json.loads(EXERCISES_JSON.read_text())
    records = [ExerciseSeedRecord(**e) for e in data]
    print(f"Validated {len(records)} exercises.")

    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        count = (await session.execute(text("SELECT COUNT(*) FROM exercises"))).scalar()
        if count > 0:
            print(f"Exercises table already has {count} rows. Skipping seed.")
            return

        for r in records:
            await session.execute(
                text("""
                    INSERT INTO exercises (
                        id, name, category, muscle_groups, equipment_required,
                        movement_patterns, is_reps, is_duration, supports_weight,
                        is_bilateral, bilateral_pair_id, priority_tier, description,
                        joints_loaded, side, estimated_rep_duration
                    ) VALUES (
                        :id, :name, :category, :muscle_groups, :equipment_required,
                        :movement_patterns, :is_reps, :is_duration, :supports_weight,
                        :is_bilateral, :bilateral_pair_id, :priority_tier, :description,
                        :joints_loaded, :side, :estimated_rep_duration
                    )
                """),
                {
                    "id": str(r.id),
                    "name": r.name,
                    "category": derive_category(r),
                    "muscle_groups": r.muscle_groups,
                    "equipment_required": r.equipment_required,
                    "movement_patterns": r.movement_patterns,
                    "is_reps": r.is_reps,
                    "is_duration": r.is_duration,
                    "supports_weight": r.supports_weight,
                    "is_bilateral": r.is_bilateral,
                    "bilateral_pair_id": str(r.bilateral_pair_id) if r.bilateral_pair_id else None,
                    "priority_tier": r.priority_tier,
                    "description": r.description,
                    "joints_loaded": r.joints_loaded,
                    "side": r.side,
                    "estimated_rep_duration": r.estimated_rep_duration,
                },
            )
        await session.commit()
        print(f"Seeded {len(records)} exercises.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
