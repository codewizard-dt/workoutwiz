"""Generation sub-graph: ContextSlice → WorkoutRecommendation.

Accepts a ContextSlice (from context_assembler) and a user query, calls Claude
via with_structured_output(WorkoutRecommendation) to generate a structured
workout, and returns a WorkoutRecommendation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.config import settings
from app.kg.context_assembler import ContextSlice

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic output models
# ---------------------------------------------------------------------------


class RecommendedExercise(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: int | None = None
    duration_seconds: int | None = None
    weight_kg: float | None = None
    reasoning: str


class WorkoutRecommendation(BaseModel):
    exercises: list[RecommendedExercise]
    overall_reasoning: str
    member_id: str = ""
    skipped_exercise_ids: list[str] = []


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


from typing import TypedDict


class GenerationState(TypedDict, total=False):
    """State flowing through the generation sub-graph."""

    # Inputs (required)
    member_id: str
    query: str
    context: ContextSlice | None

    # Populated by generate_workout node
    recommendation: WorkoutRecommendation | None

    # Set by validate_context when safe_exercises is empty
    fallback_triggered: bool

    # Non-fatal error message
    error: str | None


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_GENERATION_SYSTEM_PROMPT = """\
You are an expert personal fitness coach building a personalized workout plan.

You will be given:
- A member profile (age, goals, fitness level, any injuries)
- A list of SAFE exercises the member can perform (pre-filtered for safety)
- A list of PREFERRED exercises based on the member's history and preferences
- The member's workout request

Your task:
1. Select exercises ONLY from the provided safe exercise list (use their exact IDs).
2. Design a balanced, effective workout matching the member's goals and fitness level.
3. For each chosen exercise, provide sets, reps or duration, optional weight, and clear reasoning.
4. List any safe exercises you deliberately skip and briefly explain why.
5. Provide overall reasoning for the workout design.

IMPORTANT: Never reference exercises outside the provided safe list.
"""


# ---------------------------------------------------------------------------
# Helper: build prompt messages
# ---------------------------------------------------------------------------


def _build_generation_prompt(
    query: str, context: ContextSlice
) -> list[BaseMessage]:
    profile = context.get("member_profile") or {}
    safe_exercises = context.get("safe_exercises") or []
    preferred_exercises = context.get("preferred_exercises") or []

    profile_text = json.dumps(profile, indent=2) if profile else "(not available)"
    safe_text = (
        json.dumps(safe_exercises, indent=2) if safe_exercises else "(none)"
    )
    preferred_text = (
        json.dumps(preferred_exercises, indent=2) if preferred_exercises else "(none)"
    )

    human_content = f"""\
<member_profile>
{profile_text}
</member_profile>

<safe_exercises>
{safe_text}
</safe_exercises>

<preferred_exercises>
{preferred_text}
</preferred_exercises>

<member_request>
{query}
</member_request>

Please design a personalized workout for this member using only the exercises in the safe_exercises list.
"""
    return [
        SystemMessage(content=_GENERATION_SYSTEM_PROMPT),
        HumanMessage(content=human_content),
    ]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------


def _validate_context_node(state: GenerationState) -> dict:
    """Check that safe_exercises is non-empty; trigger fallback if not."""
    context = state.get("context")
    if not context or not context.get("safe_exercises"):
        logger.warning(
            "generation_graph: no safe exercises for member=%s — triggering fallback",
            state.get("member_id"),
        )
        return {"fallback_triggered": True}
    return {"fallback_triggered": False}


async def _generate_workout_node(state: GenerationState) -> dict:
    """Call Claude with structured output to produce a WorkoutRecommendation."""
    context = state["context"]
    member_id = state.get("member_id", "")

    llm = ChatAnthropic(
        model=settings.generator_model,
        api_key=settings.anthropic_api_key,
    ).with_structured_output(WorkoutRecommendation)

    messages = _build_generation_prompt(state["query"], context)

    try:
        recommendation: WorkoutRecommendation = await llm.ainvoke(messages)
        recommendation.member_id = member_id
        return {"recommendation": recommendation}
    except Exception as exc:
        logger.error("generation_graph: LLM call failed: %s", exc)
        return {
            "error": str(exc),
            "recommendation": WorkoutRecommendation(
                exercises=[],
                overall_reasoning="Generation failed due to an error.",
                member_id=member_id,
            ),
        }


def _format_response_node(state: GenerationState) -> dict:
    """Final node — state already has the recommendation; nothing to do."""
    return {}


# ---------------------------------------------------------------------------
# Routing helper
# ---------------------------------------------------------------------------


def _route_after_validate(state: GenerationState) -> str:
    if state.get("fallback_triggered"):
        return END
    return "generate_workout"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_generation_graph() -> Any:
    """Build and compile the generation sub-graph.

    Returns a compiled LangGraph graph. Invoke with::

        result = await graph.ainvoke({
            "member_id": "...",
            "query": "...",
            "context": context_slice,
        })
        recommendation = result["recommendation"]
    """
    builder = StateGraph(GenerationState)

    builder.add_node("validate_context", _validate_context_node)
    builder.add_node("generate_workout", _generate_workout_node)
    builder.add_node("format_response", _format_response_node)

    builder.set_entry_point("validate_context")
    builder.add_conditional_edges(
        "validate_context",
        _route_after_validate,
    )
    builder.add_edge("generate_workout", "format_response")
    builder.add_edge("format_response", END)

    return builder.compile()
