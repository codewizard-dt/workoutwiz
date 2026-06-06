import uuid
from typing import Any
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
    movement_patterns: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, server_default="{}")
    is_reps: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_duration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supports_weight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_bilateral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bilateral_pair_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    priority_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
