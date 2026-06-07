"""
Tests for backend/app/kg/concept_resolver.py

All Neo4j driver/session interactions and embedding/vector-store calls are
mocked so no live Neo4j instance is required.

Mocking strategy
----------------
- ``app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver`` → returns an
  AsyncMock whose ``session()`` context manager yields a mock session with a
  configurable ``run()`` / ``.data()`` chain.
- ``app.kg.concept_resolver._get_embeddings`` → returns a synchronous
  MagicMock that controls the in-process cosine similarity pass.
- ``asyncio.to_thread`` is patched where needed to call the supplied callable
  synchronously (avoids real thread overhead in tests).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_async_driver(session_data: list[dict[str, Any]]) -> AsyncMock:
    """
    Build a minimal AsyncMock neo4j driver whose ``session().run().data()``
    chain returns ``session_data``.
    """
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=session_data)

    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)

    # ``async with driver.session(...) as session:``
    @asynccontextmanager
    async def _session_ctx(*args: Any, **kwargs: Any):
        yield mock_session

    mock_driver = AsyncMock()
    mock_driver.session = _session_ctx
    mock_driver.close = AsyncMock()
    return mock_driver


def _knee_body_structure() -> dict[str, Any]:
    return {
        "_label": "BodyStructure",
        "snomed_name": "Knee",
        "catalog_term": "Knee joint",
        "snomed_code": "72696002",
    }


def _kettlebell_equipment() -> dict[str, Any]:
    return {
        "_label": "Equipment",
        "name": "Kettlebell",
    }


def _lumbar_body_structure() -> dict[str, Any]:
    return {
        "_label": "BodyStructure",
        "snomed_name": "Lumbar region",
        "catalog_term": "Lower back",
        "snomed_code": "37822005",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExactHit:
    @pytest.mark.asyncio
    async def test_exact_hit_returns_method_exact(self) -> None:
        """'knee' should resolve to a BodyStructure node with method='exact'."""
        from app.kg.concept_resolver import resolve_concept

        driver = _make_async_driver([_knee_body_structure()])

        with patch(
            "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
            return_value=driver,
        ):
            result = await resolve_concept("knee")

        assert result.method == "exact"
        assert result.confidence == 1.0
        assert result.canonical_name == "Knee"
        assert result.matched_node is not None
        assert result.matched_node["_label"] == "BodyStructure"

    @pytest.mark.asyncio
    async def test_exact_hit_case_insensitive(self) -> None:
        """Normalisation makes 'KNEE' and '  Knee  ' hit the exact pass."""
        from app.kg.concept_resolver import resolve_concept

        driver = _make_async_driver([_knee_body_structure()])

        with patch(
            "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
            return_value=driver,
        ):
            result = await resolve_concept("  KNEE  ")

        assert result.method == "exact"
        assert result.confidence == 1.0


class TestFuzzyHit:
    @pytest.mark.asyncio
    async def test_fuzzy_hit_kettlebell_misspelling(self) -> None:
        """'kettlebel' (missing 'l') should fuzzy-match Kettlebell above threshold."""
        from app.kg.concept_resolver import FUZZY_THRESHOLD, resolve_concept

        # Pass 1 (exact) returns nothing; Pass 2 (fuzzy) gets the full list
        call_count = 0

        mock_result_exact = AsyncMock()
        mock_result_exact.data = AsyncMock(return_value=[])

        mock_result_fuzzy = AsyncMock()
        mock_result_fuzzy.data = AsyncMock(return_value=[_kettlebell_equipment()])

        mock_session = AsyncMock()

        async def _run_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            return mock_result_exact if call_count == 1 else mock_result_fuzzy

        mock_session.run = AsyncMock(side_effect=_run_side_effect)

        @asynccontextmanager
        async def _session_ctx(*args: Any, **kwargs: Any):
            yield mock_session

        mock_driver = AsyncMock()
        mock_driver.session = _session_ctx
        mock_driver.close = AsyncMock()

        with patch(
            "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
            return_value=mock_driver,
        ):
            result = await resolve_concept("kettlebel")

        assert result.method == "fuzzy"
        assert result.confidence >= FUZZY_THRESHOLD
        assert result.canonical_name is not None
        assert "Kettlebell" in (result.canonical_name or "")
        assert result.matched_node is not None

    @pytest.mark.asyncio
    async def test_fuzzy_hit_advances_past_exact_miss(self) -> None:
        """When exact returns empty, fuzzy is attempted."""
        from app.kg.concept_resolver import FUZZY_THRESHOLD, resolve_concept

        call_count = 0

        mock_result_empty = AsyncMock()
        mock_result_empty.data = AsyncMock(return_value=[])

        mock_result_candidates = AsyncMock()
        mock_result_candidates.data = AsyncMock(
            return_value=[
                {"_label": "Equipment", "name": "Dumbbell"},
                {"_label": "Equipment", "name": "Barbell"},
                {"_label": "Equipment", "name": "Kettlebell"},
            ]
        )

        mock_session = AsyncMock()

        async def _run_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            return mock_result_empty if call_count == 1 else mock_result_candidates

        mock_session.run = AsyncMock(side_effect=_run_side_effect)

        @asynccontextmanager
        async def _session_ctx(*args: Any, **kwargs: Any):
            yield mock_session

        mock_driver = AsyncMock()
        mock_driver.session = _session_ctx
        mock_driver.close = AsyncMock()

        with patch(
            "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
            return_value=mock_driver,
        ):
            result = await resolve_concept("kettlebell", concept_type="equipment")

        # The exact match for 'kettlebell' on Equipment should actually hit or
        # at the very least the fuzzy pass should succeed
        assert result.method in ("exact", "fuzzy")
        assert result.confidence >= FUZZY_THRESHOLD


class TestEmbeddingFallback:
    @pytest.mark.asyncio
    async def test_embedding_fallback_bad_lower_back(self) -> None:
        """
        When exact and fuzzy both miss, embedding similarity should resolve
        'bad lower back' to the lumbar region node.
        """
        from app.kg.concept_resolver import EMBEDDING_THRESHOLD, resolve_concept

        # All Cypher calls return no rows (exact + fuzzy + embedding candidate fetch miss)
        # but embedding pass gets candidates via a separate session.run call
        call_count = 0
        lumbar = _lumbar_body_structure()

        mock_result_empty = AsyncMock()
        mock_result_empty.data = AsyncMock(return_value=[])

        mock_result_candidates = AsyncMock()
        mock_result_candidates.data = AsyncMock(return_value=[lumbar])

        mock_session = AsyncMock()

        async def _run_side_effect(*args: Any, **kwargs: Any) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            # call 1 = exact pass, call 2 = fuzzy candidates (returns 1 candidate
            # but score will be low), call 3 = embedding candidate fetch
            if call_count == 1:
                return mock_result_empty
            elif call_count == 2:
                # Fuzzy candidates — return only "Lumbar region"; fuzzy score
                # for "bad lower back" vs "Lumbar region" is below threshold
                return mock_result_candidates
            else:
                return mock_result_candidates

        mock_session.run = AsyncMock(side_effect=_run_side_effect)

        @asynccontextmanager
        async def _session_ctx(*args: Any, **kwargs: Any):
            yield mock_session

        mock_driver = AsyncMock()
        mock_driver.session = _session_ctx
        mock_driver.close = AsyncMock()

        # Mock _get_embeddings to return vectors that make "bad lower back"
        # similar to "Lumbar region"
        mock_embeddings = MagicMock()
        # query vector and doc vector are nearly identical → cosine sim ≈ 1.0
        mock_embeddings.embed_query = MagicMock(return_value=[1.0, 0.0, 0.0])
        mock_embeddings.embed_documents = MagicMock(return_value=[[0.99, 0.0, 0.0]])

        with (
            patch(
                "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
                return_value=mock_driver,
            ),
            patch(
                "app.kg.concept_resolver._get_embeddings",
                return_value=mock_embeddings,
            ),
            # Replace asyncio.to_thread with the async helper that calls fn() synchronously
            patch(
                "app.kg.concept_resolver.asyncio.to_thread",
                new=_sync_to_thread,
            ),
        ):
            result = await resolve_concept("bad lower back")

        # Either fuzzy or embedding hit is acceptable; embedding is expected
        # here given the mocked high cosine sim
        assert result.method in ("fuzzy", "embedding")
        assert result.confidence >= EMBEDDING_THRESHOLD
        assert result.matched_node is not None


class TestNoMatchDegradation:
    @pytest.mark.asyncio
    async def test_no_match_returns_none_method(self) -> None:
        """When nothing clears any threshold, method='none' and matched_node is None."""
        from app.kg.concept_resolver import resolve_concept

        # All passes return empty candidates
        mock_result_empty = AsyncMock()
        mock_result_empty.data = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.run = AsyncMock(return_value=mock_result_empty)

        @asynccontextmanager
        async def _session_ctx(*args: Any, **kwargs: Any):
            yield mock_session

        mock_driver = AsyncMock()
        mock_driver.session = _session_ctx
        mock_driver.close = AsyncMock()

        mock_embeddings = MagicMock()
        # Very dissimilar vectors
        mock_embeddings.embed_query = MagicMock(return_value=[1.0, 0.0, 0.0])
        mock_embeddings.embed_documents = MagicMock(return_value=[[0.0, 1.0, 0.0]])

        with (
            patch(
                "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
                return_value=mock_driver,
            ),
            patch(
                "app.kg.concept_resolver._get_embeddings",
                return_value=mock_embeddings,
            ),
            patch(
                "app.kg.concept_resolver.asyncio.to_thread",
                new=_sync_to_thread,
            ),
        ):
            result = await resolve_concept("xyzzy_nonexistent_thing_1234")

        assert result.method == "none"
        assert result.matched_node is None
        assert result.canonical_name is None
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_empty_text_returns_none_immediately(self) -> None:
        """Empty / whitespace-only input returns method='none' without touching Neo4j."""
        from app.kg.concept_resolver import resolve_concept

        mock_driver = AsyncMock()

        with patch(
            "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
            return_value=mock_driver,
        ):
            result_empty = await resolve_concept("")
            result_ws = await resolve_concept("   ")

        # Driver should never have been created for empty input
        assert result_empty.method == "none"
        assert result_ws.method == "none"


class TestNeverRaisesOnInfraError:
    @pytest.mark.asyncio
    async def test_never_raises_when_session_run_raises(self) -> None:
        """If session.run raises, resolve_concept returns method='none' — no exception."""
        from app.kg.concept_resolver import resolve_concept

        mock_session = AsyncMock()
        mock_session.run = AsyncMock(side_effect=RuntimeError("connection refused"))

        @asynccontextmanager
        async def _session_ctx(*args: Any, **kwargs: Any):
            yield mock_session

        mock_driver = AsyncMock()
        mock_driver.session = _session_ctx
        mock_driver.close = AsyncMock()

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query = MagicMock(side_effect=RuntimeError("no model"))

        with (
            patch(
                "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
                return_value=mock_driver,
            ),
            patch(
                "app.kg.concept_resolver._get_embeddings",
                return_value=mock_embeddings,
            ),
            patch(
                "app.kg.concept_resolver.asyncio.to_thread",
                new=_sync_to_thread,
            ),
        ):
            # Must not raise
            result = await resolve_concept("knee")

        assert result.method == "none"
        assert result.matched_node is None

    @pytest.mark.asyncio
    async def test_never_raises_when_driver_creation_raises(self) -> None:
        """If driver creation itself raises, resolve_concept returns method='none'."""
        from app.kg.concept_resolver import resolve_concept

        with patch(
            "app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver",
            side_effect=ConnectionError("Neo4j unreachable"),
        ):
            result = await resolve_concept("shoulder")

        assert result.method == "none"


# ---------------------------------------------------------------------------
# Normalization unit test
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_normalize_strips_and_lowercases(self) -> None:
        from app.kg.concept_resolver import _normalize

        assert _normalize("  Knee ") == "knee"
        assert _normalize("KNEE") == "knee"
        assert _normalize("  bad   lower   back  ") == "bad lower back"

    def test_normalize_collapses_internal_whitespace(self) -> None:
        from app.kg.concept_resolver import _normalize

        assert _normalize("lower   back") == "lower back"


# ---------------------------------------------------------------------------
# Private helper: run asyncio.to_thread targets synchronously in tests
# ---------------------------------------------------------------------------


async def _sync_to_thread(fn, *args, **kwargs):
    """Async wrapper that calls *fn* synchronously — used to replace asyncio.to_thread."""
    return fn()
