"""Generation sub-graph: ContextSlice → WorkoutRecommendation.

Accepts a ContextSlice (from context_assembler) and a user query, calls Claude
via with_structured_output(WorkoutRecommendation) to generate a structured
workout, and returns a WorkoutRecommendation.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Literal

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
    """Exercise recommendation with source provenance tracking.
    
    Attributes:
        exercise_id: Unique exercise identifier
        name: Exercise name
        sets: Number of sets
        reps: Target repetitions (if applicable)
        duration_seconds: Target duration in seconds (if applicable)
        weight_kg: Weight in kilograms (if applicable)
        reasoning: Rationale for recommending this exercise
        source_type: Origin of recommendation (SAFE_SET, PREFERRED, VECTOR_SEARCH, or FALLBACK)
        source_id: Optional identifier for the source context (query ID, context ID, fallback set ID)
    """
    exercise_id: str
    name: str
    sets: int
    reps: int | None = None
    duration_seconds: int | None = None
    weight_kg: float | None = None
    reasoning: str
    source_type: Literal["SAFE_SET", "PREFERRED", "VECTOR_SEARCH", "FALLBACK"]
    source_id: str | None = None
    provenance: dict | None = None


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

    # Audit log entries appended by each node
    audit_log: list[dict[str, Any]]


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





def _build_provenance(rec: dict, decision: str) -> dict:
    """Build a PROV-O-aligned provenance trace from a contraindicated_provenance record."""
    return {
        "prov_type": "prov:wasDerivedFrom",
        "injury_name": rec.get("injury_name"),
        "disorder_snomed": rec.get("disorder_code"),
        "disorder_name": rec.get("disorder_name"),
        "finding_site_snomed": rec.get("finding_site_code"),
        "finding_site_name": rec.get("finding_site_name"),
        "matched_joint": rec.get("matched_joint"),
        "joint_snomed_code": rec.get("joint_snomed_code"),
        "skos_mapping": {
            "catalog_term": rec.get("matched_joint"),
            "snomed_code": rec.get("joint_snomed_code"),
            "relation": rec.get("skos_relation"),
        },
        "traversal_path": (
            "Member→HAS_INJURY→Injury→MAPS_TO_DISORDER→Disorder"
            "→FINDING_SITE→BodyStructure→PART_OF*→BodyStructure←MAPS_TO←Exercise"
        ),
        "decision": decision,
    }


def _enrich_recommendation_with_sources(
    recommendation: WorkoutRecommendation,
    context: ContextSlice,
) -> WorkoutRecommendation:
    """Post-process recommendation to populate source_type and source_id fields.
    
    For each exercise in the recommendation, traces its origin in the context:
    - If in preferred_exercises: source_type="PREFERRED"
    - Else if in vector_hits: source_type="VECTOR_SEARCH"
    - Else (safe_exercises only): source_type="SAFE_SET"
    
    Updates the recommendation in-place and returns it.
    """
    if not context or not recommendation.exercises:
        return recommendation
    
    # Build ID→index maps for quick lookup
    preferred_ids = {e.get("id"): i for i, e in enumerate(context.get("preferred_exercises", []))}
    vector_ids = {e.get("id"): i for i, e in enumerate(context.get("vector_hits", []))}

    # Index SNOMED provenance by exercise_id for O(1) lookup
    prov_records = context.get("contraindicated_provenance") or []
    prov_by_exercise: dict[str, list[dict]] = {}
    for rec in prov_records:
        prov_by_exercise.setdefault(rec["exercise_id"], []).append(rec)

    # Enrich each exercise
    enriched_exercises = []
    for exercise in recommendation.exercises:
        ex_id = exercise.exercise_id

        # Determine source based on which context list the exercise appears in
        if ex_id in preferred_ids:
            source_type = "PREFERRED"
            source_id = f"preferred_{preferred_ids[ex_id]}"
        elif ex_id in vector_ids:
            source_type = "VECTOR_SEARCH"
            source_id = f"vector_{vector_ids[ex_id]}"
        else:
            source_type = "SAFE_SET"
            source_id = f"safe_{ex_id}"

        # Build PROV-O-aligned provenance trace for this recommended exercise
        prov: dict | None = None
        if ex_id in prov_by_exercise:
            # Exercise appears in contraindicated set — shouldn't reach here after safety gate,
            # but record the path defensively
            rec = prov_by_exercise[ex_id][0]
            prov = _build_provenance(rec, decision="CONTRAINDICATED — passed safety gate unexpectedly")
        else:
            # Recommended exercise — record the positive path
            prov = {
                "prov_type": "prov:wasGeneratedBy",
                "source_type": source_type,
                "traversal_path": "Member→HAS_INJURY→Injury→MAPS_TO_DISORDER→Disorder"
                                  "→FINDING_SITE→BodyStructure→PART_OF*→BodyStructure←MAPS_TO←Exercise",
                "decision": "SAFE — not contraindicated via SNOMED traversal",
            }

        # Create a new RecommendedExercise with source + provenance fields
        enriched = RecommendedExercise(
            exercise_id=exercise.exercise_id,
            name=exercise.name,
            sets=exercise.sets,
            reps=exercise.reps,
            duration_seconds=exercise.duration_seconds,
            weight_kg=exercise.weight_kg,
            reasoning=exercise.reasoning,
            source_type=source_type,
            source_id=source_id,
            provenance=prov,
        )
        enriched_exercises.append(enriched)
    
    # Return a new recommendation with enriched exercises
    return WorkoutRecommendation(
        exercises=enriched_exercises,
        overall_reasoning=recommendation.overall_reasoning,
        member_id=recommendation.member_id,
        skipped_exercise_ids=recommendation.skipped_exercise_ids,
    )


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------


def _validate_context_node(state: GenerationState) -> dict[str, Any]:
    """Check that safe_exercises is non-empty; trigger fallback if not."""
    context = state.get("context")
    if not context or not context.get("safe_exercises"):
        logger.warning(
            "generation_graph: no safe exercises for member=%s — triggering fallback",
            state.get("member_id"),
        )
        return {"fallback_triggered": True}
    return {"fallback_triggered": False}


async def _generate_workout_node(state: GenerationState) -> dict[str, Any]:
    """Call Claude with structured output to produce a WorkoutRecommendation."""
    context = state["context"]
    member_id = state.get("member_id", "")
    model_name = settings.generator_model

    llm = ChatAnthropic(
        model=model_name,
        api_key=settings.anthropic_api_key,
    ).with_structured_output(WorkoutRecommendation, include_raw=True)

    messages = _build_generation_prompt(state["query"], context)  # type: ignore[arg-type]

    t0 = time.monotonic()
    try:
        raw_result = await llm.ainvoke(messages)
        latency_ms = int((time.monotonic() - t0) * 1000)

        # include_raw=True returns {"raw": AIMessage, "parsed": WorkoutRecommendation, ...}
        # Mocks may return WorkoutRecommendation directly — handle both.
        if isinstance(raw_result, dict) and "parsed" in raw_result:
            recommendation: WorkoutRecommendation = raw_result["parsed"]
            raw_response = raw_result.get("raw")
            usage_meta = getattr(raw_response, "usage_metadata", None) or {}
            tokens_in = usage_meta.get("input_tokens", 0)
            tokens_out = usage_meta.get("output_tokens", 0)
        else:
            recommendation = raw_result
            tokens_in = 0
            tokens_out = 0

        recommendation.member_id = member_id
        
        # Enrich recommendation with source information
        recommendation = _enrich_recommendation_with_sources(
            recommendation, context
        )
        
        audit_entry = {
            "event": "kg_generation_llm",
            "model": model_name,
            "provider": "anthropic",
            "latency_ms": latency_ms,
            "user_id": state.get("member_id"),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "exercise_count": len(recommendation.exercises),
        }
        return {
            "recommendation": recommendation,
            "audit_log": state.get("audit_log", []) + [audit_entry],
        }
    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.error("generation_graph: LLM call failed: %s", exc)
        audit_entry = {
            "event": "kg_generation_llm",
            "model": model_name,
            "provider": "anthropic",
            "latency_ms": latency_ms,
            "user_id": state.get("member_id"),
            "tokens_in": 0,
            "tokens_out": 0,
            "exercise_count": 0,
            "error": str(exc),
        }
        return {
            "error": str(exc),
            "recommendation": WorkoutRecommendation(
                exercises=[],
                overall_reasoning="Generation failed due to an error.",
                member_id=member_id,
            ),
            "audit_log": state.get("audit_log", []) + [audit_entry],
        }


def _safety_gate_node(state: GenerationState) -> dict[str, Any]:
    """Post-generation safety gate: remove contraindicated exercises.

    Even if the LLM ignores the safe_exercises constraint, this node
    filters out any exercise whose ID is in context.contraindicated_ids
    before the response is returned. If fewer than 2 safe exercises
    remain, sets fallback_triggered=True so the fallback handler can
    pick it up.
    """
    t0 = time.monotonic()

    if state.get("fallback_triggered") or not state.get("recommendation"):
        latency_ms = int((time.monotonic() - t0) * 1000)
        audit_entry = {
            "event": "kg_generation_safety_gate",
            "latency_ms": latency_ms,
            "user_id": state.get("member_id"),
            "exercise_in": 0,
            "exercise_out": 0,
            "violations_filtered": 0,
            "skipped": True,
        }
        return {"audit_log": state.get("audit_log", []) + [audit_entry]}

    raw_context: dict[str, Any] = dict(state.get("context") or {})
    raw_ids: list[str] = [str(x) for x in raw_context.get("contraindicated_ids", [])]
    contraindicated: set[str] = set(raw_ids)
    rec: WorkoutRecommendation = state["recommendation"]  # type: ignore[assignment]

    exercise_in = len(rec.exercises)
    safe = [e for e in rec.exercises if e.exercise_id not in contraindicated]
    removed = [e.exercise_id for e in rec.exercises if e.exercise_id in contraindicated]
    exercise_out = len(safe)

    latency_ms = int((time.monotonic() - t0) * 1000)
    audit_entry = {
        "event": "kg_generation_safety_gate",
        "latency_ms": latency_ms,
        "user_id": state.get("member_id"),
        "exercise_in": exercise_in,
        "exercise_out": exercise_out,
        "violations_filtered": len(removed),
    }

    result: dict[str, Any] = {"audit_log": state.get("audit_log", []) + [audit_entry]}
    if removed:
        rec = rec.model_copy(
            update={
                "exercises": safe,
                "skipped_exercise_ids": rec.skipped_exercise_ids + removed,
                "overall_reasoning": (
                    rec.overall_reasoning
                    + f" (Removed {len(removed)} contraindicated exercise(s).)"
                ),
            }
        )
        result["recommendation"] = rec

    if len(safe) < 2:
        result["fallback_triggered"] = True

    return result


def _format_response_node(state: GenerationState) -> dict[str, Any]:
    """Final node — state already has the recommendation; nothing to do."""
    return {}


# ---------------------------------------------------------------------------
# Routing helper
# ---------------------------------------------------------------------------


def _route_after_validate(state: GenerationState) -> str:
    if state.get("fallback_triggered"):
        return "fallback"
    return "generate_workout"


def _fallback_node(state: GenerationState) -> dict[str, Any]:
    """Build a minimal WorkoutRecommendation from the top-3 safe exercises.

    Runs when fallback_triggered=True (set by either _validate_context_node
    when no safe exercises exist, or _safety_gate_node when fewer than 2
    exercises survive contraindication filtering).
    """
    t0 = time.monotonic()
    fallback_triggered: bool = state.get("fallback_triggered", True)

    context: dict[str, Any] = dict(state.get("context") or {})
    raw_ids: list[str] = [str(x) for x in context.get("contraindicated_ids", [])]
    contraindicated: set[str] = set(raw_ids)
    all_safe: list[dict[str, Any]] = context.get("safe_exercises", [])
    safe: list[dict[str, Any]] = [e for e in all_safe if e.get("id") not in contraindicated][:3]
    exercises = [
        RecommendedExercise(
            exercise_id=e["id"],
            name=e.get("name", e["id"]),
            sets=3,
            reps=10,
            reasoning="Selected as a safe alternative given your current injury profile.",
            source_type="FALLBACK",
            source_id=f"fallback_{i}",
        )
        for i, e in enumerate(safe)
    ]
    existing_rec: WorkoutRecommendation | None = state.get("recommendation")
    rec = WorkoutRecommendation(
        exercises=exercises,
        overall_reasoning=(
            "Limited exercise options are available due to injury constraints. "
            "These are the safest alternatives from your profile."
        ),
        member_id=state.get("member_id", "") or "",
        skipped_exercise_ids=existing_rec.skipped_exercise_ids if existing_rec else [],
    )

    latency_ms = int((time.monotonic() - t0) * 1000)
    audit_entry = {
        "event": "kg_generation_fallback",
        "latency_ms": latency_ms,
        "user_id": state.get("member_id"),
        "fallback_triggered": fallback_triggered,
        "exercise_count": len(exercises),
    }
    return {
        "recommendation": rec,
        "audit_log": state.get("audit_log", []) + [audit_entry],
    }


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
    builder.add_node("safety_gate", _safety_gate_node)
    builder.add_node("fallback", _fallback_node)
    builder.add_node("format_response", _format_response_node)

    builder.set_entry_point("validate_context")
    builder.add_conditional_edges(
        "validate_context",
        _route_after_validate,
    )
    builder.add_edge("generate_workout", "safety_gate")
    builder.add_conditional_edges(
        "safety_gate",
        lambda s: "fallback" if s.get("fallback_triggered") else "format_response",
    )
    builder.add_edge("fallback", "format_response")
    builder.add_edge("format_response", END)

    return builder.compile()
