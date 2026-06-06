import time

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.workout_generator import workout_generator_graph
from app.agents.workout_logger import workout_logger_graph
from app.agents.state import AgentState, Intent, RouteDecision
from app.agents.coach import coach_graph
from app.config import settings


_ROUTER_SYSTEM_PROMPT = """You are a routing agent for a fitness coaching system.
Classify the user's message into exactly one of these intents:

- COACH: General fitness question, advice, explanation, or motivation (e.g. "What muscles does a deadlift work?", "How many rest days do I need?")
- WORKOUT_GENERATE: The user wants you to create, plan, or suggest a workout (e.g. "Give me a leg day workout", "Plan a 3-day split for me")
- WORKOUT_LOG: The user is recording a workout they already completed (e.g. "I just did 3x10 squats at 100kg", "Log my run: 5km in 25 minutes")
- FALLBACK: The message is unclear, off-topic, or cannot be mapped to the above intents

Return a confidence score (0.0–1.0). Use < 0.6 only when genuinely ambiguous.
"""


def _router_node(state: AgentState) -> dict:
    """LLM-based routing node using ChatAnthropic with_structured_output(RouteDecision)."""
    model_name = settings.router_model
    llm = ChatAnthropic(model=model_name).with_structured_output(RouteDecision, include_raw=True)

    # Extract last human message for classification
    last_human = next(
        (m for m in reversed(state["messages"]) if hasattr(m, "type") and m.type == "human"),
        None,
    )
    if last_human is None:
        return {
            "route_decision": RouteDecision(
                intent=Intent.FALLBACK, confidence=0.0, reasoning="No human message found"
            )
        }

    t0 = time.monotonic()
    raw_result = llm.invoke([
        SystemMessage(content=_ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=last_human.content),
    ])
    latency_ms = int((time.monotonic() - t0) * 1000)

    # include_raw=True returns {"raw": AIMessage, "parsed": RouteDecision, ...}
    # Mocks may return RouteDecision directly — handle both.
    if isinstance(raw_result, dict) and "parsed" in raw_result:
        route_decision: RouteDecision = raw_result["parsed"]
        raw_response = raw_result.get("raw")
        usage_meta = getattr(raw_response, "usage_metadata", None) or {}
        tokens_in = usage_meta.get("input_tokens", 0)
        tokens_out = usage_meta.get("output_tokens", 0)
    else:
        route_decision = raw_result
        tokens_in = 0
        tokens_out = 0

    audit_entry = {
        "event": "router",
        "model": model_name,
        "provider": "anthropic",
        "route": route_decision.intent.value,
        "confidence": route_decision.confidence,
        "latency_ms": latency_ms,
        "user_id": state.get("user_id"),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }

    return {
        "route_decision": route_decision,
        "audit_log": state.get("audit_log", []) + [audit_entry],
    }


def _clarification_node(state: AgentState) -> dict:
    """Returns a clarification prompt when routing confidence is below threshold or intent is FALLBACK."""
    rd = state.get("route_decision")
    reason_hint = ""
    if rd and rd.reasoning:
        reason_hint = f" (reason: {rd.reasoning})"

    content = (
        "I'm not sure what you're asking{}. I can help with:\n\n"
        "• **Fitness coaching** — questions about exercises, form, programming, recovery\n"
        "• **Workout planning** — generating a workout plan tailored to your goals\n"
        "• **Workout logging** — recording a workout you just completed\n\n"
        "Could you rephrase your request?"
    ).format(reason_hint)

    audit_entry = {
        "event": "clarification",
        "trigger": "low_confidence" if (rd and rd.confidence < 0.6) else "fallback_intent",
        "confidence": rd.confidence if rd else None,
        "user_id": state.get("user_id"),
    }

    return {
        "messages": [AIMessage(content=content)],
        "audit_log": state.get("audit_log", []) + [audit_entry],
    }


def _route_selector(state: AgentState) -> str:
    """Conditional edge: dispatch to sub-agent or clarification based on route_decision."""
    rd = state.get("route_decision")
    if rd is None or rd.confidence < 0.6:
        return "clarification"
    intent_to_node = {
        Intent.COACH: "coach",
        Intent.WORKOUT_GENERATE: "workout_gen",
        Intent.WORKOUT_LOG: "workout_log",
        Intent.FALLBACK: "clarification",
    }
    return intent_to_node.get(rd.intent, "clarification")


def build_hub_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("router", _router_node)
    graph.add_node("clarification", _clarification_node)
    graph.add_node("coach", coach_graph)
    graph.add_node("workout_gen", workout_generator_graph)
    graph.add_node("workout_log", workout_logger_graph)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_selector,
        {
            "coach": "coach",
            "workout_gen": "workout_gen",
            "workout_log": "workout_log",
            "clarification": "clarification",
        },
    )
    graph.add_edge("coach", END)
    graph.add_edge("workout_gen", END)
    graph.add_edge("workout_log", END)
    graph.add_edge("clarification", END)

    return graph


# Compiled singleton — import this for production use
hub = build_hub_graph().compile()
