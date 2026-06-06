# 003 — Design Relational Schema: User, Exercise, Workout, WorkoutSequence, WorkoutSet

> **Depends on**: [001-fastapi-project-structure](001-fastapi-project-structure.md), [002-postgres-alembic-setup](002-postgres-alembic-setup.md)
> **Blocks**: [005-exercise-seed-data](005-exercise-seed-data.md), [006-auth-endpoints](006-auth-endpoints.md), [007-exercise-endpoints](007-exercise-endpoints.md), [008-workout-endpoints](008-workout-endpoints.md)
> **Parallel-safe with**: [004-fastapi-logging-error-handling](004-fastapi-logging-error-handling.md)

## Objective

Implement all SQLAlchemy ORM models and generate the initial Alembic migration that creates the full database schema: `exercises`, `workouts`, `workout_sequences`, and `workout_sets`. The `users` table is managed by `fastapi-users` and will be added in TASK-006.

## Approach

- SQLAlchemy 2.x mapped-column style (`Mapped[T]`, `mapped_column(...)`)
- `exercises` table: UUID primary key, string columns for name/category, PostgreSQL ARRAY for `muscle_groups` and `equipment_required`, JSON for `movement_patterns`
- `workouts` table: UUID PK, foreign key to `users.id` (nullable for now, FK constraint added in TASK-006), timestamps
- `workout_sequences` table: UUID PK, FK to `workouts.id`, phase enum (warmup/main/cooldown), position integer
- `workout_sets` table: UUID PK, FK to `workout_sequences.id`, FK to `exercises.id`, `set_type` enum (STRENGTH/CARDIO), conditional metric columns

## Steps

### 1. Create Exercise model  <!-- agent: general-purpose -->

Create `backend/app/models/exercise.py`:

```python
import uuid
from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    muscle_groups: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    equipment_required: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    movement_patterns: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    is_reps: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_duration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supports_weight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_bilateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bilateral_pair_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    priority_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [x] `backend/app/models/exercise.py` created
- [x] All fields from `1-multi-agent/exercises.json` are represented
- [x] `muscle_groups` and `equipment_required` use PostgreSQL ARRAY
- [x] `movement_patterns` uses JSON column

---

### 2. Create Workout and WorkoutSequence models  <!-- agent: general-purpose -->

Create `backend/app/models/workout.py`:

```python
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WorkoutPhase(str, PyEnum):
    WARMUP = "warmup"
    MAIN = "main"
    COOLDOWN = "cooldown"


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sequences: Mapped[list["WorkoutSequence"]] = relationship(back_populates="workout", cascade="all, delete-orphan")


class WorkoutSequence(Base):
    __tablename__ = "workout_sequences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    phase: Mapped[WorkoutPhase] = mapped_column(Enum(WorkoutPhase), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workout: Mapped["Workout"] = relationship(back_populates="sequences")
    sets: Mapped[list["WorkoutSet"]] = relationship(back_populates="sequence", cascade="all, delete-orphan")
```

- [x] `backend/app/models/workout.py` created
- [x] `WorkoutPhase` enum has warmup/main/cooldown values
- [x] `Workout` → `WorkoutSequence` relationship with cascade delete

---

### 3. Create WorkoutSet model with SetType enum  <!-- agent: general-purpose -->

Add `WorkoutSet` to `backend/app/models/workout.py`:

```python
class SetType(str, PyEnum):
    STRENGTH = "STRENGTH"
    CARDIO = "CARDIO"


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workout_sequences.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False)
    set_type: Mapped[SetType] = mapped_column(Enum(SetType), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # STRENGTH fields
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    # CARDIO fields
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed: Mapped[float | None] = mapped_column(nullable=True)
    distance: Mapped[float | None] = mapped_column(nullable=True)
    calories: Mapped[float | None] = mapped_column(nullable=True)
    sequence: Mapped["WorkoutSequence"] = relationship(back_populates="sets")
```

- [x] `SetType` enum: STRENGTH / CARDIO
- [x] STRENGTH fields: `reps`, `weight_kg` (nullable)
- [x] CARDIO fields: `duration_s`, `speed`, `distance`, `calories` (nullable)
- [x] FK to `exercises.id` (no cascade — exercises are reference data)
- [x] FK to `workout_sequences.id` with cascade delete

---

### 4. Register models in package and generate migration  <!-- agent: general-purpose -->

Update `backend/app/models/__init__.py` to import all models so Alembic's `Base.metadata` picks them up:

```python
from app.models.exercise import Exercise
from app.models.workout import Workout, WorkoutSequence, WorkoutSet, WorkoutPhase, SetType

__all__ = ["Exercise", "Workout", "WorkoutSequence", "WorkoutSet", "WorkoutPhase", "SetType"]
```

Update `backend/migrations/env.py` to also import from `app.models` (so models register to `Base.metadata` before `autogenerate` runs):

```python
import app.models  # noqa: F401 — registers all models to Base.metadata
```

Then generate the migration:

```bash
cd backend && alembic revision --autogenerate -m "create exercises workouts sequences sets"
alembic upgrade head
```

- [x] `backend/app/models/__init__.py` imports all model classes
- [x] `migrations/env.py` imports `app.models` before autogenerate
- [x] Migration file created in `backend/migrations/versions/`
- [x] `alembic upgrade head` creates all 4 tables in PostgreSQL
- [x] `alembic downgrade -1` drops tables cleanly

## Acceptance Criteria

- [x] `exercises` table created with all fields from exercises.json schema
- [x] `workouts` table created with `user_id` (UUID, indexed), timestamps
- [x] `workout_sequences` table created with `phase` enum and `position`
- [x] `workout_sets` table created with `set_type` enum, STRENGTH and CARDIO nullable fields
- [x] All FK constraints use CASCADE delete where appropriate
- [x] `alembic upgrade head` and `alembic downgrade -1` both succeed cleanly

---
**UAT**: [`.docs/uat/003-relational-schema-design.uat.md`](../uat/003-relational-schema-design.uat.md)
