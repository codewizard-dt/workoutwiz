"""
GraphRAG retrieval sub-graph.

A LangGraph StateGraph that orchestrates member profile lookup,
injury-aware filtering, preference traversal, vector search, and
context assembly into a single composable graph.

Usage:
    from app.kg.retrieval_graph import build_retrieval_graph

    graph = build_retrieval_graph(driver)
    result = await graph.ainvoke({"member_id": "...", "query": "build a leg workout"})
    context = result["context"]  # ContextSlice
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from neo4j import AsyncDriver

from app.kg.context_assembler import ContextSlice, assemble_context
from app.knowledge_graph.traversal import (
    get_contraindicated_exercise_ids,
    get_member_profile,
    get_performed_exercises,
    get_preferred_exercises,
    get_safe_exercises,
)
from app.kg.embeddings import get_exercise_vector_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed state
# ---------------------------------------------------------------------------


class RetrievalState(TypedDict, total=False):
    """State flowing through the retrieval sub-graph."""

    # Inputs (required)
    member_id: str
    query: str
    # Populated by lookup_member node
    member_profile: dict[str, Any] | None
    # Populated by run_injury_traversal node
    contraindicated_ids: set[str]
    safe_exercises: list[dict[str, Any]]
    # Populated by run_preference_traversal node
    preferred_exercises: list[dict[str, Any]]
    performed_exercises: list[dict[str, Any]]
    # Populated by run_vector_search node
    vector_docs: list[Any]
    # Populated by assemble node (final output)
    context: ContextSlice | None
    # Error message if any node fails non-fatally
    error: str | None


# ---------------------------------------------------------------------------
# Node factory (captures driver in closure)
# ---------------------------------------------------------------------------


def _make_nodes(
    driver: AsyncDriver,
) -> tuple[
    Any,  # lookup_member
    Any,  # run_injury_traversal
    Any,  # run_preference_traversal
    Any,  # run_vector_search
    Any,  # assemble
]:
    """Return node functions bound to the given Neo4j driver."""

    async def lookup_member(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        profile = await get_member_profile(member_id, driver)
        if profile is None:
            logger.warning("Member '%s' not found in Neo4j — returning empty profile.", member_id)
            profile = {}
        return {"member_profile": profile}

    async def run_injury_traversal(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        contraindicated, safe = await asyncio.gather(
            get_contraindicated_exercise_ids(member_id, driver),
            get_safe_exercises(member_id, driver),
        )
        return {"contraindicated_ids": contraindicated, "safe_exercises": safe}

    async def run_preference_traversal(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        preferred, performed = await asyncio.gather(
            get_preferred_exercises(member_id, driver),
            get_performed_exercises(member_id, driver),
        )
        return {"preferred_exercises": preferred, "performed_exercises": performed}

    async def run_vector_search(state: RetrievalState) -> dict[str, Any]:
        query = state.get("query", "")
        try:
            vector_store = get_exercise_vector_store()
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None, lambda: vector_store.similarity_search(query, k=10)
            )
            return {"vector_docs": docs}
        except Exception as exc:
            logger.warning("Vector search failed: %s", exc)
            return {"vector_docs": [], "error": str(exc)}

    async def assemble(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        query = state.get("query", "")
        # Delegate to context assembler — it handles dedup and budget
        context = await assemble_context(member_id, query, driver)
        return {"context": context}

    return lookup_member, run_injury_traversal, run_preference_traversal, run_vector_search, assemble


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_retrieval_graph(driver: AsyncDriver) -> Any:
    """
    Build and compile the retrieval sub-graph.

    Args:
        driver: An open neo4j.AsyncDriver instance (injected at build time).

    Returns:
        A compiled LangGraph graph. Invoke with:
            result = await graph.ainvoke({"member_id": "...", "query": "..."})
            context_slice = result["context"]
    """
    (
        lookup_member,
        run_injury_traversal,
        run_preference_traversal,
        run_vector_search,
        assemble,
    ) = _make_nodes(driver)

    builder = StateGraph(RetrievalState)

    builder.add_node("lookup_member", lookup_member)
    builder.add_node("run_injury_traversal", run_injury_traversal)
    builder.add_node("run_preference_traversal", run_preference_traversal)
    builder.add_node("run_vector_search", run_vector_search)
    builder.add_node("assemble", assemble)

    builder.set_entry_point("lookup_member")
    builder.add_edge("lookup_member", "run_injury_traversal")
    builder.add_edge("run_injury_traversal", "run_preference_traversal")
    builder.add_edge("run_preference_traversal", "run_vector_search")
    builder.add_edge("run_vector_search", "assemble")
    builder.add_edge("assemble", END)

    return builder.compile()
