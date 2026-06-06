import uuid as _uuid
import uuid
from unittest.mock import MagicMock, patch

from app.agents.hub import build_hub_graph, hub
from app.agents.state import AgentState, RouteDecision, Intent


import pytest


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


@pytest.fixture
def mock_all_llms():
    """Patch all LLM constructors so no real API calls are made."""
    from app.agents.state import RouteDecision, Intent

    def _make_hub_mock():
        m = MagicMock()
        m.with_structured_output.return_value.invoke.return_value = {
            "parsed": RouteDecision(intent=Intent.FALLBACK, confidence=0.0, reasoning="mocked"),
            "raw": MagicMock(usage_metadata={"input_tokens": 0, "output_tokens": 0}),
        }
        return m

    with patch("app.agents.hub.ChatAnthropic", return_value=_make_hub_mock()), \
         patch("app.agents.coach.ChatAnthropic"), \
         patch("app.agents.workout_generator.ChatAnthropic"), \
         patch("app.agents.workout_logger.ChatAnthropic"):
        yield


def test_hub_compiles():
    compiled = build_hub_graph().compile()
    assert compiled is not None


def test_clarification_on_low_confidence(mock_all_llms):
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


def test_fallback_routes_to_clarification(mock_all_llms):
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
