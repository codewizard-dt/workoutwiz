"""Tests for persist_audit_log helper and AuditLogEntry model."""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.agents.audit_persist import persist_audit_log
from app.models.audit_log import AuditLogEntry
from tests.conftest import TestSessionLocal


@pytest_asyncio.fixture
async def db_session(apply_migrations):
    """Provide a fresh AsyncSession per test, rolling back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_persist_audit_log_persists_entries(db_session):
    """All entries are flushed to the audit_log table with correct field mapping."""
    entries = [
        {
            "event": "router",
            "latency_ms": 42,
            "tokens_in": 10,
            "tokens_out": 5,
            "model": "claude-3-5-haiku-20241022",
            "provider": "anthropic",
            "user_id": "u1",
            "exercise_count": 3,  # unknown key → goes to extra JSONB
        },
    ]
    await persist_audit_log("sess-abc", entries, db_session)

    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.session_id == "sess-abc")
    )
    rows = result.scalars().all()

    assert len(rows) == 1
    row = rows[0]
    assert row.event == "router"
    assert row.latency_ms == 42
    assert row.tokens_in == 10
    assert row.tokens_out == 5
    assert row.model == "claude-3-5-haiku-20241022"
    assert row.provider == "anthropic"
    assert row.user_id == "u1"
    assert row.extra == {"exercise_count": 3}
    assert row.created_at is not None


@pytest.mark.asyncio
async def test_persist_audit_log_multiple_entries(db_session):
    """Multiple entries are all persisted for the same session_id."""
    entries = [
        {"event": "router", "route": "COACH", "confidence": 0.9},
        {"event": "coach", "node_name": "coach_node", "latency_ms": 200},
    ]
    await persist_audit_log("sess-multi", entries, db_session)

    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.session_id == "sess-multi")
    )
    rows = result.scalars().all()
    assert len(rows) == 2
    events = {r.event for r in rows}
    assert events == {"router", "coach"}


@pytest.mark.asyncio
async def test_persist_audit_log_no_extra_when_all_known(db_session):
    """When all keys are known fields, extra should be None."""
    entries = [
        {
            "event": "router",
            "model": "claude-3-5-haiku-20241022",
            "provider": "anthropic",
            "latency_ms": 100,
            "tokens_in": 50,
            "tokens_out": 25,
            "user_id": "u2",
            "route": "KNOWLEDGE_GRAPH",
            "confidence": 0.95,
        }
    ]
    await persist_audit_log("sess-no-extra", entries, db_session)

    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.session_id == "sess-no-extra")
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].extra is None


@pytest.mark.asyncio
async def test_persist_audit_log_empty_entries(db_session):
    """An empty entry list results in no rows inserted."""
    await persist_audit_log("sess-empty", [], db_session)

    result = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.session_id == "sess-empty")
    )
    rows = result.scalars().all()
    assert len(rows) == 0
