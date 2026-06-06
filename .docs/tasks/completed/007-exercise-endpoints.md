# 007 — Implement /exercises Endpoints (list, search by muscle_groups/equipment/movement_patterns/priority_tier)

> **Depends on**: [005-exercise-seed-data](005-exercise-seed-data.md)
> **Blocks**: [009-integration-tests](009-integration-tests.md)
> **Parallel-safe with**: [006-auth-endpoints](006-auth-endpoints.md), [008-workout-endpoints](008-workout-endpoints.md)

## Objective

Implement the `GET /exercises` endpoint with filtering by name, muscle groups, equipment, and priority tier. Exercises are public (no auth required). All filtering is done server-side against the seeded PostgreSQL data.

## Approach

- Single `GET /exercises` endpoint with optional query parameters
- Use SQLAlchemy `select()` with `where()` clauses — no ORM magic, explicit queries
- PostgreSQL ARRAY overlap operator (`&&`) for `muscle_groups` and `equipment_required` filters
- Case-insensitive name search with `ilike`
- Response: list of `ExerciseRead` Pydantic schemas; no pagination (50 exercises total)

## Steps

### 1. Create ExerciseRead schema  <!-- agent: general-purpose -->

Create `backend/app/schemas/exercise.py`:

```python
import uuid
from typing import Any
from pydantic import BaseModel


class ExerciseRead(BaseModel):
    model_config = {"from_attributes": True}

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
    bilateral_pair_id: uuid.UUID | None
    priority_tier: int
    description: str | None
```

- [x] `backend/app/schemas/exercise.py` created with `ExerciseRead` (with `from_attributes = True`)

---

### 2. Create exercises service  <!-- agent: general-purpose -->

Create `backend/app/services/exercises.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import array
from app.models.exercise import Exercise


async def list_exercises(
    session: AsyncSession,
    name: str | None = None,
    muscle_groups: list[str] | None = None,
    equipment: list[str] | None = None,
    priority_tier: int | None = None,
) -> list[Exercise]:
    stmt = select(Exercise)

    if name:
        stmt = stmt.where(Exercise.name.ilike(f"%{name}%"))
    if muscle_groups:
        stmt = stmt.where(Exercise.muscle_groups.overlap(array(muscle_groups)))
    if equipment:
        stmt = stmt.where(Exercise.equipment_required.overlap(array(equipment)))
    if priority_tier is not None:
        stmt = stmt.where(Exercise.priority_tier == priority_tier)

    stmt = stmt.order_by(Exercise.priority_tier, Exercise.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

- [x] `backend/app/services/__init__.py` created (empty)
- [x] `backend/app/services/exercises.py` created with `list_exercises`
- [x] `muscle_groups` filter uses PostgreSQL ARRAY overlap (`&&`)
- [x] `equipment` filter uses PostgreSQL ARRAY overlap
- [x] Results ordered by `priority_tier ASC, name ASC`

---

### 3. Create exercises router  <!-- agent: general-purpose -->

Create `backend/app/routers/exercises.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.schemas.exercise import ExerciseRead
from app.services.exercises import list_exercises

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[ExerciseRead])
async def get_exercises(
    name: str | None = Query(None, description="Case-insensitive name search"),
    muscle_groups: list[str] | None = Query(None, description="Filter by muscle group (any match)"),
    equipment: list[str] | None = Query(None, description="Filter by equipment (any match)"),
    priority_tier: int | None = Query(None, ge=1, le=3, description="Filter by priority tier (1=highest)"),
    session: AsyncSession = Depends(get_async_session),
) -> list[ExerciseRead]:
    return await list_exercises(session, name=name, muscle_groups=muscle_groups, equipment=equipment, priority_tier=priority_tier)
```

Register in `backend/app/main.py`:

```python
from app.routers import exercises
app.include_router(exercises.router)
```

- [x] `backend/app/routers/exercises.py` created
- [x] Router registered in `main.py` (no prefix — router has its own `/exercises` prefix)
- [x] `GET /exercises` returns all 50 exercises when no filters applied
- [x] `GET /exercises?name=squat` returns matching exercises (case-insensitive)
- [x] `GET /exercises?muscle_groups=quadriceps&muscle_groups=hamstrings` returns union
- [x] `GET /exercises?priority_tier=1` returns tier-1 exercises only

## Acceptance Criteria

- [x] `GET /exercises` returns 200 with list of `ExerciseRead` objects (no auth required)
- [x] `GET /exercises?name=bench` returns exercises with "bench" in name
- [x] `GET /exercises?muscle_groups=chest` returns exercises targeting chest
- [x] `GET /exercises?equipment=barbell` returns exercises using barbell
- [x] `GET /exercises?priority_tier=1` returns only priority 1 exercises
- [x] Multiple query params combine with AND logic
- [x] No pagination — returns all matching results (≤50 total)

---
**UAT**: [`.docs/uat/007-exercise-endpoints.uat.md`](../uat/007-exercise-endpoints.uat.md)
