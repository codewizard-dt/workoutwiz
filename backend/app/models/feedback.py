from __future__ import annotations
import uuid
from enum import StrEnum
from datetime import datetime
from sqlalchemy import Integer, Text, ForeignKey, CheckConstraint, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class FeedbackContextType(StrEnum):
    EXERCISE = "exercise"
    SET = "set"
    WORKOUT = "workout"


class ExerciseFeedback(Base):
    __tablename__ = "exercise_feedback"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_exercise_feedback_rating_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    workout_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)
    workout_set_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workout_sets.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_type: Mapped[FeedbackContextType] = mapped_column(SAEnum(FeedbackContextType, name="feedbackcontexttype", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
