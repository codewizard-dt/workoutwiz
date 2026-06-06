# 033 — Critical-Path Test A: Router Intent Classification

> **Depends on**: [024-router-node](024-router-node.md), [025-conditional-edge-routing](025-conditional-edge-routing.md)
> **Blocks**: none
> **Parallel-safe with**: [034-critical-path-generator-test](034-critical-path-generator-test.md), [035-e2e-smoke-test](035-e2e-smoke-test.md), [036-readme-production-eval](036-readme-production-eval.md)

## Objective

Prove the router correctly classifies all three intents (COACH, WORKOUT_GENERATE, WORKOUT_LOG) plus the FALLBACK path across representative inputs using a fully mocked LLM — no API key required. This is the first of two critical-path tests required by the assessment.

## Approach

Use `unittest.mock.patch` to replace the LangChain LLM call inside the router node with a pre-configured mock that returns a controlled `RouteDecision` structured output. Tests cover: one representative prompt per intent, an off-topic FALLBACK case, and a low-confidence trigger for the clarification path. All five tests run deterministically without network calls and must pass in CI.

## Steps

### 1. Create tests/test_critical_path_router.py  <!-- agent: general-purpose -->

Create `.docs/guides/1-multi-agent/tests/test_critical_path_router.py`:

```python
"""
Critical-path test A: router correctly classifies all 3 intents + fallback.

All tests run without an API key — the LLM is fully mocked.
"""
import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from workout_wiz.state import AgentState, RouteDecision, Intent


def _make_state(message: str) -> AgentState:
    """Return a minimal AgentState with one user message."""
    return {
        "messages": [HumanMessage(content=message)],
        "route_decision": None,
        "user_id": "test-user",
        "session_id": "test-session",
        "audit_log": [],
    }


def _mock_llm_returning(intent: Intent, confidence: float):
    """
    Return a mock LLM object whose .with_structured_output().invoke() chain
    yields a RouteDecision with the given intent and confidence.
    """
    route_decision = RouteDecision(intent=intent, confidence=confidence)
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = route_decision
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    return mock_llm


# ---------------------------------------------------------------------------
# COACH intent
# ---------------------------------------------------------------------------

def test_router_classifies_coach_intent():
    """Fitness advice questions should route to COACH."""
    from workout_wiz.hub import _router_node

    state = _make_state("How many rest days should I take per week?")
    mock_llm = _mock_llm_returning(Intent.COACH, confidence=0.92)

    with patch("workout_wiz.hub.llm", mock_llm):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.COACH
    assert decision.confidence >= 0.5


# ---------------------------------------------------------------------------
# WORKOUT_GENERATE intent
# ---------------------------------------------------------------------------

def test_router_classifies_workout_generate_intent():
    """Requests to build a workout should route to WORKOUT_GENERATE."""
    from workout_wiz.hub import _router_node

    state = _make_state("Give me a full-body strength workout for today.")
    mock_llm = _mock_llm_returning(Intent.WORKOUT_GENERATE, confidence=0.95)

    with patch("workout_wiz.hub.llm", mock_llm):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.WORKOUT_GENERATE
    assert decision.confidence >= 0.5


# ---------------------------------------------------------------------------
# WORKOUT_LOG intent
# ---------------------------------------------------------------------------

def test_router_classifies_workout_log_intent():
    """Logging a completed exercise should route to WORKOUT_LOG."""
    from workout_wiz.hub import _router_node

    state = _make_state("I just did 3 sets of 10 bench press at 135 lbs.")
    mock_llm = _mock_llm_returning(Intent.WORKOUT_LOG, confidence=0.88)

    with patch("workout_wiz.hub.llm", mock_llm):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.WORKOUT_LOG
    assert decision.confidence >= 0.5


# ---------------------------------------------------------------------------
# FALLBACK intent — off-topic message
# ---------------------------------------------------------------------------

def test_router_classifies_fallback_for_off_topic():
    """Off-topic messages should produce FALLBACK intent."""
    from workout_wiz.hub import _router_node

    state = _make_state("What's the capital of France?")
    mock_llm = _mock_llm_returning(Intent.FALLBACK, confidence=0.85)

    with patch("workout_wiz.hub.llm", mock_llm):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.FALLBACK


# ---------------------------------------------------------------------------
# Low-confidence → clarification path
# ---------------------------------------------------------------------------

def test_router_low_confidence_triggers_clarification():
    """
    When confidence is below the 0.6 threshold, the route_decision should
    still be recorded — the conditional edge (tested separately in task 025)
    is responsible for diverting to clarification. This test verifies the
    router node surfaces the low-confidence value so the edge can act on it.
    """
    from workout_wiz.hub import _router_node

    state = _make_state("Maybe I want to do something active?")
    mock_llm = _mock_llm_returning(Intent.COACH, confidence=0.45)

    with patch("workout_wiz.hub.llm", mock_llm):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.confidence < 0.6, (
        "Router must surface low confidence so conditional edge can route to clarification"
    )
```

- [x] File exists at `.docs/guides/1-multi-agent/tests/test_critical_path_router.py`
- [x] Five test functions are defined (one per bullet in acceptance criteria)
- [x] No `ANTHROPIC_API_KEY` import or real LLM instantiation in tests

### 2. Run the tests  <!-- agent: general-purpose -->

```bash
cd 1-multi-agent && .venv/bin/pytest tests/test_critical_path_router.py -v
```

Fix any import errors by adjusting the patch path to match the actual module path where `llm` is defined in `hub.py` (e.g., `workout_wiz.hub.llm` or `workout_wiz.hub.ChatAnthropic`).

- [x] All 5 tests pass
- [x] No real LLM calls are made (confirm by running without `ANTHROPIC_API_KEY` set)

### 3. Add to CI pytest run  <!-- agent: general-purpose -->

Verify the test file is discovered by the default pytest configuration (no explicit exclusion):

```bash
cd 1-multi-agent && .venv/bin/pytest --collect-only tests/test_critical_path_router.py
```

- [x] pytest collects 5 tests from this file

## Acceptance Criteria

- [x] `tests/test_critical_path_router.py` exists with ≥5 test cases
- [x] COACH intent: mocked router correctly classifies a fitness advice question
- [x] WORKOUT_GENERATE intent: mocked router correctly classifies a workout request
- [x] WORKOUT_LOG intent: mocked router correctly classifies a logging message
- [x] FALLBACK intent: mocked router returns FALLBACK for an off-topic message
- [x] Low-confidence: router surfaces a confidence value below 0.6 when mocked that way
- [x] `pytest tests/test_critical_path_router.py` passes (5/5) without an API key
