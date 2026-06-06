"""
Critical-path test A: router correctly classifies all 3 intents + fallback.

All tests run without an API key — the LLM is fully mocked.

Note on mocking: _router_node instantiates ChatAnthropic locally, so we
patch `app.agents.hub.ChatAnthropic` (the class) rather than a module-level
`llm` variable.  The mock must satisfy the two-step call chain:
    ChatAnthropic(model=...).with_structured_output(...).invoke(...) -> RouteDecision
"""
import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from app.agents.state import AgentState, RouteDecision, Intent


def _make_state(message: str) -> AgentState:
    """Return a minimal AgentState with one user message."""
    return {
        "messages": [HumanMessage(content=message)],
        "route_decision": None,
        "user_id": "test-user",
        "session_id": "test-session",
        "audit_log": [],
    }


def _mock_anthropic_returning(intent: Intent, confidence: float):
    """
    Return a mock ChatAnthropic class whose instantiation → with_structured_output()
    → invoke() chain yields a dict with 'parsed' = RouteDecision(...).

    Because _router_node uses include_raw=True and handles the dict form:
        {"parsed": RouteDecision, "raw": ...}
    the mock must return that shape.
    """
    route_decision = RouteDecision(
        intent=intent,
        confidence=confidence,
        reasoning="mocked reasoning for test",
    )
    mock_invoke_result = {"parsed": route_decision, "raw": MagicMock()}

    mock_structured = MagicMock()
    mock_structured.invoke.return_value = mock_invoke_result

    mock_instance = MagicMock()
    mock_instance.with_structured_output.return_value = mock_structured

    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls


# ---------------------------------------------------------------------------
# COACH intent
# ---------------------------------------------------------------------------

def test_router_classifies_coach_intent():
    """Fitness advice questions should route to COACH."""
    from app.agents.hub import _router_node

    state = _make_state("How many rest days should I take per week?")
    mock_cls = _mock_anthropic_returning(Intent.COACH, confidence=0.92)

    with patch("app.agents.hub.ChatAnthropic", mock_cls):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.COACH
    assert decision.confidence >= 0.5


# ---------------------------------------------------------------------------
# WORKOUT_GENERATE intent
# ---------------------------------------------------------------------------

def test_router_classifies_workout_generate_intent():
    """Requests to build a workout should route to WORKOUT_GENERATE."""
    from app.agents.hub import _router_node

    state = _make_state("Give me a full-body strength workout for today.")
    mock_cls = _mock_anthropic_returning(Intent.WORKOUT_GENERATE, confidence=0.95)

    with patch("app.agents.hub.ChatAnthropic", mock_cls):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.WORKOUT_GENERATE
    assert decision.confidence >= 0.5


# ---------------------------------------------------------------------------
# WORKOUT_LOG intent
# ---------------------------------------------------------------------------

def test_router_classifies_workout_log_intent():
    """Logging a completed exercise should route to WORKOUT_LOG."""
    from app.agents.hub import _router_node

    state = _make_state("I just did 3 sets of 10 bench press at 135 lbs.")
    mock_cls = _mock_anthropic_returning(Intent.WORKOUT_LOG, confidence=0.88)

    with patch("app.agents.hub.ChatAnthropic", mock_cls):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.intent == Intent.WORKOUT_LOG
    assert decision.confidence >= 0.5


# ---------------------------------------------------------------------------
# FALLBACK intent — off-topic message
# ---------------------------------------------------------------------------

def test_router_classifies_fallback_for_off_topic():
    """Off-topic messages should produce FALLBACK intent."""
    from app.agents.hub import _router_node

    state = _make_state("What's the capital of France?")
    mock_cls = _mock_anthropic_returning(Intent.FALLBACK, confidence=0.85)

    with patch("app.agents.hub.ChatAnthropic", mock_cls):
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
    from app.agents.hub import _router_node

    state = _make_state("Maybe I want to do something active?")
    mock_cls = _mock_anthropic_returning(Intent.COACH, confidence=0.45)

    with patch("app.agents.hub.ChatAnthropic", mock_cls):
        result = _router_node(state)

    decision: RouteDecision = result["route_decision"]
    assert decision.confidence < 0.6, (
        "Router must surface low confidence so conditional edge can route to clarification"
    )
