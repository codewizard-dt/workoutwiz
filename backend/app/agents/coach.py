import time
from typing import Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.config import settings

_COACH_SYSTEM_PROMPT = """You are an expert fitness coach with deep knowledge of:
- Exercise form, technique, and biomechanics
- Strength training principles (progressive overload, periodization, deload weeks)
- Cardiovascular training (zones, HIIT, steady-state)
- Recovery, sleep, and injury prevention
- Basic sports nutrition (macros, hydration, pre/post workout)

Answer the user's question clearly and concisely. Be specific, evidence-based, and practical.
Do not create workout plans (that's handled by a separate system) — focus on coaching and education.
If asked to log a workout, explain that's handled separately.
"""


def _chat_node(state: AgentState) -> dict[str, Any]:
    model_name = settings.coach_model
    llm = ChatAnthropic(model=model_name, api_key=settings.anthropic_api_key)

    identity_prefix = ""
    if email := state.get("user_email"):
        display = email.split("@")[0].replace(".", " ").title()
        identity_prefix = f"The user's name is {display} (email: {email}).\n\n"

    messages = [SystemMessage(content=identity_prefix + _COACH_SYSTEM_PROMPT)] + list(state["messages"])
    t0 = time.monotonic()
    try:
        response = llm.invoke(messages)
        latency_ms = int((time.monotonic() - t0) * 1000)
        usage = getattr(response, "response_metadata", {})
        tokens_in = usage.get("usage", {}).get("input_tokens", 0)
        tokens_out = usage.get("usage", {}).get("output_tokens", 0)
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.monotonic() - t0) * 1000)
        response = AIMessage(content="I'm temporarily unavailable. Please try again in a moment.")
        tokens_in = 0
        tokens_out = 0

    audit_entry = {
        "event": "coach",
        "model": model_name,
        "provider": "anthropic",
        "latency_ms": latency_ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }

    return {
        "messages": [response],
        "audit_log": list(state.get("audit_log", [])) + [audit_entry],
    }


def build_coach_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("chat", _chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph


coach_graph = build_coach_graph().compile()
