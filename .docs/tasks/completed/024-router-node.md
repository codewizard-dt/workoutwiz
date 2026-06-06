# 024 — Router Node with Structured Output

> **Depends on**: [023-hub-stategraph](023-hub-stategraph.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Replace the stub router node in `hub.py` with a real LLM-based classification node that uses `with_structured_output(RouteDecision)` to classify user intent, and implement the clarification node and its confidence-gated fallback — satisfying the core assessment requirement for LLM-structured-output routing.

## Approach

The router node creates a `ChatAnthropic` instance bound to `RouteDecision` via `with_structured_output()`. It extracts the last user message from state, sends it to the LLM with a system prompt that describes the four intents, and stores the returned `RouteDecision` in state. The existing `_route_selector` conditional edge (task 023) then dispatches based on `route_decision.intent` and `route_decision.confidence`. The clarification node (already stubbed in task 023) is finalized here.

The audit log entry is appended inside the router node: `{tokens_in, tokens_out, model, provider, route, latency_ms, user_id}`.

## Steps

### 1. Implement the LLM router node  <!-- agent: general-purpose -->

Replace `_router_node` in `1-multi-agent/src/workout_wiz/hub.py` with:

```python
import time
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from workout_wiz.state import AgentState, RouteDecision

_ROUTER_SYSTEM_PROMPT = """You are a routing agent for a fitness coaching system.
Classify the user's message into exactly one of these intents:

- COACH: General fitness question, advice, explanation, or motivation (e.g. "What muscles does a deadlift work?", "How many rest days do I need?")
- WORKOUT_GENERATE: The user wants you to create, plan, or suggest a workout (e.g. "Give me a leg day workout", "Plan a 3-day split for me")
- WORKOUT_LOG: The user is recording a workout they already completed (e.g. "I just did 3x10 squats at 100kg", "Log my run: 5km in 25 minutes")
- FALLBACK: The message is unclear, off-topic, or cannot be mapped to the above intents

Return a confidence score (0.0–1.0). Use < 0.6 only when genuinely ambiguous.
"""


def _router_node(state: AgentState) -> dict:
    model_name = os.getenv("ROUTER_MODEL", "claude-haiku-4-5-20251001")
    llm = ChatAnthropic(model=model_name).with_structured_output(RouteDecision)

    # Extract last human message for classification
    last_human = next(
        (m for m in reversed(state["messages"]) if hasattr(m, "type") and m.type == "human"),
        None,
    )
    if last_human is None:
        from workout_wiz.state import Intent
        return {
            "route_decision": RouteDecision(
                intent=Intent.FALLBACK, confidence=0.0, reasoning="No human message found"
            )
        }

    t0 = time.monotonic()
    route_decision: RouteDecision = llm.invoke([
        SystemMessage(content=_ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=last_human.content),
    ])
    latency_ms = int((time.monotonic() - t0) * 1000)

    audit_entry = {
        "event": "router",
        "model": model_name,
        "provider": "anthropic",
        "route": route_decision.intent.value,
        "confidence": route_decision.confidence,
        "latency_ms": latency_ms,
        "user_id": state.get("user_id"),
    }

    return {
        "route_decision": route_decision,
        "audit_log": state.get("audit_log", []) + [audit_entry],
    }
```

- [ ] `_router_node` calls `ChatAnthropic(...).with_structured_output(RouteDecision)`
- [ ] System prompt clearly defines all four intents
- [ ] Audit entry is appended to `state["audit_log"]` with model, route, confidence, latency_ms, user_id
- [ ] Handles the edge case of no human message in state (returns FALLBACK at 0.0 confidence)

### 2. Update hub.py imports  <!-- agent: general-purpose -->

Ensure `hub.py` imports are correct after replacing the stub. The file should import `time`, `os`, `ChatAnthropic`, `SystemMessage`, `HumanMessage` at the top level (not inside the function, for testability). Move the imports from inside the function body to module level.

- [ ] All imports are at module level in `hub.py`
- [ ] No import errors when running `python -c "from workout_wiz.hub import hub"`

### 3. Write router node tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_router.py`. These tests use `unittest.mock` to avoid real LLM calls:

```python
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage

from workout_wiz.state import RouteDecision, Intent


def _make_state(content: str) -> dict:
    return {
        "messages": [HumanMessage(content=content)],
        "route_decision": None,
        "user_id": "test-user",
        "session_id": "test-session",
        "audit_log": [],
    }


def _mock_llm(intent: Intent, confidence: float):
    mock = MagicMock()
    mock.invoke.return_value = RouteDecision(
        intent=intent, confidence=confidence, reasoning="mocked"
    )
    return mock


def test_router_coach_intent():
    from workout_wiz import hub as hub_module
    with patch.object(hub_module, "ChatAnthropic") as mock_cls:
        mock_cls.return_value.with_structured_output.return_value = _mock_llm(Intent.COACH, 0.95)
        from workout_wiz.hub import _router_node
        result = _router_node(_make_state("What muscles does a squat work?"))
    assert result["route_decision"].intent == Intent.COACH
    assert result["route_decision"].confidence == 0.95
    assert len(result["audit_log"]) == 1
    assert result["audit_log"][0]["route"] == "COACH"


def test_router_appends_audit_log():
    from workout_wiz import hub as hub_module
    with patch.object(hub_module, "ChatAnthropic") as mock_cls:
        mock_cls.return_value.with_structured_output.return_value = _mock_llm(Intent.WORKOUT_GENERATE, 0.88)
        from workout_wiz.hub import _router_node
        result = _router_node(_make_state("Plan a push day for me"))
    assert result["audit_log"][0]["latency_ms"] >= 0
    assert result["audit_log"][0]["user_id"] == "test-user"


def test_router_no_human_message():
    from workout_wiz.hub import _router_node
    result = _router_node({
        "messages": [],
        "route_decision": None,
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    })
    assert result["route_decision"].intent == Intent.FALLBACK
    assert result["route_decision"].confidence == 0.0
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_router.py -v`

- [ ] All 3 tests pass (mocked — no real API calls)

## Acceptance Criteria

- [ ] `_router_node` in `hub.py` uses `ChatAnthropic(...).with_structured_output(RouteDecision)`
- [ ] Router system prompt covers all four intents with examples
- [ ] Audit log entry includes: event, model, provider, route, confidence, latency_ms, user_id
- [ ] No-human-message edge case returns FALLBACK at 0.0 confidence without raising exceptions
- [ ] `pytest tests/test_router.py` passes (3/3, mocked)

---
**UAT**: [`.docs/uat/024-router-node.uat.md`](../uat/024-router-node.uat.md)
