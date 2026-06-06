# 023 — Hub StateGraph with Typed State and Explicit Edges

> **Depends on**: [021-shared-state-and-route-schema](021-shared-state-and-route-schema.md), [022-exercise-data-loader](022-exercise-data-loader.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Implement the central hub as a LangGraph `StateGraph` with `AgentState` typed state, explicit node registrations, and conditional edges that dispatch to the correct sub-agent based on the router node's output. The graph must be compilable and invokable even before sub-agents are wired (stubs are fine in this task).

## Approach

The hub graph lives in `src/workout_wiz/hub.py`. It uses `StateGraph(AgentState)` as the container. Nodes are registered by name (`"router"`, `"coach"`, `"workout_gen"`, `"workout_log"`, `"clarification"`). Conditional edges use a `_route_selector` function that reads `state["route_decision"]` and returns the target node name. Sub-agent nodes in this task are stubs that echo back a placeholder message — they will be replaced in tasks 025–027.

## Steps

### 1. Create src/workout_wiz/hub.py  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/hub.py`:

```python
from langgraph.graph import StateGraph, START, END

from workout_wiz.state import AgentState, Intent


def _router_node(state: AgentState) -> dict:
    """Placeholder — replaced in task 024 with LLM-based routing."""
    return {}


def _clarification_node(state: AgentState) -> dict:
    """Returns a message asking the user to rephrase when confidence < 0.6."""
    from langchain_core.messages import AIMessage
    return {
        "messages": [AIMessage(content=(
            "I'm not sure what you're asking. Could you rephrase? "
            "I can help with fitness coaching, creating a workout plan, or logging a completed workout."
        ))]
    }


def _coach_stub(state: AgentState) -> dict:
    """Stub — replaced by coach sub-agent graph in task 025."""
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="[coach stub] Not yet implemented.")]}


def _workout_gen_stub(state: AgentState) -> dict:
    """Stub — replaced by workout generator sub-agent graph in task 026."""
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="[workout_gen stub] Not yet implemented.")]}


def _workout_log_stub(state: AgentState) -> dict:
    """Stub — replaced by workout logger sub-agent graph in task 027."""
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="[workout_log stub] Not yet implemented.")]}


def _route_selector(state: AgentState) -> str:
    """Conditional edge: dispatch to sub-agent or clarification based on route_decision."""
    rd = state.get("route_decision")
    if rd is None or rd.confidence < 0.6:
        return "clarification"
    intent_to_node = {
        Intent.COACH: "coach",
        Intent.WORKOUT_GENERATE: "workout_gen",
        Intent.WORKOUT_LOG: "workout_log",
        Intent.FALLBACK: "clarification",
    }
    return intent_to_node.get(rd.intent, "clarification")


def build_hub_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("router", _router_node)
    graph.add_node("clarification", _clarification_node)
    graph.add_node("coach", _coach_stub)
    graph.add_node("workout_gen", _workout_gen_stub)
    graph.add_node("workout_log", _workout_log_stub)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_selector,
        {
            "coach": "coach",
            "workout_gen": "workout_gen",
            "workout_log": "workout_log",
            "clarification": "clarification",
        },
    )
    graph.add_edge("coach", END)
    graph.add_edge("workout_gen", END)
    graph.add_edge("workout_log", END)
    graph.add_edge("clarification", END)

    return graph


# Compiled singleton — import this for production use
hub = build_hub_graph().compile()
```

- [x] `src/workout_wiz/hub.py` exists
- [x] `build_hub_graph()` returns a `StateGraph` with 5 nodes: router, clarification, coach, workout_gen, workout_log
- [x] `_route_selector` returns `"clarification"` when `confidence < 0.6` or intent is `FALLBACK`
- [x] All nodes connect to `END`
- [x] Module-level `hub` compiled graph is exported

### 2. Verify graph compiles  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "from workout_wiz.hub import hub; print('Hub compiled:', hub)"
```

- [x] Exits 0 with hub object printed (no import or compilation errors)

### 3. Write graph structure test  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_hub.py`:

```python
from workout_wiz.hub import build_hub_graph, hub
from workout_wiz.state import AgentState, RouteDecision, Intent


def test_hub_compiles():
    compiled = build_hub_graph().compile()
    assert compiled is not None


def test_clarification_on_low_confidence():
    """Router stub returns no route_decision → should route to clarification."""
    from langchain_core.messages import HumanMessage
    result = hub.invoke({
        "messages": [HumanMessage(content="asdf")],
        "route_decision": None,
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    })
    # With stub router (no LLM), route_decision stays None → clarification fires
    last_msg = result["messages"][-1].content
    assert "rephrase" in last_msg.lower() or "sure" in last_msg.lower()


def test_fallback_routes_to_clarification():
    """Explicit FALLBACK intent should route to clarification."""
    from langchain_core.messages import HumanMessage
    result = hub.invoke({
        "messages": [HumanMessage(content="tell me a joke")],
        "route_decision": RouteDecision(
            intent=Intent.FALLBACK, confidence=0.8, reasoning="off-topic"
        ),
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    })
    last_msg = result["messages"][-1].content
    assert "stub" not in last_msg  # stub nodes shouldn't fire for FALLBACK
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_hub.py -v`

- [x] All 3 tests pass

## Acceptance Criteria

- [x] `src/workout_wiz/hub.py` exists with `build_hub_graph()` and compiled `hub` export
- [x] Graph has 5 named nodes with explicit edges (no implicit ordering)
- [x] `_route_selector` routes low-confidence and FALLBACK to clarification
- [x] `pytest tests/test_hub.py` passes (3/3)
- [x] Module imports without error

---
**UAT**: [`.docs/uat/023-hub-stategraph.uat.md`](../uat/023-hub-stategraph.uat.md)
