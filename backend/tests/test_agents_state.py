from app.agents.state import AgentState, RouteDecision, Intent


def test_route_decision_valid():
    rd = RouteDecision(intent=Intent.COACH, confidence=0.9, reasoning="General fitness question")
    assert rd.intent == Intent.COACH
    assert rd.confidence == 0.9


def test_route_decision_confidence_bounds():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RouteDecision(intent=Intent.COACH, confidence=1.5, reasoning="too high")


def test_intent_values():
    assert set(Intent) == {Intent.COACH, Intent.WORKOUT_GENERATE, Intent.WORKOUT_LOG, Intent.FALLBACK}
