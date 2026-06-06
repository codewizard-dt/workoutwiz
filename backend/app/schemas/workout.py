import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.workout import WorkoutPhase, SetType


class WorkoutSetCreate(BaseModel):
    exercise_id: uuid.UUID = Field(description="UUID of the exercise being performed", examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"])
    set_type: SetType = Field(description="Tracking type — STRENGTH (reps/weight) or CARDIO (duration/distance)", examples=["STRENGTH"])
    position: int = Field(default=0, description="Zero-based ordering within the sequence", examples=[0])
    reps: int | None = Field(default=None, description="Number of repetitions (null for cardio sets)", examples=[10])
    weight_kg: float | None = Field(default=None, description="Load in kilograms (null if bodyweight)", examples=[100.0])
    duration_s: int | None = Field(default=None, description="Duration in seconds (null for strength sets)", examples=[None])
    speed: float | None = Field(default=None, description="Speed in km/h (null if not tracked)", examples=[None])
    distance: float | None = Field(default=None, description="Distance in km (null if not tracked)", examples=[None])
    calories: float | None = Field(default=None, description="Calories burned estimate (null if not tracked)", examples=[None])


class WorkoutSequenceCreate(BaseModel):
    phase: WorkoutPhase = Field(description="Workout phase — warmup, main, or cooldown", examples=["main"])
    position: int = Field(default=0, description="Zero-based ordering of this sequence within the workout", examples=[0])
    sets: list[WorkoutSetCreate] = Field(default=[], description="Ordered list of sets in this sequence", examples=[[]])


class WorkoutCreate(BaseModel):
    started_at: datetime = Field(description="ISO 8601 timestamp when the workout began", examples=["2026-06-05T09:00:00Z"])
    ended_at: datetime | None = Field(default=None, description="ISO 8601 timestamp when the workout ended (null if in progress)", examples=[None])
    sequences: list[WorkoutSequenceCreate] = Field(default=[], description="Ordered list of exercise sequences (warmup/main/cooldown)", examples=[[]])


class WorkoutSetRead(WorkoutSetCreate):
    model_config = {"from_attributes": True}
    id: uuid.UUID = Field(description="Unique set identifier (UUID)", examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"])
    sequence_id: uuid.UUID = Field(description="UUID of the parent sequence", examples=["c3d4e5f6-a7b8-9012-cdef-123456789012"])


class WorkoutSequenceRead(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID = Field(description="Unique sequence identifier (UUID)", examples=["d4e5f6a7-b8c9-0123-defa-234567890123"])
    workout_id: uuid.UUID = Field(description="UUID of the parent workout", examples=["e5f6a7b8-c9d0-1234-efab-345678901234"])
    phase: WorkoutPhase = Field(description="Workout phase — warmup, main, or cooldown", examples=["main"])
    position: int = Field(description="Zero-based ordering within the workout", examples=[0])
    sets: list[WorkoutSetRead] = Field(description="Ordered list of sets in this sequence", examples=[[]])


class WorkoutRead(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID = Field(description="Unique workout identifier (UUID)", examples=["f6a7b8c9-d0e1-2345-fab0-456789012345"])
    user_id: uuid.UUID = Field(description="UUID of the user who owns this workout", examples=["a7b8c9d0-e1f2-3456-0ab1-567890123456"])
    started_at: datetime = Field(description="ISO 8601 timestamp when the workout began", examples=["2026-06-05T09:00:00Z"])
    ended_at: datetime | None = Field(description="ISO 8601 timestamp when the workout ended (null if in progress)", examples=[None])
    sequences: list[WorkoutSequenceRead] = Field(description="Ordered list of exercise sequences", examples=[[]])
