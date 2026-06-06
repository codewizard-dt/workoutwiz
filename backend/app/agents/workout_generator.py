import time
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from app.agents.exercises import get_all_exercises
from app.agents.exercises import search_exercises as _search_exercises
from app.agents.state import AgentState
from app.config import settings


class SearchExercisesInput(BaseModel):
    muscle_groups: list[str] | None = Field(
        default=None,
        description="Muscle groups to target, e.g. ['chest', 'triceps']. Case-insensitive substring match.",
    )
    equipment: list[str] | None = Field(
        default=None,
        description="Equipment available, e.g. ['barbell', 'dumbbell']. Use 'bodyweight' for no equipment.",
    )
    movement_patterns: list[str] | None = Field(
        default=None,
        description="Movement patterns to include, e.g. ['push', 'hinge', 'squat', 'pull', 'carry'].",
    )
    max_results: int = Field(
        default=8,
        description="Maximum number of exercises to return (1-20).",
    )


class BuildWorkoutInput(BaseModel):
    goal: str = Field(
        description="The user's workout goal, e.g. 'upper body strength', 'cardio', 'full body'.",
    )
    exercise_ids: list[str] = Field(
        description="List of exercise UUIDs (from search_exercises results) to include in the workout.",
    )
    sets: int = Field(
        default=3,
        description="Number of sets per exercise (1-6).",
    )
    rest_seconds: int = Field(
        default=90,
        description="Rest period between sets in seconds.",
    )


@tool(args_schema=SearchExercisesInput)
def search_exercises_tool(
    muscle_groups: list[str] | None = None,
    equipment: list[str] | None = None,
    movement_patterns: list[str] | None = None,
    max_results: int = 8,
) -> list[dict[str, Any]]:
    """Search the exercise database by muscle group, equipment, or movement pattern.
    Returns a list of matching exercises with their IDs, names, and key properties.
    Always call this before build_workout to get valid exercise IDs."""
    exercises = _search_exercises(
        muscle_groups=muscle_groups,
        equipment=equipment,
        movement_patterns=movement_patterns,
        max_results=max_results,
    )
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "muscle_groups": e.muscle_groups,
            "equipment_required": e.equipment_required,
            "is_reps": e.is_reps,
            "is_duration": e.is_duration,
            "supports_weight": e.supports_weight,
        }
        for e in exercises
    ]


@tool(args_schema=BuildWorkoutInput)
def build_workout_tool(
    goal: str,
    exercise_ids: list[str],
    sets: int = 3,
    rest_seconds: int = 90,
) -> dict[str, Any]:
    """Build a structured workout plan from a list of exercise IDs.
    Returns a workout plan with warmup/main/cooldown phases.
    Only use exercise IDs returned by search_exercises — never invent IDs."""
    all_exercises = {str(e.id): e for e in get_all_exercises()}
    valid = [all_exercises[eid] for eid in exercise_ids if eid in all_exercises]
    invalid_ids = [eid for eid in exercise_ids if eid not in all_exercises]

    warmup = valid[:2] if len(valid) >= 3 else []
    main = valid[2:] if len(valid) >= 3 else valid
    cooldown: list[dict[str, Any]] = []

    def exercise_to_dict(e: object) -> dict[str, Any]:
        return {
            "id": str(e.id),  # type: ignore[attr-defined]
            "name": e.name,  # type: ignore[attr-defined]
            "sets": sets,
            "reps": "10-12" if e.is_reps else None,  # type: ignore[attr-defined]
            "duration_s": 30 if e.is_duration else None,  # type: ignore[attr-defined]
            "rest_s": rest_seconds,
        }

    return {
        "goal": goal,
        "phases": {
            "warmup": [exercise_to_dict(e) for e in warmup],
            "main": [exercise_to_dict(e) for e in main],
            "cooldown": cooldown,
        },
        "total_exercises": len(valid),
        "invalid_ids_skipped": invalid_ids,
    }


_GENERATOR_SYSTEM_PROMPT = """You are a workout planning assistant. Your job is to create a workout plan based on the user's request.

Steps:
1. Call search_exercises to find relevant exercises matching the user's goals and available equipment.
2. Select 4-8 exercises from the results.
3. Call build_workout with the selected exercise IDs to produce the final plan.
4. Present the workout plan to the user in a clear, readable format.

CRITICAL: Only use exercise IDs returned by search_exercises. Never invent or guess exercise IDs.
If the user asks for equipment you don't find results for, fall back to bodyweight exercises.
"""

_TOOLS = [search_exercises_tool, build_workout_tool]


def _should_continue(state: AgentState) -> Any:
    """Route to tool executor or end based on last message."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def _generate_node(state: AgentState) -> dict[str, Any]:
    model_name = settings.generator_model
    llm = ChatAnthropic(model=model_name).bind_tools(_TOOLS)
    messages = [SystemMessage(content=_GENERATOR_SYSTEM_PROMPT)] + list(state["messages"])
    t0 = time.monotonic()
    response = llm.invoke(messages)
    latency_ms = int((time.monotonic() - t0) * 1000)

    usage = getattr(response, "response_metadata", {})
    audit_entry = {
        "event": "generator",
        "model": model_name,
        "provider": "anthropic",
        "latency_ms": latency_ms,
        "tokens_in": usage.get("usage", {}).get("input_tokens", 0),
        "tokens_out": usage.get("usage", {}).get("output_tokens", 0),
    }

    return {
        "messages": [response],
        "audit_log": list(state.get("audit_log", [])) + [audit_entry],
    }


def build_workout_generator_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    tool_node = ToolNode(_TOOLS)

    graph.add_node("generate", _generate_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "generate")
    graph.add_conditional_edges("generate", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "generate")

    return graph


workout_generator_graph = build_workout_generator_graph().compile()
