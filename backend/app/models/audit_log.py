from __future__ import annotations
import uuid
from typing import Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


_KNOWN_FIELDS = frozenset({
    "event", "model", "provider", "latency_ms", "tokens_in", "tokens_out",
    "user_id", "route", "confidence", "node_name", "source_type", "source_id",
})


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    event: Mapped[str] = mapped_column(String, nullable=False, index=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    node_name: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String, nullable=True)
    source_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    @classmethod
    async def create(
        cls,
        session_id: str,
        entry: dict[str, Any],
        db: AsyncSession,
    ) -> AuditLogEntry:
        """Construct and immediately persist an audit log entry.

        Known fields are mapped to typed columns; all other keys go into extra (JSONB).
        Calling this method is the only supported way to create a persisted row.
        """
        known = {k: entry.get(k) for k in _KNOWN_FIELDS}
        extra = {k: v for k, v in entry.items() if k not in _KNOWN_FIELDS} or None
        obj = cls(session_id=session_id, extra=extra, **known)
        db.add(obj)
        await db.flush()  # assigns DB-generated values (e.g. created_at) without full commit
        return obj
