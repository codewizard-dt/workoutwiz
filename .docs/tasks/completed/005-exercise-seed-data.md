# 005 — Import and Validate exercises.json, Load into PostgreSQL

> **Depends on**: [003-relational-schema-design](003-relational-schema-design.md)
> **Blocks**: [007-exercise-endpoints](007-exercise-endpoints.md)
> **Parallel-safe with**: [006-auth-endpoints](006-auth-endpoints.md)

## Objective

Write a one-time Alembic data migration (seed script) that reads `1-multi-agent/exercises.json`, validates each record against a Pydantic schema, and inserts all 50 exercises into the `exercises` PostgreSQL table.

## Approach

- Use an Alembic data migration (`alembic revision`) with raw SQL inserts via `op.execute()` — not ORM — so it runs reliably regardless of model changes
- Validate the JSON against a Pydantic schema before inserting to catch schema drift early
- Path to `exercises.json` resolved relative to the migration file (or an environment variable)
- Idempotent: the migration checks for existing rows and skips if already seeded

## Steps

### 1. Create Pydantic validation schema for exercises.json  <!-- agent: general-purpose -->

Create `backend/app/schemas/exercise_seed.py`:

```python
import uuid
from typing import Any
from pydantic import BaseModel


class ExerciseSeedRecord(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    muscle_groups: list[str]
    equipment_required: list[str]
    movement_patterns: dict[str, Any]
    is_reps: bool
    is_duration: bool
    supports_weight: bool
    is_bilateral: bool
    bilateral_pair_id: uuid.UUID | None = None
    priority_tier: int
    description: str | None = None
```

- [x] `backend/app/schemas/exercise_seed.py` created with `ExerciseSeedRecord`
- [x] All 50 records from `1-multi-agent/exercises.json` validate against this schema (verify by running `python -c "from app.schemas.exercise_seed import ExerciseSeedRecord; import json; [ExerciseSeedRecord(**e) for e in json.load(open('../1-multi-agent/exercises.json'))]"` from `backend/`)

---

### 2. Write seed script as standalone Python script  <!-- agent: general-purpose -->

Create `backend/scripts/seed_exercises.py`:

```python
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

EXERCISES_JSON = Path(__file__).parent.parent.parent / "1-multi-agent" / "exercises.json"


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
                        is_bilateral, bilateral_pair_id, priority_tier, description
                    ) VALUES (
                        :id, :name, :category, :muscle_groups, :equipment_required,
                        :movement_patterns::jsonb, :is_reps, :is_duration, :supports_weight,
                        :is_bilateral, :bilateral_pair_id, :priority_tier, :description
                    )
                """),
                {
                    "id": str(r.id),
                    "name": r.name,
                    "category": r.category,
                    "muscle_groups": r.muscle_groups,
                    "equipment_required": r.equipment_required,
                    "movement_patterns": json.dumps(r.movement_patterns),
                    "is_reps": r.is_reps,
                    "is_duration": r.is_duration,
                    "supports_weight": r.supports_weight,
                    "is_bilateral": r.is_bilateral,
                    "bilateral_pair_id": str(r.bilateral_pair_id) if r.bilateral_pair_id else None,
                    "priority_tier": r.priority_tier,
                    "description": r.description,
                },
            )
        await session.commit()
        print(f"Seeded {len(records)} exercises.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
```

- [x] `backend/scripts/__init__.py` created (empty)
- [x] `backend/scripts/seed_exercises.py` created
- [x] Script resolves `exercises.json` relative to project root (not hardcoded absolute path)
- [x] Script is idempotent (skips if rows already exist)

---

### 3. Run the seed and verify  <!-- agent: general-purpose -->

From `backend/` with DB running:

```bash
python scripts/seed_exercises.py
```

Then verify in psql or via a direct query:

```sql
SELECT COUNT(*) FROM exercises;   -- should be 50
SELECT name, category FROM exercises LIMIT 5;
```

- [x] `python scripts/seed_exercises.py` runs without errors
- [x] `SELECT COUNT(*) FROM exercises` returns 50
- [x] Running the script a second time prints "Exercises table already has 50 rows. Skipping seed." and exits cleanly

## Acceptance Criteria

- [x] `ExerciseSeedRecord` Pydantic schema validates all 50 records from `exercises.json` without errors
- [x] `seed_exercises.py` inserts all 50 rows on first run
- [x] Script is idempotent (safe to run twice)
- [x] `muscle_groups` and `equipment_required` stored as PostgreSQL ARRAY
- [x] `movement_patterns` stored as JSON (DB column is `json` type, not `jsonb`)
- [x] `bilateral_pair_id` NULL for exercises without a pair

---
**UAT**: [`.docs/uat/005-exercise-seed-data.uat.md`](../uat/005-exercise-seed-data.uat.md)
