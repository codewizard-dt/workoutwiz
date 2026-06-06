# 028 — Workout Generator Sub-Agent

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [024-router-node](024-router-node.md), [027-coach-sub-agent](027-coach-sub-agent.md)

## Objective

Implement the workout generator as a separate, composable `StateGraph` with two LangGraph tools (`search_exercises` and `build_workout`) that have Pydantic input schemas, grounded entirely in `exercises.json` — no hallucinated exercise IDs. Wire it into the hub as the `workout_gen` node.

## Approach

The sub-agent lives in `src/workout_wiz/agents/workout_generator.py`. It is a `StateGraph(AgentState)` with a single `generate_node` that uses a `ToolNode` for tool execution. The two tools are LangGraph-compatible functions decorated with `@tool` and have Pydantic `BaseModel` input schemas with field descriptions so the LLM knows how to call them. The compiled graph is registered in `hub.py` as the `workout_gen` node, replacing `_workout_gen_stub`.

## Steps

### 1. Create workout generator tool schemas  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/agents/workout_generator.py` starting with the two tool input schemas and tool definitions:

```python
import os
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from workout_wiz.state import AgentState
from workout_wiz.exercises import search_exercises as _search_exercises, get_all_exercises


class SearchExercisesInput(BaseModel):
    muscle_groups: Optional[list[str]] = Field(
        default=None,
        description="Muscle groups to target, e.g. ['chest', 'triceps']. Case-insensitive substring match."
    )
    equipment: Optional[list[str]] = Field(
        default=None,
        description="Equipment available, e.g. ['barbell', 'dumbbell']. Use 'bodyweight' for no equipment."
    )
    movement_patterns: Optional[list[str]] = Field(
        default=None,
        description="Movement patterns to include, e.g. ['push', 'hinge', 'squat', 'pull', 'carry']."
    )
    max_results: int = Field(
        default=8,
        description="Maximum number of exercises to return (1-20)."
    )


class BuildWorkoutInput(BaseModel):
    goal: str = Field(
        description="The user's workout goal, e.g. 'upper body strength', 'cardio', 'full body'."
    )
    exercise_ids: list[str] = Field(
        description="List of exercise UUIDs (from search_exercises results) to include in the workout."
    )
    sets: int = Field(
        default=3,
        description="Number of sets per exercise (1-6)."
    )
    rest_seconds: int = Field(
        default=90,
        description="Rest period between sets in seconds."
    )


@tool(args_schema=SearchExercisesInput)
def search_exercises_tool(
    muscle_groups: Optional[list[str]] = None,
    equipment: Optional[list[str]] = None,
    movement_patterns: Optional[list[str]] = None,
    max_results: int = 8,
) -> list[dict]:
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
            "id": e.id,
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
) -> dict:
    """Build a structured workout plan from a list of exercise IDs.
    Returns a workout plan with warmup/main/cooldown phases.
    Only use exercise IDs returned by search_exercises — never invent IDs."""
    all_exercises = {e.id: e for e in get_all_exercises()}
    valid = [all_exercises[eid] for eid in exercise_ids if eid in all_exercises]
    invalid_ids = [eid for eid in exercise_ids if eid not in all_exercises]

    warmup = valid[:2] if len(valid) >= 3 else []
    main = valid[2:] if len(valid) >= 3 else valid
    cooldown = []

    def exercise_to_dict(e):
        return {
            "id": e.id,
            "name": e.name,
            "sets": sets,
            "reps": "10-12" if e.is_reps else None,
            "duration_s": 30 if e.is_duration else None,
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
```

- [ ] `src/workout_wiz/agents/workout_generator.py` exists
- [ ] `SearchExercisesInput` and `BuildWorkoutInput` are Pydantic `BaseModel` subclasses with field descriptions
- [ ] Both tools use `@tool(args_schema=...)` decorator
- [ ] `build_workout_tool` validates exercise IDs against the real dataset (no hallucination)

### 2. Implement the generator StateGraph  <!-- agent: general-purpose -->

Add the `StateGraph` and node logic to `workout_generator.py`:

```python
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


def _should_continue(state: AgentState) -> str:
    """Route to tool executor or end based on last message."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def _generate_node(state: AgentState) -> dict:
    model_name = os.getenv("GENERATOR_MODEL", "claude-haiku-4-5-20251001")
    llm = ChatAnthropic(model=model_name).bind_tools(_TOOLS)
    messages = [SystemMessage(content=_GENERATOR_SYSTEM_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}


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
```

- [ ] `_generate_node` uses `ChatAnthropic(...).bind_tools(_TOOLS)`
- [ ] `_should_continue` routes to `tools` when tool calls are present, else END
- [ ] `ToolNode` handles tool execution
- [ ] Graph has a `generate → tools → generate` loop for multi-turn tool use
- [ ] Module-level `workout_generator_graph` compiled export

### 3. Wire into hub  <!-- agent: general-purpose -->

In `1-multi-agent/src/workout_wiz/hub.py`, replace `_workout_gen_stub` with the imported workout generator graph:

```python
from workout_wiz.agents.workout_generator import workout_generator_graph

# In build_hub_graph():
# Replace: graph.add_node("workout_gen", _workout_gen_stub)
# With:
graph.add_node("workout_gen", workout_generator_graph)
```

Remove `_workout_gen_stub` from `hub.py`.

- [ ] `hub.py` imports `workout_generator_graph`
- [ ] `graph.add_node("workout_gen", workout_generator_graph)` replaces the stub
- [ ] `_workout_gen_stub` removed from `hub.py`

### 4. Write tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_workout_generator.py`:

```python
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from workout_wiz.agents.workout_generator import (
    build_workout_generator_graph,
    search_exercises_tool,
    build_workout_tool,
)


def test_generator_graph_compiles():
    graph = build_workout_generator_graph()
    assert graph.compile() is not None


def test_search_exercises_tool_returns_results():
    results = search_exercises_tool.invoke({"muscle_groups": ["chest"]})
    assert isinstance(results, list)
    assert len(results) > 0
    assert all("id" in r and "name" in r for r in results)


def test_search_exercises_tool_respects_max_results():
    results = search_exercises_tool.invoke({"max_results": 3})
    assert len(results) <= 3


def test_build_workout_tool_valid_ids():
    exercises = search_exercises_tool.invoke({"max_results": 5})
    ids = [e["id"] for e in exercises]
    workout = build_workout_tool.invoke({
        "goal": "full body strength",
        "exercise_ids": ids,
        "sets": 3,
        "rest_seconds": 90,
    })
    assert workout["total_exercises"] == len(ids)
    assert workout["invalid_ids_skipped"] == []
    assert "phases" in workout


def test_build_workout_tool_rejects_invalid_ids():
    workout = build_workout_tool.invoke({
        "goal": "test",
        "exercise_ids": ["00000000-0000-0000-0000-000000000000"],
        "sets": 3,
        "rest_seconds": 60,
    })
    assert workout["total_exercises"] == 0
    assert "00000000-0000-0000-0000-000000000000" in workout["invalid_ids_skipped"]


def test_hub_imports_cleanly():
    from workout_wiz.hub import hub
    assert hub is not None
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_workout_generator.py -v`

- [ ] All 6 tests pass (no real LLM calls required — tools are pure functions)

### 5. Verify hub still compiles  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "from workout_wiz.hub import hub; print('Hub OK')"
```

- [ ] Exits 0 with "Hub OK"

## Acceptance Criteria

- [ ] `src/workout_wiz/agents/workout_generator.py` exists with `search_exercises_tool` and `build_workout_tool`
- [ ] Both tools use Pydantic `BaseModel` input schemas with field descriptions
- [ ] `build_workout_tool` validates exercise IDs against real dataset — invalid IDs listed in `invalid_ids_skipped`, not silently included
- [ ] Generator sub-agent is a `StateGraph` with tool-call loop (generate → tools → generate)
- [ ] `workout_generator_graph` wired into hub as `workout_gen` node (not stub)
- [ ] `pytest tests/test_workout_generator.py` passes (6/6)

---
**UAT**: [`.docs/uat/028-workout-generator-sub-agent.uat.md`](../uat/028-workout-generator-sub-agent.uat.md)
