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


class SetType(str, PyEnum):
    STRENGTH = "STRENGTH"
    CARDIO = "CARDIO"


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
