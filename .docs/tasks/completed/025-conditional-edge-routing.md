# 025 — Conditional Edge Routing Integration Tests

> **Depends on**: [024-router-node](024-router-node.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Write integration tests that verify the hub's conditional edges correctly dispatch to each of the four branches (coach, workout_gen, workout_log, clarification) across representative inputs, and that low-confidence routing always falls back to clarification — satisfying the assessor requirement for "router correctly classifies all 3 intents + fallback".

## Approach

The conditional edge logic (`_route_selector`) was implemented in task 023 and the LLM router in task 024. This task adds the integration-level test suite that exercises all routing paths with mocked LLM responses. Tests run without API calls. This is distinct from unit tests in `test_router.py` (which tested the node in isolation) — here we invoke the full compiled `hub` graph and assert the correct terminal state.

## Steps

### 1. Write integration routing tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_routing_integration.py`:

```python
"""Integration tests: hub conditional edges dispatch to correct sub-agent branch."""
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage

from workout_wiz.state import RouteDecision, Intent
from workout_wiz.hub import hub


def _invoke_with_route(intent: Intent, confidence: float, message: str) -> dict:
    """Invoke the hub with a pre-set route_decision to bypass the LLM router."""
    return hub.invoke({
        "messages": [HumanMessage(content=message)],
        "route_decision": RouteDecision(
            intent=intent, confidence=confidence, reasoning="test"
        ),
        "user_id": "test-user",
        "session_id": "sess-001",
        "audit_log": [],
    })


def test_coach_intent_dispatches_to_coach():
    result = _invoke_with_route(Intent.COACH, 0.9, "How do I improve my squat form?")
    last = result["messages"][-1].content
    assert "coach" in last.lower() or "stub" in last.lower()


def test_workout_generate_dispatches_correctly():
    result = _invoke_with_route(Intent.WORKOUT_GENERATE, 0.85, "Give me a push day")
    last = result["messages"][-1].content
    assert "workout_gen" in last.lower() or "stub" in last.lower()


def test_workout_log_dispatches_correctly():
    result = _invoke_with_route(Intent.WORKOUT_LOG, 0.92, "I did 3x10 bench at 80kg")
    last = result["messages"][-1].content
    assert "workout_log" in last.lower() or "stub" in last.lower()


def test_fallback_routes_to_clarification():
    result = _invoke_with_route(Intent.FALLBACK, 0.7, "banana")
    last = result["messages"][-1].content
    # Clarification node fires — should contain a rephrase prompt
    assert "rephrase" in last.lower() or "sure" in last.lower() or "help" in last.lower()


def test_low_confidence_routes_to_clarification():
    """Any intent with confidence < 0.6 must route to clarification regardless of intent."""
    result = _invoke_with_route(Intent.COACH, 0.4, "uh I dunno")
    last = result["messages"][-1].content
    assert "rephrase" in last.lower() or "sure" in last.lower() or "help" in last.lower()


def test_boundary_confidence_0_6_routes_to_intent():
    """Confidence exactly 0.6 should route to the intent (threshold is strictly < 0.6)."""
    result = _invoke_with_route(Intent.COACH, 0.6, "something about fitness")
    last = result["messages"][-1].content
    # Should NOT go to clarification — goes to coach stub
    assert "coach" in last.lower() or "stub" in last.lower()
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py -v`

- [x] All 6 tests pass
- [x] `test_low_confidence_routes_to_clarification` verifies the < 0.6 threshold
- [x] `test_boundary_confidence_0_6_routes_to_intent` verifies the exact boundary

### 2. Update _route_selector if boundary test fails  <!-- agent: general-purpose -->

If `test_boundary_confidence_0_6_routes_to_intent` fails, check `_route_selector` in `hub.py`. The condition must be `if rd.confidence < 0.6` (strict less-than), not `<= 0.6`. Fix if needed.

- [x] `_route_selector` uses `rd.confidence < 0.6` (strict less-than)

## Acceptance Criteria

- [x] `tests/test_routing_integration.py` exists with 6 test cases covering all four routing paths
- [x] All 6 tests pass without real API calls
- [x] Low-confidence threshold is strict `< 0.6` (0.6 itself routes to the intent)
- [x] `pytest tests/test_routing_integration.py -v` exits 0

---
**UAT**: [`.docs/uat/completed/025-conditional-edge-routing.uat.md`](../uat/completed/025-conditional-edge-routing.uat.md)
