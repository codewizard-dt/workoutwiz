import uuid
from unittest.mock import MagicMock, patch

import pytest
import app.agents.hub as hub_module
from langchain_core.messages import HumanMessage
from app.agents.hub import hub
from app.agents.state import RouteDecision, Intent


@pytest.fixture(autouse=True)
def populate_exercise_cache():
    from app.agents import exercises as ex_module
    from app.models.exercise import Exercise as ExModel
    fake = MagicMock(spec=ExModel)
    fake.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    fake.name = "Squat"
    fake.muscle_groups = ["quadriceps"]
    fake.equipment_required = ["barbell"]
    fake.movement_patterns = ["squat"]
    fake.is_reps = True
    fake.is_duration = False
    fake.supports_weight = True
    fake.priority_tier = 1
    ex_module._cache = [fake]
    yield
    ex_module._cache = []


def _mock_router(route_decision: RouteDecision):
    """Return a patched ChatAnthropic that makes the router emit the given RouteDecision."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = route_decision
    mock_cls = MagicMock()
    mock_cls.return_value.with_structured_output.return_value = mock_llm
    return mock_cls


def test_clarification_message_format():
    """Clarification node should list all three capabilities."""
    rd = RouteDecision(intent=Intent.FALLBACK, confidence=0.3, reasoning="completely off-topic")
    with patch.object(hub_module, "ChatAnthropic", _mock_router(rd)):
        result = hub.invoke({
            "messages": [HumanMessage(content="what?")],
            "route_decision": None,
            "user_id": "u1",
            "session_id": "s1",
            "audit_log": [],
        })
    last = result["messages"][-1].content
    assert "coaching" in last.lower() or "fitness" in last.lower()
    assert "workout" in last.lower()
    assert "logging" in last.lower() or "log" in last.lower()
    assert "rephrase" in last.lower() or "?" in last


def test_clarification_appends_audit():
    """Clarification node should add an audit entry."""
    rd = RouteDecision(intent=Intent.COACH, confidence=0.4, reasoning="ambiguous")
    with patch.object(hub_module, "ChatAnthropic", _mock_router(rd)):
        result = hub.invoke({
            "messages": [HumanMessage(content="hmm")],
            "route_decision": None,
            "user_id": "u2",
            "session_id": "s2",
            "audit_log": [],
        })
    clarification_entries = [e for e in result["audit_log"] if e.get("event") == "clarification"]
    assert len(clarification_entries) == 1
    assert clarification_entries[0]["trigger"] == "low_confidence"
    assert clarification_entries[0]["confidence"] == 0.4


def test_clarification_includes_reasoning():
    """Reasoning from route_decision should appear in the clarification message."""
    rd = RouteDecision(intent=Intent.FALLBACK, confidence=0.1, reasoning="no recognizable keywords")
    with patch.object(hub_module, "ChatAnthropic", _mock_router(rd)):
        result = hub.invoke({
            "messages": [HumanMessage(content="xyz")],
            "route_decision": None,
            "user_id": None,
            "session_id": None,
            "audit_log": [],
        })
    last = result["messages"][-1].content
    assert "no recognizable keywords" in last
