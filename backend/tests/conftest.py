import asyncio
import json
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from alembic import command
from alembic.config import Config
from app.main import app
from app.database import get_async_session, Base
from app.config import settings

TEST_DATABASE_URL = settings.database_url.replace("/workoutwiz", "/workoutwiz_test")

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _run_alembic(direction: str) -> None:
    """Run alembic upgrade/downgrade in a thread (avoids nested asyncio.run).

    Temporarily patches settings.database_url so migrations/env.py targets the
    test DB rather than the dev DB.
    """
    original_url = settings.database_url
    settings.database_url = TEST_DATABASE_URL
    try:
        cfg = Config("alembic.ini")
        if direction == "head":
            command.upgrade(cfg, "head")
        else:
            command.downgrade(cfg, "base")
    finally:
        settings.database_url = original_url


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations():
    """Migrate test DB to head once per session; downgrade to base on teardown."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_alembic, "head")
    yield
    await loop.run_in_executor(None, _run_alembic, "base")
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_exercises(apply_migrations):
    """Seed exercises once per test session."""
    from pathlib import Path
    from app.schemas.exercise_seed import ExerciseSeedRecord

    data = json.loads(
        (Path(__file__).parent.parent.parent / ".docs/guides/1-multi-agent/exercises.json").read_text()
    )
    records = [ExerciseSeedRecord(**e) for e in data]

    async with TestSessionLocal() as session:
        count = (await session.execute(text("SELECT COUNT(*) FROM exercises"))).scalar()
        if count == 0:
            for r in records:
                await session.execute(
                    text(
                        "INSERT INTO exercises "
                        "(id, name, category, muscle_groups, equipment_required, movement_patterns, "
                        "is_reps, is_duration, supports_weight, is_bilateral, bilateral_pair_id, "
                        "priority_tier, description) "
                        "VALUES "
                        "(:id, :name, :category, :muscle_groups, :equipment_required, "
                        ":movement_patterns, "
                        ":is_reps, :is_duration, :supports_weight, :is_bilateral, :bilateral_pair_id, "
                        ":priority_tier, :description)"
                    ),
                    {
                        "id": str(r.id),
                        "name": r.name,
                        "category": r.category or "",
                        "muscle_groups": r.muscle_groups,
                        "equipment_required": r.equipment_required,
                        "movement_patterns": r.movement_patterns,
                        "is_reps": r.is_reps,
                        "is_duration": r.is_duration,
                        "supports_weight": r.supports_weight,
                        "is_bilateral": r.is_bilateral,
                        "bilateral_pair_id": str(r.bilateral_pair_id) if r.bilateral_pair_id else None,
                        "priority_tier": r.priority_tier,
                        "description": r.description,
                    },
                )
            await session.commit()


@pytest_asyncio.fixture
async def client():
    """HTTP client that routes requests through the ASGI app against the test DB.

    Each request gets its own session from TestSessionLocal so services can
    commit/flush freely without conflicting with fixture teardown.
    """
    async def override_get_session():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
