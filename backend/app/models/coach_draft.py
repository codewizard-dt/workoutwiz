import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..database import Base


class CoachDraftStatus(enum.StrEnum):
    draft = "draft"
    approved = "approved"
    sent = "sent"


class CoachDraftContentType(enum.StrEnum):
    nudge = "nudge"
    recommendation = "recommendation"


class CoachDraft(Base):
    __tablename__ = "coach_drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    member_name: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[CoachDraftContentType] = mapped_column(
        SAEnum(CoachDraftContentType, name="coachdraftcontenttype", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    grounded_on: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialised list[str]
    status: Mapped[CoachDraftStatus] = mapped_column(
        SAEnum(CoachDraftStatus, name="coachdraftstatus", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=CoachDraftStatus.draft,
        index=True,
    )
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)   # user email
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
