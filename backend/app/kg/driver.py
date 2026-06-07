"""Shared async Neo4j driver singleton.

The driver is created once during FastAPI lifespan startup and closed once on
shutdown — mirroring the SQLAlchemy ``engine`` pattern in ``database.py``.
Request handlers obtain the driver via :func:`get_neo4j_driver`, a FastAPI
dependency that returns the shared instance without closing it (lifetime is
owned by ``lifespan``).
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

import neo4j

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — None until create_neo4j_driver() is called.
_driver: neo4j.AsyncDriver | None = None


def create_neo4j_driver() -> neo4j.AsyncDriver:
    """Create (or return the existing) shared async Neo4j driver.

    Called once during ``lifespan`` startup.  Idempotent: if the driver has
    already been created it is returned unchanged.
    """
    global _driver
    if _driver is None:
        _driver = neo4j.AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        logger.info("Neo4j async driver created (uri=%s).", settings.neo4j_uri)
    return _driver


async def close_neo4j_driver() -> None:
    """Close the shared driver.  Called once during ``lifespan`` shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j async driver closed.")


async def get_neo4j_driver() -> AsyncGenerator[neo4j.AsyncDriver, None]:
    """FastAPI dependency that yields the shared async Neo4j driver.

    Does **not** close the driver — lifetime is managed by ``lifespan``.
    Mirrors the :func:`app.database.get_async_session` pattern.

    Usage::

        @router.get("/example")
        async def handler(driver: neo4j.AsyncDriver = Depends(get_neo4j_driver)):
            ...
    """
    if _driver is None:
        raise RuntimeError(
            "Neo4j driver has not been initialised. "
            "Ensure create_neo4j_driver() is called during lifespan startup."
        )
    yield _driver
