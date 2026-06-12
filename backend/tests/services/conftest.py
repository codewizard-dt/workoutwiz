"""Override session-scoped DB fixtures so pure-unit tests run without a database."""
import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations():
    """No-op: accountability service tests need no database."""
    yield


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_exercises(apply_migrations):
    """No-op: accountability service tests need no database."""
    yield
