from __future__ import annotations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLogEntry


async def persist_audit_log(
    session_id: str,
    entries: list[dict[str, Any]],
    db: AsyncSession,
) -> None:
    """Persist audit log entries to Postgres via AuditLogEntry.create().

    Uses AuditLogEntry.create() for each entry so the model is responsible
    for its own persistence (known fields → typed columns; overflow → extra JSONB).
    Commits once after all rows are flushed.
    """
    for entry in entries:
        await AuditLogEntry.create(session_id, entry, db)
    await db.commit()
