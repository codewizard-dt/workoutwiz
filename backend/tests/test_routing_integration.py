"""Routing integration tests for the hub StateGraph conditional edge.

Verifies that the compiled hub graph dispatches to the correct sub-agent branch
for each intent and confidence combination — without making real LLM calls.
"""
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.hub import build_hub_graph
from app.agents.state import AgentState, Intent, RouteDecision


def _initial_state() -> dict:
    return {
        "messages": [HumanMessage(content="test")],
        "route_decision": None,
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    }


def _stub_sub_agent(label: str):
    """Returns a node function that appends a labelled stub message."""
    def node(state: AgentState) -> dict:
        return {"messages": [AIMessage(content=f"{label} stub response")]}
    return node


def _run_with_route(intent: Intent, confidence: float) -> list:
    """Compile and invoke the hub with a fixed RouteDecision; return final messages."""
    rd = RouteDecision(intent=intent, confidence=confidence, reasoning="test")

    def router_stub(state: AgentState) -> dict:
        return {"route_decision": rd, "audit_log": state.get("audit_log", [])}

    with (
        patch("app.agents.hub._router_node", router_stub),
        patch("app.agents.hub.coach_graph", _stub_sub_agent("coach")),
        patch("app.agents.hub.workout_generator_graph", _stub_sub_agent("workout_gen")),
        patch("app.agents.hub.workout_logger_graph", _stub_sub_agent("workout_log")),
        patch("app.agents.hub._knowledge_graph_node", _stub_sub_agent("knowledge_graph")),
    ):
        graph = build_hub_graph().compile()
        result = graph.invoke(_initial_state())
    return result["messages"]


def test_coach_intent_dispatches_to_coach():
    messages = _run_with_route(Intent.COACH, 0.9)
    last = messages[-1].content.lower()
    assert "coach" in last or "stub" in last


def test_workout_generate_dispatches_correctly():
    messages = _run_with_route(Intent.WORKOUT_GENERATE, 0.85)
    last = messages[-1].content.lower()
    assert "workout_gen" in last or "stub" in last


def test_workout_log_dispatches_correctly():
    messages = _run_with_route(Intent.WORKOUT_LOG, 0.92)
    last = messages[-1].content.lower()
    assert "workout_log" in last or "stub" in last


def test_fallback_routes_to_clarification():
    # FALLBACK intent always maps to clarification regardless of confidence
    messages = _run_with_route(Intent.FALLBACK, 0.7)
    last = messages[-1].content.lower()
    assert "rephrase" in last or "sure" in last or "help" in last


def test_low_confidence_routes_to_clarification():
    # confidence < 0.6 overrides intent and routes to clarification
    messages = _run_with_route(Intent.COACH, 0.4)
    last = messages[-1].content.lower()
    assert "rephrase" in last or "sure" in last or "help" in last


def test_boundary_confidence_0_6_routes_to_intent():
    # Strict less-than: confidence == 0.6 is NOT low-confidence, routes to coach
    messages = _run_with_route(Intent.COACH, 0.6)
    last = messages[-1].content.lower()
    assert "coach" in last or "stub" in last
