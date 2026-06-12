import time
from typing import Any, cast

from app.kg.driver import create_neo4j_driver
from app.kg.retrieval_graph import build_retrieval_graph
from app.kg.generation_graph import build_generation_graph

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.workout_logger import workout_logger_graph
from app.agents.state import AgentState, Intent, RouteDecision
from app.agents.coach import coach_graph
from app.config import settings


_ROUTER_SYSTEM_PROMPT = """You are a routing agent for a fitness coaching system.
Classify the user's message into exactly one of these intents:

- MEMBER_CONTEXT_KG: The user is asking a fitness *question* or wants advice, education, explanation, or motivation — but is NOT asking to generate a workout. Examples: "What muscles does a deadlift work?", "How many rest days do I need?", "Should I do cardio before or after lifting?", "who am i", "what's my name", "tell me about myself". COACH is for questions, not plans.
- WORKOUT_LOG: The user is recording a workout they already completed (e.g. "I just did 3x10 squats at 100kg", "Log my run: 5km in 25 minutes", "I finished my chest day").
- WORKOUT_GENERATE_KG: The user wants a workout or exercise selection *produced for them* — built, created, planned, generated, OR recommended based on their own profile/injuries. This route reads the member's personal knowledge graph (their injuries, history, equipment) and returns a personalized, injury-filtered list of exercises. Use it whenever the answer should be a tailored list of specific exercises. Examples: "Give me a 30-minute upper body workout", "Build me a push day", "I only have dumbbells, give me a full-body workout", "Create a leg day routine", "What should I do for my workout today?", "I have a bad knee, build me something safe", "Suggest exercises that won't aggravate my shoulder", "What exercises suit my injuries?", "What exercises are safe for me?", "Which exercises should I avoid given my injuries?". Any request whose best answer is a personalized list of exercises belongs here — even when it is phrased as a question.
- FALLBACK: The message is unclear, off-topic, or cannot be mapped to the above intents (e.g. "What's the capital of France?", "Tell me a joke").

IMPORTANT: When in doubt between MEMBER_CONTEXT_KG and WORKOUT_GENERATE_KG, ask: would the best answer be a personalized list of specific exercises for *this* user? If yes — including injury-aware questions like "what exercises suit my injuries?" — always choose WORKOUT_GENERATE_KG. COACH is only for general fitness questions whose answer is explanation or advice, not a tailored exercise list. Never route an injury-aware exercise-suitability question to COACH or FALLBACK.

Return a confidence score (0.0–1.0). Use < 0.6 only when genuinely ambiguous.
"""


async def _router_node(state: AgentState) -> dict[str, Any]:
    """LLM-based routing node using ChatAnthropic with_structured_output(RouteDecision)."""
    model_name = settings.router_model
    llm = ChatAnthropic(model=model_name, api_key=settings.anthropic_api_key).with_structured_output(RouteDecision, include_raw=True)

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
        route_decision = cast(RouteDecision, raw_result)
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


def _clarification_node(state: AgentState) -> dict[str, Any]:
    """Returns a clarification prompt when routing confidence is below threshold or intent is FALLBACK."""
    rd = state.get("route_decision")
    reason_hint = ""
    if rd and rd.reasoning:
        reason_hint = f" (reason: {rd.reasoning})"

    content = (
        f"I'm not sure what you're asking{reason_hint}. I can help with:\n\n"
        "• **Fitness coaching** — questions about exercises, form, programming, recovery\n"
        "• **Workout planning** — generating a workout plan tailored to your goals\n"
        "• **Workout logging** — recording a workout you just completed\n\n"
        "Could you rephrase your request?"
    )

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


async def _knowledge_graph_node(state: AgentState) -> dict[str, Any]:
    """Run retrieval → generation pipeline and return formatted recommendation."""
    last_human = next(
        (m for m in reversed(state["messages"]) if hasattr(m, "type") and m.type == "human"),
        None,
    )
    query = last_human.content if last_human else ""
    member_id = state.get("user_id") or "unknown-member"

    t0 = time.monotonic()
    nested_audit_log: list[dict[str, Any]] = []
    rec = None
    kg_result: dict[str, Any] | None = None
    try:
        driver = create_neo4j_driver()
        retrieval_result = await build_retrieval_graph(driver).ainvoke(
            {"member_id": member_id, "query": query}
        )
        context = retrieval_result.get("context")
        # Collect audit entries from retrieval subgraph
        nested_audit_log.extend(retrieval_result.get("audit_log", []))

        gen_result = await build_generation_graph().ainvoke(
            {"member_id": member_id, "query": query, "context": context}
        )
        # Collect audit entries from generation subgraph
        nested_audit_log.extend(gen_result.get("audit_log", []))

        latency_ms = int((time.monotonic() - t0) * 1000)

        rec = gen_result.get("recommendation")
        if rec and rec.exercises:
            # Build a Markdown reply so the frontend can render it cleanly.
            lines = ["**Here's your personalized workout:**", ""]
            for i, ex in enumerate(rec.exercises, 1):
                if ex.reps:
                    detail = f"{ex.sets} × {ex.reps} reps"
                elif ex.duration_seconds:
                    detail = f"{ex.sets} × {ex.duration_seconds}s"
                else:
                    detail = f"{ex.sets} sets"
                if getattr(ex, "weight_kg", None):
                    detail += f" @ {ex.weight_kg} kg"
                lines.append(f"{i}. **{ex.name}** — {detail}")
                if ex.reasoning:
                    lines.append(f"   - {ex.reasoning}")
            if rec.overall_reasoning:
                lines.append("")
                lines.append(rec.overall_reasoning)
            if rec.skipped_exercise_ids:
                lines.append("")
                lines.append(
                    f"> Note: {len(rec.skipped_exercise_ids)} exercise(s) "
                    "excluded due to injury constraints."
                )
            content = "\n".join(lines)
        else:
            content = "I couldn't build a recommendation with the available context. Please provide more details."

        tokens_in = gen_result.get("tokens_in", 0)
        tokens_out = gen_result.get("tokens_out", 0)

        if rec is not None:
            kg_result = {
                "overall_reasoning": getattr(rec, "overall_reasoning", None),
                "fallback_used": getattr(rec, "fallback_used", False),
                "exercises": [
                    {
                        "exercise_id": getattr(ex, "exercise_id", None),
                        "name": getattr(ex, "name", None),
                        "sets": getattr(ex, "sets", None),
                        "reps": getattr(ex, "reps", None),
                        "duration_seconds": getattr(ex, "duration_seconds", None),
                        "weight_kg": getattr(ex, "weight_kg", None),
                        "reasoning": getattr(ex, "reasoning", None),
                    }
                    for ex in (rec.exercises or [])
                ],
            }
    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        content = f"Knowledge graph recommendation failed: {exc}"
        tokens_in = 0
        tokens_out = 0

    audit_entry = {
        "event": "kg_hub",
        "model": "n/a",
        "provider": "neo4j",
        "intent": "WORKOUT_GENERATE_KG",
        "latency_ms": latency_ms,
        "user_id": state.get("user_id"),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }

    return {
        "messages": [AIMessage(content=content)],
        "audit_log": state.get("audit_log", []) + nested_audit_log + [audit_entry],
        "kg_result": kg_result,
    }


def _route_selector(state: AgentState) -> str:
    """Conditional edge: dispatch to sub-agent or clarification based on route_decision."""
    rd = state.get("route_decision")
    if rd is None or rd.confidence < 0.6:
        return "clarification"
    intent_to_node = {
        Intent.MEMBER_CONTEXT_KG: "coach",
        Intent.WORKOUT_LOG: "workout_log",
        Intent.FALLBACK: "clarification",
        Intent.WORKOUT_GENERATE_KG: "knowledge_graph",
    }
    return intent_to_node.get(rd.intent, "clarification")


def build_hub_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("router", _router_node)
    graph.add_node("clarification", _clarification_node)
    graph.add_node("coach", coach_graph)
    graph.add_node("workout_log", workout_logger_graph)
    graph.add_node("knowledge_graph", _knowledge_graph_node)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_selector,
        {
            "coach": "coach",
            "workout_log": "workout_log",
            "clarification": "clarification",
            "knowledge_graph": "knowledge_graph",
        },
    )
    graph.add_edge("coach", END)
    graph.add_edge("workout_log", END)
    graph.add_edge("clarification", END)
    graph.add_edge("knowledge_graph", END)

    return graph


# Compiled singleton — import this for production use
hub = build_hub_graph().compile()
