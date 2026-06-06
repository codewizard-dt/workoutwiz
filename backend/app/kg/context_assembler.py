"""
Context assembler for the GraphRAG retrieval layer.

Orchestrates graph traversal + vector search, deduplicates results,
enforces the 2 048-token budget from ADR-001 D3, and returns a
structured context slice for the generation agent.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TypedDict
from collections.abc import Callable

from neo4j import AsyncDriver

from app.knowledge_graph.traversal import (
    get_member_profile,
    get_safe_exercises,
    get_preferred_exercises,
    get_performed_exercises,
)
from app.kg.embeddings import get_exercise_vector_store

logger = logging.getLogger(__name__)

# Token budget constants (ADR-001 D3)
TOTAL_TOKEN_BUDGET = 2048
MEMBER_PROFILE_BUDGET = 200
SAFE_EXERCISES_BUDGET = 600
PREFERRED_EXERCISES_BUDGET = 400
VECTOR_HITS_BUDGET = 400

# Approximation: 1 token ≈ 4 characters (adjust if needed)
CHARS_PER_TOKEN = 4


class SectionTokenCounts(TypedDict):
    member_profile: int
    safe_exercises: int
    preferred_exercises: int
    vector_hits: int
    total: int


class ContextSlice(TypedDict):
    member_profile: dict[str, Any] | None
    safe_exercises: list[dict[str, Any]]
    preferred_exercises: list[dict[str, Any]]
    vector_hits: list[dict[str, Any]]
    token_counts: SectionTokenCounts


def _estimate_tokens(obj: Any) -> int:
    """Estimate the token count of a serializable object using char approximation."""
    try:
        text = json.dumps(obj, default=str)
    except (TypeError, ValueError):
        text = str(obj)
    return max(1, len(text) // CHARS_PER_TOKEN)


def _truncate_to_budget(
    items: list[dict[str, Any]],
    budget_tokens: int,
) -> tuple[list[dict[str, Any]], int]:
    """
    Return the longest prefix of `items` that fits within `budget_tokens`.

    Returns (truncated_list, actual_tokens_used).
    Items are included greedily from the front of the list (caller is
    responsible for ordering by priority before calling this function).
    """
    selected: list[dict[str, Any]] = []
    used = 0
    for item in items:
        cost = _estimate_tokens(item)
        if used + cost > budget_tokens:
            break
        selected.append(item)
        used += cost
    return selected, used


async def _safe_call(
    fn: Callable[..., Any], *args: Any, **kwargs: Any
) -> list[dict[str, Any]]:
    """Call an async traversal function; return [] on any exception."""
    try:
        result: list[dict[str, Any]] = await fn(*args, **kwargs)
        return result
    except Exception as exc:
        logger.warning("Traversal function %s failed: %s", fn.__name__, exc)
        return []


async def _safe_vector_search(query: str, k: int) -> list[Any]:
    """Run vector similarity search; return [] if vector store is unavailable."""
    try:
        vector_store = get_exercise_vector_store()
        # Neo4jVector.similarity_search is synchronous — run in thread pool
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(
            None, lambda: vector_store.similarity_search(query, k=k)
        )
        return docs
    except Exception as exc:
        logger.warning("Vector similarity search failed: %s", exc)
        return []


async def assemble_context(
    member_id: str,
    query: str,
    driver: AsyncDriver,
    database: str = "neo4j",
    vector_k: int = 10,
) -> ContextSlice:
    """
    Assemble a token-budgeted context slice for the generation agent.

    Orchestrates:
    1. Graph traversal (member profile, safe exercises, preferred, performed)
    2. Vector similarity search
    3. Deduplication (preferred + vector_hits filtered against safe set)
    4. Token budget enforcement per section (ADR-001 D3)

    Args:
        member_id: The Member node's `id` property (UUID string).
        query: The user's workout query (used for vector similarity search).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").
        vector_k: Number of vector similarity candidates to fetch (default: 10).

    Returns:
        A ContextSlice TypedDict with all sections and token_counts.
        Returns an empty ContextSlice (with zero counts) when the member is not found.
    """
    # Step 1: Run all traversals in parallel
    (
        member_profile,
        safe_exercises_raw,
        preferred_raw,
        performed_raw,
    ) = await asyncio.gather(
        get_member_profile(member_id, driver, database=database),
        get_safe_exercises(member_id, driver, database=database),
        _safe_call(get_preferred_exercises, member_id, driver, database=database),
        _safe_call(get_performed_exercises, member_id, driver, database=database),
    )

    if member_profile is None:
        logger.warning(
            "assemble_context: member '%s' not found in Neo4j — returning empty ContextSlice.",
            member_id,
        )
        return ContextSlice(
            member_profile={},
            safe_exercises=[],
            preferred_exercises=[],
            vector_hits=[],
            token_counts=SectionTokenCounts(
                member_profile=0,
                safe_exercises=0,
                preferred_exercises=0,
                vector_hits=0,
                total=0,
            ),
        )

    # Step 2: Vector similarity search
    vector_docs = await _safe_vector_search(query, k=vector_k)

    # Step 3: Build the safe exercise ID set for deduplication
    safe_ids: set[str] = {e["id"] for e in safe_exercises_raw}

    # Combine preferred + performed, deduplicated by id, filtered to safe set
    seen_preferred: set[str] = set()
    preferred_deduped: list[dict[str, Any]] = []
    for ex in preferred_raw + performed_raw:
        ex_id = ex.get("id")
        if ex_id and ex_id in safe_ids and ex_id not in seen_preferred:
            preferred_deduped.append(ex)
            seen_preferred.add(ex_id)

    # Filter vector hits to safe set and deduplicate against preferred
    vector_hits_filtered: list[dict[str, Any]] = []
    for doc in vector_docs:
        # LangChain Document objects have .page_content and .metadata; plain dicts have .get()
        if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
            ex_id = doc.metadata.get("id")
        else:
            ex_id = doc.get("id") if isinstance(doc, dict) else None
        if ex_id and ex_id in safe_ids and ex_id not in seen_preferred:
            vector_hits_filtered.append(
                {"id": ex_id, "name": doc.page_content, "score": doc.metadata.get("score")}
                if hasattr(doc, "page_content")
                else doc
            )

    # Step 4: Apply per-section token budgets
    profile_tokens = _estimate_tokens(member_profile)
    if profile_tokens > MEMBER_PROFILE_BUDGET:
        # Trim to essential fields only
        member_profile = {
            k: member_profile[k]
            for k in ("id", "name", "goals", "equipment", "fitness_level", "injury_names")
            if k in member_profile
        }
        profile_tokens = _estimate_tokens(member_profile)

    safe_truncated, safe_tokens = _truncate_to_budget(safe_exercises_raw, SAFE_EXERCISES_BUDGET)
    preferred_truncated, preferred_tokens = _truncate_to_budget(preferred_deduped, PREFERRED_EXERCISES_BUDGET)
    vector_truncated, vector_tokens = _truncate_to_budget(vector_hits_filtered, VECTOR_HITS_BUDGET)

    total_tokens = profile_tokens + safe_tokens + preferred_tokens + vector_tokens
    logger.info(
        "Context assembled for member %s: profile=%d, safe=%d, preferred=%d, vector=%d, total=%d tokens",
        member_id, profile_tokens, safe_tokens, preferred_tokens, vector_tokens, total_tokens,
    )

    return ContextSlice(
        member_profile=member_profile,
        safe_exercises=safe_truncated,
        preferred_exercises=preferred_truncated,
        vector_hits=vector_truncated,
        token_counts=SectionTokenCounts(
            member_profile=profile_tokens,
            safe_exercises=safe_tokens,
            preferred_exercises=preferred_tokens,
            vector_hits=vector_tokens,
            total=total_tokens,
        ),
    )
