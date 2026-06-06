# 027 — Coach Sub-Agent Graph

> **Depends on**: [023-hub-stategraph](023-hub-stategraph.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Implement the coach sub-agent as a separate, composable `StateGraph` that answers general fitness questions (form, programming, recovery, nutrition basics). Wire it into the hub by replacing the `_coach_stub` node with a call to the compiled coach graph.

## Approach

The coach sub-agent lives in `src/workout_wiz/agents/coach.py`. It is a minimal `StateGraph(AgentState)` with a single `chat_node` that calls `ChatAnthropic` with a fitness coaching system prompt. The compiled graph is imported into `hub.py` and registered as the `coach` node via a thin wrapper function. Keeping it a separate `StateGraph` (not inlined) satisfies the assessment requirement for composable sub-agent graphs.

## Steps

### 1. Create agents package  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/agents/__init__.py` (empty).

- [ ] `src/workout_wiz/agents/__init__.py` exists

### 2. Create src/workout_wiz/agents/coach.py  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/agents/coach.py`:

```python
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END

from workout_wiz.state import AgentState

_COACH_SYSTEM_PROMPT = """You are an expert fitness coach with deep knowledge of:
- Exercise form, technique, and biomechanics
- Strength training principles (progressive overload, periodization, deload weeks)
- Cardiovascular training (zones, HIIT, steady-state)
- Recovery, sleep, and injury prevention
- Basic sports nutrition (macros, hydration, pre/post workout)

Answer the user's question clearly and concisely. Be specific, evidence-based, and practical.
Do not create workout plans (that's handled by a separate system) — focus on coaching and education.
If asked to log a workout, explain that's handled separately.
"""


def _chat_node(state: AgentState) -> dict:
    model_name = os.getenv("COACH_MODEL", "claude-haiku-4-5-20251001")
    llm = ChatAnthropic(model=model_name)

    messages = [SystemMessage(content=_COACH_SYSTEM_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages)

    return {"messages": [response]}


def build_coach_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("chat", _chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph


coach_graph = build_coach_graph().compile()
```

- [ ] `src/workout_wiz/agents/coach.py` exists
- [ ] `build_coach_graph()` returns a `StateGraph` with a single `chat` node
- [ ] System prompt covers form, programming, recovery, nutrition basics
- [ ] System prompt explicitly NOT generating workout plans (that's the generator's job)
- [ ] Module-level `coach_graph` compiled export

### 3. Wire coach graph into hub  <!-- agent: general-purpose -->

In `1-multi-agent/src/workout_wiz/hub.py`, replace the `_coach_stub` function and its node registration with the imported coach graph:

```python
from workout_wiz.agents.coach import coach_graph

# In build_hub_graph():
# Replace: graph.add_node("coach", _coach_stub)
# With:
graph.add_node("coach", coach_graph)
```

LangGraph accepts a compiled graph as a node — it will invoke the sub-graph and merge state back.

- [ ] `hub.py` imports `coach_graph` from `workout_wiz.agents.coach`
- [ ] `graph.add_node("coach", coach_graph)` replaces the stub
- [ ] `_coach_stub` function removed from `hub.py`

### 4. Write coach sub-agent tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_coach_agent.py`:

```python
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from workout_wiz.agents.coach import build_coach_graph


def test_coach_graph_compiles():
    graph = build_coach_graph()
    compiled = graph.compile()
    assert compiled is not None


def test_coach_returns_ai_message():
    """Coach node should return an AIMessage."""
    mock_response = AIMessage(content="Great question! The squat primarily targets the quadriceps.")
    with patch("workout_wiz.agents.coach.ChatAnthropic") as mock_cls:
        mock_cls.return_value.invoke.return_value = mock_response
        compiled = build_coach_graph().compile()
        result = compiled.invoke({
            "messages": [HumanMessage(content="What muscles does a squat work?")],
            "route_decision": None,
            "user_id": "u1",
            "session_id": "s1",
            "audit_log": [],
        })
    last = result["messages"][-1]
    assert isinstance(last, AIMessage)
    assert "squat" in last.content.lower() or "quadriceps" in last.content.lower()


def test_coach_uses_model_env_var():
    """Coach should pick up COACH_MODEL env var."""
    import os
    with patch.dict(os.environ, {"COACH_MODEL": "claude-opus-4-8"}):
        with patch("workout_wiz.agents.coach.ChatAnthropic") as mock_cls:
            mock_cls.return_value.invoke.return_value = AIMessage(content="ok")
            build_coach_graph().compile().invoke({
                "messages": [HumanMessage(content="hi")],
                "route_decision": None,
                "user_id": None,
                "session_id": None,
                "audit_log": [],
            })
        mock_cls.assert_called_with(model="claude-opus-4-8")
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_coach_agent.py -v`

- [ ] All 3 tests pass (mocked — no real API calls)

### 5. Verify hub still compiles after wiring  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "from workout_wiz.hub import hub; print('Hub OK')"
```

- [ ] `Hub OK` printed, no errors

## Acceptance Criteria

- [ ] `src/workout_wiz/agents/coach.py` exists as a separate `StateGraph` with system prompt
- [ ] `coach_graph` is wired into the hub as the `coach` node (not inlined)
- [ ] `pytest tests/test_coach_agent.py` passes (3/3, mocked)
- [ ] `from workout_wiz.hub import hub` imports without error after wiring

---
**UAT**: [`.docs/uat/027-coach-sub-agent.uat.md`](../uat/027-coach-sub-agent.uat.md)
