"""Async integration tests for GET /kg/audit/{session_id} endpoint.

Uses the conftest async client and test database to verify:
- Response schema (session_id, audit_log, total_entries)
- KG event filtering (only kg_* and retrieval_* events)
- Required entry fields (event, latency_ms, created_at)
- Expected node events (kg_hub, retrieval_*, generation_*)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import MagicMock
from sqlalchemy import insert

import pytest

from app.models.audit_log import AuditLogEntry
from app.auth import current_active_user
from app.main import app


_MOCK_USER = MagicMock()
_MOCK_USER.id = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(autouse=True)
def override_auth():
    """Override auth to use mock user for all tests."""
    app.dependency_overrides[current_active_user] = lambda: _MOCK_USER
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_kg_audit_response_schema(client):
    """Verify KgAuditResponse has correct structure with session_id, audit_log, total_entries."""
    # Insert test audit entries directly into test database
    session_id = "test-schema-session"

    # Get a fresh session from the client fixture setup
    from app.database import get_async_session
    session_factory = app.dependency_overrides[get_async_session]

    async for db in session_factory():
        # Insert test audit entries
        await db.execute(
            insert(AuditLogEntry).values([
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "kg_hub_router",
                    "latency_ms": 42,
                    "created_at": datetime(2025, 1, 1, 12, 0, 0),
                },
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "retrieval_search",
                    "latency_ms": 150,
                    "created_at": datetime(2025, 1, 1, 12, 0, 1),
                },
            ])
        )
        await db.commit()

    # Now call the endpoint
    resp = await client.get(f"/kg/audit/{session_id}")
    assert resp.status_code == 200
    data = resp.json()

    # Verify schema structure
    assert "session_id" in data
    assert "audit_log" in data
    assert "total_entries" in data

    # Verify types
    assert isinstance(data["session_id"], str)
    assert isinstance(data["audit_log"], list)
    assert isinstance(data["total_entries"], int)

    # Verify consistency
    assert data["session_id"] == session_id
    assert len(data["audit_log"]) == 2
    assert data["total_entries"] == 2


@pytest.mark.asyncio
async def test_kg_audit_filters_out_non_kg_events(client):
    """Verify /kg/audit/{session_id} returns ONLY kg_ or retrieval_ prefixed events."""
    session_id = "test-filter-session"

    from app.database import get_async_session
    session_factory = app.dependency_overrides[get_async_session]

    async for db in session_factory():
        # Insert mixed entries: KG, non-KG
        await db.execute(
            insert(AuditLogEntry).values([
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "kg_generation_executor",
                    "latency_ms": 100,
                    "created_at": datetime(2025, 1, 1, 12, 0, 0),
                },
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "retrieval_vector_search",
                    "latency_ms": 200,
                    "created_at": datetime(2025, 1, 1, 12, 0, 1),
                },
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "router",  # Non-KG event
                    "latency_ms": 50,
                    "created_at": datetime(2025, 1, 1, 12, 0, 2),
                },
            ])
        )
        await db.commit()

    # Call endpoint
    resp = await client.get(f"/kg/audit/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    audit_log = data["audit_log"]

    # Verify filtering: should have only 2 entries (kg_generation_executor, retrieval_vector_search)
    assert data["total_entries"] == 2, f"Expected 2 entries, got {data['total_entries']}"
    assert len(audit_log) == 2

    # Verify all entries are KG-prefixed
    events = {entry["event"] for entry in audit_log}
    assert events == {"kg_generation_executor", "retrieval_vector_search"}

    # Verify non-KG entry was filtered out
    assert "router" not in events


@pytest.mark.asyncio
async def test_kg_audit_entry_has_required_keys(client):
    """Verify each audit entry has required keys: event, latency_ms, created_at."""
    session_id = "test-keys-session"

    from app.database import get_async_session
    session_factory = app.dependency_overrides[get_async_session]

    async for db in session_factory():
        # Insert entries with basic fields
        await db.execute(
            insert(AuditLogEntry).values([
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "kg_hub_router",
                    "latency_ms": 42,
                    "created_at": datetime(2025, 1, 1, 12, 0, 0),
                },
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "retrieval_context_builder",
                    "latency_ms": 123,
                    "created_at": datetime(2025, 1, 1, 12, 0, 1),
                },
            ])
        )
        await db.commit()

    # Call endpoint
    resp = await client.get(f"/kg/audit/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    audit_log = data["audit_log"]

    # Verify required keys in each entry
    required_keys = {"event", "created_at", "latency_ms"}
    for entry in audit_log:
        assert required_keys.issubset(entry.keys()), \
            f"Entry {entry['event']} missing required keys. Has: {entry.keys()}"

        # Verify types
        assert isinstance(entry["event"], str)
        assert isinstance(entry["created_at"], str)
        assert isinstance(entry["latency_ms"], (int, float))

        # Verify latency_ms is non-negative
        assert entry["latency_ms"] >= 0, f"latency_ms should be non-negative, got {entry['latency_ms']}"


@pytest.mark.asyncio
async def test_kg_audit_contains_expected_kg_node_events(client):
    """
    Verify audit_log contains events from major KG nodes.
    Expects at least kg_hub and either retrieval_* or kg_generation_* events.
    """
    session_id = "test-nodes-session"

    from app.database import get_async_session
    session_factory = app.dependency_overrides[get_async_session]

    async for db in session_factory():
        # Insert events from major KG nodes
        await db.execute(
            insert(AuditLogEntry).values([
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "kg_hub_router",
                    "latency_ms": 10,
                    "created_at": datetime(2025, 1, 1, 12, 0, 0),
                },
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "retrieval_init",
                    "latency_ms": 20,
                    "created_at": datetime(2025, 1, 1, 12, 0, 1),
                },
                {
                    "session_id": session_id,
                    "user_id": str(_MOCK_USER.id),
                    "event": "kg_generation_executor",
                    "latency_ms": 50,
                    "created_at": datetime(2025, 1, 1, 12, 0, 2),
                },
            ])
        )
        await db.commit()

    # Call endpoint
    resp = await client.get(f"/kg/audit/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    audit_log = data["audit_log"]

    events = {entry["event"] for entry in audit_log}

    # At minimum, kg_hub should be present
    assert any(e.startswith("kg_hub") for e in events), \
        f"No kg_hub event found. Events: {events}"

    # Should contain retrieval or generation events (or both)
    has_retrieval = any(e.startswith("retrieval_") for e in events)
    has_generation = any(e.startswith("kg_generation_") for e in events)
    assert has_retrieval or has_generation, \
        f"No retrieval or generation events found. Events: {events}"

    # In this test, we have all three types
    assert "kg_hub_router" in events
    assert any(e.startswith("retrieval_") for e in events)
    assert any(e.startswith("kg_generation_") for e in events)
