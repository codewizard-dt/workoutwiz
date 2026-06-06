from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from app.agents.state import Intent, RouteDecision


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
    from app.agents import hub as hub_module

    with patch.object(hub_module, "ChatAnthropic") as mock_cls:
        mock_cls.return_value.with_structured_output.return_value = _mock_llm(Intent.COACH, 0.95)
        from app.agents.hub import _router_node

        result = _router_node(_make_state("What muscles does a squat work?"))
    assert result["route_decision"].intent == Intent.COACH
    assert result["route_decision"].confidence == 0.95
    assert len(result["audit_log"]) == 1
    assert result["audit_log"][0]["route"] == "COACH"


def test_router_appends_audit_log():
    from app.agents import hub as hub_module

    with patch.object(hub_module, "ChatAnthropic") as mock_cls:
        mock_cls.return_value.with_structured_output.return_value = _mock_llm(
            Intent.WORKOUT_GENERATE, 0.88
        )
        from app.agents.hub import _router_node

        result = _router_node(_make_state("Plan a push day for me"))
    assert result["audit_log"][0]["latency_ms"] >= 0
    assert result["audit_log"][0]["user_id"] == "test-user"


def test_router_no_human_message():
    from app.agents.hub import _router_node

    result = _router_node(
        {
            "messages": [],
            "route_decision": None,
            "user_id": None,
            "session_id": None,
            "audit_log": [],
        }
    )
    assert result["route_decision"].intent == Intent.FALLBACK
    assert result["route_decision"].confidence == 0.0
