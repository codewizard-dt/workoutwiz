from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.coach import build_coach_graph


def test_coach_graph_compiles():
    graph = build_coach_graph()
    compiled = graph.compile()
    assert compiled is not None


def test_coach_returns_ai_message():
    """Coach node should return an AIMessage."""
    mock_response = AIMessage(content="Great question! The squat primarily targets the quadriceps.")
    with patch("app.agents.coach.ChatAnthropic") as mock_cls:
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
    mock_settings = MagicMock()
    mock_settings.coach_model = "claude-opus-4-8"
    with patch("app.agents.coach.settings", mock_settings):
        with patch("app.agents.coach.ChatAnthropic") as mock_cls:
            mock_cls.return_value.invoke.return_value = AIMessage(content="ok")
            build_coach_graph().compile().invoke({
                "messages": [HumanMessage(content="hi")],
                "route_decision": None,
                "user_id": None,
                "session_id": None,
                "audit_log": [],
            })
        mock_cls.assert_called_with(model="claude-opus-4-8")
