"""Local conftest for knowledge_graph tests — overrides the session-scoped
autouse fixtures from the parent conftest so these unit tests run without a
live PostgreSQL or Neo4j connection."""
import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations():
    """No-op: knowledge_graph tests don't need PostgreSQL migrations."""
    yield


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_exercises(apply_migrations):
    """No-op: knowledge_graph tests don't need PostgreSQL exercise seeding."""
    yield
