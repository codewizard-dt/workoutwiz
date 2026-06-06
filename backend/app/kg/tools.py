"""LangChain tool wrappers for the KG retrieval + generation pipeline.

These tools are callable from the hub router agent or any LangChain agent
that needs knowledge-graph-backed workout recommendations.
"""

from __future__ import annotations

import logging

import neo4j
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.config import settings
from app.kg.explainability import explain_skipped_exercise
from app.kg.generation_graph import build_generation_graph
from app.kg.retrieval_graph import build_retrieval_graph

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class KGRecommendInput(BaseModel):
    """Input schema for kg_recommend_tool."""

    member_id: str = Field(description="The member's Neo4j UUID")
    query: str = Field(description="The workout request from the user")


class KGExplainInput(BaseModel):
    """Input schema for kg_explain_tool."""

    member_id: str = Field(description="The member's Neo4j UUID")
    exercise_id: str = Field(description="The exercise UUID that was skipped")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool("kg_recommend", args_schema=KGRecommendInput)
async def kg_recommend_tool(member_id: str, query: str) -> dict[str, object]:
    """Retrieve a personalized, injury-aware workout recommendation from the knowledge graph."""
    driver = neo4j.AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        retrieval_graph = build_retrieval_graph(driver)
        retrieval_result = await retrieval_graph.ainvoke(
            {"member_id": member_id, "query": query}
        )
        context = retrieval_result.get("context")

        generation_graph = build_generation_graph()
        gen_result = await generation_graph.ainvoke(
            {"member_id": member_id, "query": query, "context": context}
        )

        recommendation = gen_result.get("recommendation")
        if recommendation is None:
            logger.warning("Generation graph returned no recommendation for member %s", member_id)
            return {"exercises": [], "overall_reasoning": "No recommendation generated.", "skipped_exercise_ids": []}

        return {
            "exercises": recommendation.exercises,
            "overall_reasoning": recommendation.overall_reasoning,
            "skipped_exercise_ids": recommendation.skipped_exercise_ids,
        }
    except Exception:
        logger.exception("Error in kg_recommend_tool for member %s", member_id)
        raise
    finally:
        await driver.close()


@tool("kg_explain", args_schema=KGExplainInput)
async def kg_explain_tool(member_id: str, exercise_id: str) -> dict[str, object]:
    """Explain why a specific exercise was excluded from a member's workout recommendation."""
    driver = neo4j.AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        explanation, _audit_entry, confidence = await explain_skipped_exercise(
            member_id=member_id,
            exercise_id=exercise_id,
            driver=driver,
        )
        return {"explanation": explanation, "confidence": confidence}
    except Exception:
        logger.exception(
            "Error in kg_explain_tool for member %s, exercise %s", member_id, exercise_id
        )
        raise
    finally:
        await driver.close()


# ---------------------------------------------------------------------------
# Exported tool list
# ---------------------------------------------------------------------------

KG_TOOLS: list[object] = [kg_recommend_tool, kg_explain_tool]
