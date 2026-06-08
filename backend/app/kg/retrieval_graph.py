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
import operator
import time
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph
from neo4j import AsyncDriver

from app.kg.context_assembler import ContextSlice, assemble_context_from_parts
from app.knowledge_graph.traversal import (
    get_avoided_exercises,
    get_biomarkers,
    get_contraindicated_exercise_ids,
    get_contraindicated_provenance,
    get_lab_results,
    get_member_profile,
    get_performed_exercises,
    get_preferred_exercises,
    get_recent_chat_history,
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
    contraindicated_provenance: list[dict[str, Any]]
    safe_exercises: list[dict[str, Any]]
    # Populated by run_preference_traversal node
    preferred_exercises: list[dict[str, Any]]
    performed_exercises: list[dict[str, Any]]
    avoided_exercises: list[dict[str, Any]]
    # Populated by run_vector_search node
    vector_docs: list[Any]
    # Populated by run_biomarker_traversal node
    biomarkers: dict[str, Any] | None
    lab_results: list[dict[str, Any]]
    # Populated by run_chat_history_traversal node
    chat_history: list[dict[str, Any]]
    # Populated by assemble node (final output)
    context: ContextSlice | None
    # Error message if any node fails non-fatally
    error: str | None
    # Observability: optional caller-provided user_id and accumulated audit entries
    user_id: str | None
    audit_log: Annotated[list[dict[str, Any]], operator.add]


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
    Any,  # run_biomarker_traversal
    Any,  # run_chat_history_traversal
    Any,  # assemble
]:
    """Return node functions bound to the given Neo4j driver."""

    async def lookup_member(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        t0 = time.monotonic()
        profile = await get_member_profile(member_id, driver)
        if profile is None:
            logger.warning("Member '%s' not found in Neo4j — returning empty profile.", member_id)
            profile = {}
        latency_ms = int((time.monotonic() - t0) * 1000)
        audit_entry = {
            "event": "retrieval_lookup_member",
            "latency_ms": latency_ms,
            "user_id": state.get("user_id"),
            "result_count": 1 if profile else 0,
        }
        return {
            "member_profile": profile,
            "audit_log": [audit_entry],
        }

    async def run_injury_traversal(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        t0 = time.monotonic()
        contraindicated, safe, provenance = await asyncio.gather(
            get_contraindicated_exercise_ids(member_id, driver),
            get_safe_exercises(member_id, driver),
            get_contraindicated_provenance(member_id, driver),
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        audit_entry = {
            "event": "retrieval_injury_traversal",
            "latency_ms": latency_ms,
            "user_id": state.get("user_id"),
            "result_count": len(safe),
            "constraint_count": len(contraindicated),
            "snomed_provenance_records": len(provenance),
        }
        return {
            "contraindicated_ids": contraindicated,
            "contraindicated_provenance": provenance,
            "safe_exercises": safe,
            "audit_log": [audit_entry],
        }

    async def run_preference_traversal(state: RetrievalState) -> dict[str, Any]:
            member_id = state["member_id"]
            t0 = time.monotonic()
            preferred, performed, avoided = await asyncio.gather(
                get_preferred_exercises(member_id, driver),
                get_performed_exercises(member_id, driver),
                get_avoided_exercises(member_id, driver),
            )
            latency_ms = int((time.monotonic() - t0) * 1000)
            audit_entry = {
                "event": "retrieval_preference_traversal",
                "latency_ms": latency_ms,
                "user_id": state.get("user_id"),
                "result_count": len(preferred) + len(performed),
                "avoided_count": len(avoided),
            }
            return {
                "preferred_exercises": preferred,
                "performed_exercises": performed,
                "avoided_exercises": avoided,
                "audit_log": [audit_entry],
            }

    async def run_vector_search(state: RetrievalState) -> dict[str, Any]:
        query = state.get("query", "")
        t0 = time.monotonic()
        try:
            vector_store = get_exercise_vector_store()
            loop = asyncio.get_event_loop()
            embed_t0 = time.monotonic()
            docs = await loop.run_in_executor(
                None, lambda: vector_store.similarity_search(query, k=10)
            )
            embedding_latency_ms = int((time.monotonic() - embed_t0) * 1000)
            latency_ms = int((time.monotonic() - t0) * 1000)
            audit_entry = {
                "event": "retrieval_vector_search",
                "latency_ms": latency_ms,
                "user_id": state.get("user_id"),
                "result_count": len(docs),
                "embedding_latency_ms": embedding_latency_ms,
            }
            return {
                "vector_docs": docs,
                "audit_log": [audit_entry],
            }
        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("Vector search failed: %s", exc)
            audit_entry = {
                "event": "retrieval_vector_search",
                "latency_ms": latency_ms,
                "user_id": state.get("user_id"),
                "result_count": 0,
                "error": str(exc),
            }
            return {
                "vector_docs": [],
                "error": str(exc),
                "audit_log": [audit_entry],
            }

    async def run_biomarker_traversal(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        t0 = time.monotonic()
        biomarkers, lab_results = await asyncio.gather(
            get_biomarkers(member_id, driver),
            get_lab_results(member_id, driver),
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        audit_entry = {
            "event": "retrieval_biomarker_traversal",
            "latency_ms": latency_ms,
            "user_id": state.get("user_id"),
            "has_biomarkers": biomarkers is not None,
            "lab_result_count": len(lab_results),
        }
        return {
            "biomarkers": biomarkers,
            "lab_results": lab_results,
            "audit_log": [audit_entry],
        }

    async def run_chat_history_traversal(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        t0 = time.monotonic()
        history = await get_recent_chat_history(member_id, driver, limit=10)
        latency_ms = int((time.monotonic() - t0) * 1000)
        audit_entry = {
            "event": "retrieval_chat_history_traversal",
            "latency_ms": latency_ms,
            "user_id": state.get("user_id"),
            "result_count": len(history),
        }
        return {
            "chat_history": history,
            "audit_log": [audit_entry],
        }

    async def assemble(state: RetrievalState) -> dict[str, Any]:
        member_id = state["member_id"]
        query = state.get("query", "")
        # Count inputs before assembling (from state — no re-query needed)
        input_count = (
            len(state.get("safe_exercises") or [])
            + len(state.get("preferred_exercises") or [])
            + len(state.get("vector_docs") or [])
        )
        t0 = time.monotonic()
        # Delegate to context assembler using pre-fetched state — no redundant traversals
        context = await assemble_context_from_parts(
            query=query,
            member_profile=state.get("member_profile"),
            safe_exercises=state.get("safe_exercises") or [],
            preferred_exercises=state.get("preferred_exercises") or [],
            performed_exercises=state.get("performed_exercises") or [],
            avoided_exercises=state.get("avoided_exercises") or [],
            vector_docs=state.get("vector_docs") or [],
            recent_workout_feedback=[],
            member_id=member_id,
            biomarkers=state.get("biomarkers"),
            lab_results=state.get("lab_results") or [],
            chat_history=state.get("chat_history") or [],
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        output_count = len((context or {}).get("safe_exercises", [])) if context else 0
        audit_entry = {
            "event": "retrieval_assemble",
            "latency_ms": latency_ms,
            "user_id": state.get("user_id"),
            "input_count": input_count,
            "output_count": output_count,
        }
        # Stitch SNOMED provenance from injury traversal into the assembled context
        if context is not None:
            context["contraindicated_provenance"] = state.get(
                "contraindicated_provenance", []
            )
        return {
            "context": context,
            "audit_log": [audit_entry],
        }

    return lookup_member, run_injury_traversal, run_preference_traversal, run_vector_search, run_biomarker_traversal, run_chat_history_traversal, assemble


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
        run_biomarker_traversal,
        run_chat_history_traversal,
        assemble,
    ) = _make_nodes(driver)

    builder = StateGraph(RetrievalState)

    builder.add_node("lookup_member", lookup_member)
    builder.add_node("run_injury_traversal", run_injury_traversal)
    builder.add_node("run_preference_traversal", run_preference_traversal)
    builder.add_node("run_vector_search", run_vector_search)
    builder.add_node("run_biomarker_traversal", run_biomarker_traversal)
    builder.add_node("run_chat_history_traversal", run_chat_history_traversal)
    builder.add_node("assemble", assemble)

    builder.set_entry_point("lookup_member")
    builder.add_edge("lookup_member", "run_injury_traversal")
    builder.add_edge("lookup_member", "run_biomarker_traversal")
    builder.add_edge("lookup_member", "run_chat_history_traversal")
    builder.add_edge("run_injury_traversal", "run_preference_traversal")
    builder.add_edge("run_preference_traversal", "run_vector_search")
    builder.add_edge("run_vector_search", "assemble")
    builder.add_edge("run_biomarker_traversal", "assemble")
    builder.add_edge("run_chat_history_traversal", "assemble")
    builder.add_edge("assemble", END)

    return builder.compile()
