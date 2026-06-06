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
