"""Integration tests: hub conditional edges dispatch to correct sub-agent branch.

These tests invoke the compiled `hub` graph with mocked LLM calls to verify
that conditional edge routing dispatches to each of the four branches without
real API calls.
"""
import uuid
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.workout_logger import LoggedSet, WorkoutLog
from app.agents.state import Intent, RouteDecision


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


def _make_router_mock(intent: Intent, confidence: float):
    """Return a mock LLM that yields a RouteDecision when invoked."""
    mock = MagicMock()
    mock.invoke.return_value = RouteDecision(
        intent=intent, confidence=confidence, reasoning="test"
    )
    return mock


def _make_coach_mock():
    """Return a mock LLM that yields a coach stub AIMessage."""
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="coach stub response")
    return mock


def _make_gen_mock():
    """Return a mock LLM that yields a workout_gen stub AIMessage (no tool_calls → END)."""
    response = AIMessage(content="workout_gen stub response")
    # Ensure no tool_calls so _should_continue routes to END
    response.tool_calls = []
    mock = MagicMock()
    mock.invoke.return_value = response
    mock.bind_tools.return_value = mock
    return mock


def _make_logger_mock():
    """Return a mock LLM that yields a WorkoutLog (used by workout_logger with_structured_output)."""
    mock = MagicMock()
    mock.invoke.return_value = WorkoutLog(
        raw_input="test input",
        logged_sets=[
            LoggedSet(
                exercise_name="bench press",
                sets=3,
                reps=10,
                weight_kg=80.0,
                match_confidence=0.95,
            )
        ],
    )
    return mock


@contextmanager
def _mock_all_llms(intent: Intent, confidence: float):
    """Patch ChatAnthropic in hub, coach, workout_generator, and workout_logger modules."""
    import app.agents.hub as hub_module
    import app.agents.coach as coach_module
    import app.agents.workout_generator as gen_module
    import app.agents.workout_logger as logger_module

    router_llm = _make_router_mock(intent, confidence)
    coach_llm = _make_coach_mock()
    gen_llm = _make_gen_mock()
    logger_llm = _make_logger_mock()

    with (
        patch.object(hub_module, "ChatAnthropic") as mock_hub_cls,
        patch.object(coach_module, "ChatAnthropic") as mock_coach_cls,
        patch.object(gen_module, "ChatAnthropic") as mock_gen_cls,
        patch.object(logger_module, "ChatAnthropic") as mock_logger_cls,
    ):
        # Router: llm.with_structured_output(RouteDecision).invoke(...)
        mock_hub_cls.return_value.with_structured_output.return_value = router_llm

        # Coach: llm.invoke(messages) → AIMessage
        mock_coach_cls.return_value = coach_llm

        # Generator: llm.bind_tools(_TOOLS).invoke(messages) → AIMessage
        mock_gen_cls.return_value = gen_llm

        # Logger: llm.with_structured_output(WorkoutLog).invoke(...) → WorkoutLog
        mock_logger_cls.return_value.with_structured_output.return_value = logger_llm

        yield


def _invoke_with_route(intent: Intent, confidence: float, message: str) -> dict:
    """Invoke the compiled hub graph with a mocked router returning the given intent/confidence."""
    from app.agents.hub import hub

    with _mock_all_llms(intent, confidence):
        return hub.invoke({
            "messages": [HumanMessage(content=message)],
            "route_decision": None,
            "user_id": "test-user",
            "session_id": "sess-001",
            "audit_log": [],
        })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

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
    # workout_log stub formats output like "Logged N exercise(s)."
    assert "workout_log" in last.lower() or "logged" in last.lower() or "bench" in last.lower()


def test_fallback_routes_to_clarification():
    result = _invoke_with_route(Intent.FALLBACK, 0.7, "banana")
    last = result["messages"][-1].content
    # _clarification_node fires — contains a rephrase prompt
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
    # Should NOT go to clarification — should go to coach stub
    assert "coach" in last.lower() or "stub" in last.lower()
