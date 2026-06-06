# 083 — Persist audit_log entries to Postgres

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [075-instrument-kg-hub-node](075-instrument-kg-hub-node.md), [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md), [078-instrument-explainability-tool](078-instrument-explainability-tool.md), [079-add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md), [080-add-explainability-confidence-score](080-add-explainability-confidence-score.md), [081-add-kg-audit-endpoint](081-add-kg-audit-endpoint.md), [082-test-routing-trace-coverage](082-test-routing-trace-coverage.md)

## Objective

After each `/chat` graph invocation completes, flush all in-session `audit_log` entries to a new `audit_log` Postgres table so telemetry survives session eviction and can be queried directly via SQL. All fields carried in the existing audit entry dicts are stored in typed columns; node-specific overflow fields go in a `JSONB` `extra` column. A `created_at` timestamp is added by the database on insert.

## Approach

The `AuditLogEntry` model carries an async classmethod factory `create(cls, session_id, entry, db)` so that **constructing a row is the same act as persisting it** — the caller never handles `session.add()` or `session.commit()` directly. `__init__` cannot be async, so the factory pattern is the idiomatic SQLAlchemy way to achieve this.

After `graph.invoke()` returns in the chat router, iterate the final `audit_log` list and call `await AuditLogEntry.create(session_id, entry, db)` for each entry. The in-memory `state["audit_log"]` is unchanged; Postgres is an additive side-effect.

Known fixed fields: `event`, `model`, `provider`, `latency_ms`, `tokens_in`, `tokens_out`, `user_id`, `route`, `confidence`, `node_name`, `source_type`, `source_id`. All other keys go into `extra` (JSONB).

## Steps

### 1. Create `AuditLogEntry` SQLAlchemy model with `create` factory  <!-- agent: general-purpose -->

Create `backend/app/models/audit_log.py`:

```python
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
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    @classmethod
    async def create(
        cls,
        session_id: str,
        entry: dict[str, Any],
        db: "AsyncSession",
    ) -> "AuditLogEntry":
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
```

Export from `backend/app/models/__init__.py` — add `from app.models.audit_log import AuditLogEntry`.

- [x] `AuditLogEntry` model with `create` classmethod created at `backend/app/models/audit_log.py` <!-- Completed: 2026-06-06 -->
- [x] Exported from `backend/app/models/__init__.py` <!-- Completed: 2026-06-06 -->

### 2. Create Alembic migration  <!-- agent: general-purpose -->

Generate a new migration file in `backend/migrations/versions/` (use `alembic revision --autogenerate` or write manually). The migration must:

- Create table `audit_log` with all columns from Step 1
- Add `ix_audit_log_session_id` index on `session_id`
- Add `ix_audit_log_user_id` index on `user_id`
- Add `ix_audit_log_event` index on `event`
- Downgrade drops the table

File naming convention: `XXXXXXXXXXXXXXXX_add_audit_log_table.py` (auto-generated hash prefix).

Run migration: `cd backend && alembic upgrade head`

- [x] Migration file created in `backend/migrations/versions/` <!-- Completed: 2026-06-06 -->
- [x] `alembic upgrade head` runs without errors <!-- Completed: 2026-06-06 -->

### 3. Create `persist_audit_log` helper  <!-- agent: general-purpose -->

Create `backend/app/agents/audit_persist.py`:

```python
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
```

- [x] `persist_audit_log` helper created at `backend/app/agents/audit_persist.py` <!-- Completed: 2026-06-06 -->

### 4. Call `persist_audit_log` in the chat router after graph invocation  <!-- agent: general-purpose -->

In `backend/app/routers/chat.py`, locate the endpoint(s) that call `graph.invoke()` or `graph.ainvoke()`. After the graph returns and `final_state["audit_log"]` is available:

1. Inject `db: AsyncSession = Depends(get_async_session)` into the endpoint signature
2. Extract `session_id` from `final_state` (or from the request/session store)
3. Call `await persist_audit_log(session_id, final_state.get("audit_log", []), db)`

Example diff (adapt to actual function signature):
```python
from app.agents.audit_persist import persist_audit_log
from app.database import get_async_session

@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_session),
    ...
):
    ...
    final_state = await graph.ainvoke(...)
    await persist_audit_log(
        session_id=final_state.get("session_id", request.session_id),
        entries=final_state.get("audit_log", []),
        db=db,
    )
    return ...
```

- [x] `persist_audit_log` called in the chat endpoint after graph completion <!-- Completed: 2026-06-06 -->
- [x] `get_async_session` dependency injected correctly <!-- Completed: 2026-06-06 -->
- [x] No changes to graph node logic required <!-- Completed: 2026-06-06 -->

### 5. Test persistence  <!-- agent: general-purpose -->

Add a test in `backend/tests/` (e.g. `test_audit_persist.py`) that:

1. Calls `flush_audit_log` with a known list of audit entries and a real (test) DB session
2. Queries the `audit_log` table by `session_id`
3. Asserts row count matches entry count
4. Asserts all fixed fields are stored correctly
5. Asserts unknown keys landed in `extra` JSONB column
6. Asserts `created_at` is populated

```python
async def test_flush_audit_log_persists_entries(db_session):
    entries = [
        {"event": "router", "latency_ms": 42, "tokens_in": 10, "tokens_out": 5,
         "model": "claude-3-5-haiku-20241022", "provider": "anthropic",
         "user_id": "u1", "exercise_count": 3},  # exercise_count goes to extra
    ]
    await persist_audit_log("sess-abc", entries, db_session)

    from sqlalchemy import select
    from app.models.audit_log import AuditLogEntry
    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.session_id == "sess-abc")
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].event == "router"
    assert rows[0].latency_ms == 42
    assert rows[0].extra == {"exercise_count": 3}
    assert rows[0].created_at is not None
```

- [x] Test written and passing <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [ ] `audit_log` table exists in Postgres with all columns including `created_at`
- [ ] `AuditLogEntry` SQLAlchemy model covers all known fixed fields; unknown fields go in `extra` JSONB
- [ ] `flush_audit_log` is called after each chat graph invocation
- [ ] Audit entries from a `/chat` call are queryable from Postgres by `session_id`
- [ ] `created_at` is set automatically by the database on insert
- [ ] In-memory `audit_log` behavior is unchanged — no graph node logic modified
- [ ] Test confirms correct field mapping and `extra` spillover

---
**UAT**: [`.docs/uat/083-persist-audit-log-to-postgres.uat.md`](../uat/083-persist-audit-log-to-postgres.uat.md)
