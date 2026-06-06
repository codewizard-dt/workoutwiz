# 008 — Implement /workouts Endpoints (list, create, update, delete for authenticated users)

> **Depends on**: [006-auth-endpoints](006-auth-endpoints.md), [003-relational-schema-design](003-relational-schema-design.md)
> **Blocks**: [009-integration-tests](009-integration-tests.md)
> **Parallel-safe with**: [007-exercise-endpoints](007-exercise-endpoints.md)

## Objective

Implement CRUD endpoints for workouts (`GET /workouts`, `POST /workouts`, `GET /workouts/{id}`, `PUT /workouts/{id}`, `DELETE /workouts/{id}`). All endpoints require authentication. Users can only access their own workouts.

## Approach

- Each endpoint injects `current_active_user` (from `app.auth`) — returns 401 if not authenticated
- `user_id` scoping on all queries — never return another user's workouts
- `POST /workouts` accepts a full workout with sequences and sets in one request
- `PUT /workouts/{id}` replaces the full workout (delete + re-insert sequences/sets)
- Return Pydantic schemas, not ORM objects directly

## Steps

### 1. Create workout Pydantic schemas  <!-- agent: general-purpose -->

Create `backend/app/schemas/workout.py`:

```python
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.workout import WorkoutPhase, SetType


class WorkoutSetCreate(BaseModel):
    exercise_id: uuid.UUID
    set_type: SetType
    position: int = 0
    reps: int | None = None
    weight_kg: float | None = None
    duration_s: int | None = None
    speed: float | None = None
    distance: float | None = None
    calories: float | None = None


class WorkoutSequenceCreate(BaseModel):
    phase: WorkoutPhase
    position: int = 0
    sets: list[WorkoutSetCreate] = []


class WorkoutCreate(BaseModel):
    started_at: datetime
    ended_at: datetime | None = None
    sequences: list[WorkoutSequenceCreate] = []


class WorkoutSetRead(WorkoutSetCreate):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    sequence_id: uuid.UUID


class WorkoutSequenceRead(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    workout_id: uuid.UUID
    phase: WorkoutPhase
    position: int
    sets: list[WorkoutSetRead]


class WorkoutRead(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    sequences: list[WorkoutSequenceRead]
```

- [x] `backend/app/schemas/workout.py` created with Create and Read schemas
- [x] `WorkoutCreate` accepts nested sequences and sets
- [x] `WorkoutRead` includes nested sequences and sets

---

### 2. Create workouts service  <!-- agent: general-purpose -->

Create `backend/app/services/workouts.py`:

```python
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.workout import Workout, WorkoutSequence, WorkoutSet
from app.schemas.workout import WorkoutCreate


async def get_user_workouts(session: AsyncSession, user_id: uuid.UUID) -> list[Workout]:
    stmt = (
        select(Workout)
        .where(Workout.user_id == user_id)
        .options(selectinload(Workout.sequences).selectinload(WorkoutSequence.sets))
        .order_by(Workout.started_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_workout(session: AsyncSession, workout_id: uuid.UUID, user_id: uuid.UUID) -> Workout | None:
    stmt = (
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
        .options(selectinload(Workout.sequences).selectinload(WorkoutSequence.sets))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_workout(session: AsyncSession, user_id: uuid.UUID, data: WorkoutCreate) -> Workout:
    workout = Workout(user_id=user_id, started_at=data.started_at, ended_at=data.ended_at)
    session.add(workout)
    await session.flush()  # Get workout.id before inserting sequences

    for seq_data in data.sequences:
        seq = WorkoutSequence(workout_id=workout.id, phase=seq_data.phase, position=seq_data.position)
        session.add(seq)
        await session.flush()
        for set_data in seq_data.sets:
            ws = WorkoutSet(sequence_id=seq.id, **set_data.model_dump())
            session.add(ws)

    await session.commit()
    await session.refresh(workout)
    return await get_workout(session, workout.id, user_id)


async def update_workout(session: AsyncSession, workout: Workout, data: WorkoutCreate) -> Workout:
    workout.started_at = data.started_at
    workout.ended_at = data.ended_at
    # Replace sequences (cascade delete handles sets)
    await session.execute(delete(WorkoutSequence).where(WorkoutSequence.workout_id == workout.id))
    await session.flush()
    for seq_data in data.sequences:
        seq = WorkoutSequence(workout_id=workout.id, phase=seq_data.phase, position=seq_data.position)
        session.add(seq)
        await session.flush()
        for set_data in seq_data.sets:
            ws = WorkoutSet(sequence_id=seq.id, **set_data.model_dump())
            session.add(ws)
    await session.commit()
    return await get_workout(session, workout.id, workout.user_id)


async def delete_workout(session: AsyncSession, workout: Workout) -> None:
    await session.delete(workout)
    await session.commit()
```

- [x] `backend/app/services/workouts.py` created
- [x] `get_user_workouts` uses `selectinload` for nested sequences/sets (no N+1)
- [x] `create_workout` and `update_workout` handle nested sequences and sets
- [x] `delete_workout` cascades to sequences and sets

---

### 3. Create workouts router  <!-- agent: general-purpose -->

Create `backend/app/routers/workouts.py`:

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.auth import current_active_user
from app.models.user import User
from app.schemas.workout import WorkoutCreate, WorkoutRead
from app.services import workouts as workout_service

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=list[WorkoutRead])
async def list_workouts(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    return await workout_service.get_user_workouts(session, user.id)


@router.post("/", response_model=WorkoutRead, status_code=201)
async def create_workout(
    data: WorkoutCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    return await workout_service.create_workout(session, user.id, data)


@router.get("/{workout_id}", response_model=WorkoutRead)
async def get_workout(
    workout_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.put("/{workout_id}", response_model=WorkoutRead)
async def update_workout(
    workout_id: uuid.UUID,
    data: WorkoutCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return await workout_service.update_workout(session, workout, data)


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    await workout_service.delete_workout(session, workout)
```

Register in `backend/app/main.py`:
```python
from app.routers import workouts
app.include_router(workouts.router)
```

- [x] `backend/app/routers/workouts.py` created with 5 CRUD endpoints
- [x] All endpoints require `current_active_user`
- [x] `GET /workouts/{id}` for another user's workout returns 404 (not 403 — no information leak)
- [x] Router registered in `main.py`

## Acceptance Criteria

- [x] `GET /workouts` without auth → 401
- [x] `POST /workouts` creates workout with nested sequences and sets; returns 201 + `WorkoutRead`
- [x] `GET /workouts` returns only the authenticated user's workouts
- [x] `GET /workouts/{id}` returns 404 for a workout belonging to another user
- [x] `PUT /workouts/{id}` replaces sequences and sets atomically
- [x] `DELETE /workouts/{id}` returns 204; cascades to sequences and sets

---
**UAT**: [`.docs/uat/completed/008-workout-endpoints.uat.md`](../../uat/completed/008-workout-endpoints.uat.md)
