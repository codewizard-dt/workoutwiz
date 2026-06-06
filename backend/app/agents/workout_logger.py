import time
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from rapidfuzz import process as fuzz_process

from app.agents.exercises import get_all_exercises
from app.agents.state import AgentState
from app.config import settings


class LoggedSet(BaseModel):
    exercise_name: str = Field(description="The name of the exercise as stated by the user")
    canonical_name: str | None = Field(
        default=None,
        description="Canonical exercise name from the database after fuzzy matching",
    )
    exercise_id: str | None = Field(
        default=None,
        description="UUID of the matched exercise from the database (null if no match found)",
    )
    match_confidence: float = Field(
        default=0.0,
        description="Fuzzy match confidence 0.0-1.0 (1.0 = exact match)",
    )
    sets: int | None = Field(default=None, description="Number of sets performed")
    reps: int | None = Field(default=None, description="Reps per set")
    weight_kg: float | None = Field(default=None, description="Weight in kg (if applicable)")
    duration_s: int | None = Field(default=None, description="Duration in seconds (if applicable)")
    distance_m: float | None = Field(default=None, description="Distance in metres (if applicable)")
    notes: str | None = Field(default=None, description="Any additional notes for this set")


class WorkoutLog(BaseModel):
    raw_input: str = Field(description="The user's original workout description, verbatim")
    logged_sets: list[LoggedSet] = Field(
        description="Structured list of exercises with their metrics, parsed from the user's input"
    )
    unrecognized: list[str] = Field(
        default_factory=list,
        description="Exercise names mentioned that could not be matched to any exercise (confidence < 0.75)",
    )
    parse_notes: str | None = Field(
        default=None,
        description="Any ambiguity or assumptions made during parsing",
    )


_LOGGER_SYSTEM_PROMPT = """You are a workout logging assistant. Parse the user's workout description into a structured format.

For each exercise mentioned, extract:
- The exercise name (as stated by the user)
- Sets and reps (if mentioned), e.g. "3x10" = 3 sets of 10 reps
- Weight (if mentioned), convert to kg if in lbs (1 lb = 0.453592 kg)
- Duration (if mentioned), convert to seconds
- Distance (if mentioned), convert to metres

Be precise. If an exercise is mentioned multiple times, create separate entries.
If information is not mentioned, leave the field null.
If you're making assumptions, note them in parse_notes.
"""


def _fuzzy_match_exercise(name: str, exercises: list[Any]) -> tuple[str | None, str | None, float]:
    """Fuzzy-match exercise name against the dataset. Returns (exercise_id, canonical_name, confidence 0-1)."""
    if not exercises:
        return None, None, 0.0
    exercise_names = [e.name for e in exercises]
    result = fuzz_process.extractOne(name, exercise_names, scorer=fuzz.token_sort_ratio)
    if result is None:
        return None, None, 0.0
    matched_name, score, idx = result
    confidence = score / 100.0
    if confidence < 0.45:
        return None, None, confidence
    return str(exercises[idx].id), matched_name, confidence


def _log_node(state: AgentState) -> dict[str, Any]:
    model_name = settings.logger_model
    llm = ChatAnthropic(model=model_name, api_key=settings.anthropic_api_key).with_structured_output(WorkoutLog, include_raw=True)
    exercises = get_all_exercises()

    next(
        (m for m in reversed(state["messages"]) if hasattr(m, "type") and m.type == "human"),
        None,
    )

    t0 = time.monotonic()
    raw_result = llm.invoke([
        SystemMessage(content=_LOGGER_SYSTEM_PROMPT),
        *state["messages"],
    ])
    latency_ms = int((time.monotonic() - t0) * 1000)

    # include_raw=True returns {"raw": AIMessage, "parsed": WorkoutLog, ...}
    # Mocks may return WorkoutLog directly — handle both.
    if isinstance(raw_result, dict) and "parsed" in raw_result:
        workout_log: WorkoutLog = raw_result["parsed"]
        raw_response = raw_result.get("raw")
        usage_meta = getattr(raw_response, "usage_metadata", None) or {}
        tokens_in = usage_meta.get("input_tokens", 0)
        tokens_out = usage_meta.get("output_tokens", 0)
    else:
        workout_log = raw_result
        tokens_in = 0
        tokens_out = 0

    # Resolve exercise IDs via fuzzy matching
    unrecognized = []
    for logged_set in workout_log.logged_sets:
        if logged_set.exercise_id is None:
            exercise_id, canonical_name, confidence = _fuzzy_match_exercise(logged_set.exercise_name, exercises)
            logged_set.exercise_id = exercise_id
            logged_set.canonical_name = canonical_name
            logged_set.match_confidence = confidence
            if exercise_id is None:
                unrecognized.append(logged_set.exercise_name)

    workout_log.unrecognized = unrecognized

    response_text = (
        f"Logged {len(workout_log.logged_sets)} exercise(s).\n"
        + "\n".join(
            f"• {s.canonical_name or s.exercise_name}: "
            + (f"{s.sets}×{s.reps}" if s.sets and s.reps else "")
            + (f" @ {s.weight_kg}kg" if s.weight_kg else "")
            + (f" ({int(s.match_confidence * 100)}% match)" if s.exercise_id else " [unrecognized]")
            for s in workout_log.logged_sets
        )
        + (f"\nUnrecognized: {', '.join(unrecognized)}" if unrecognized else "")
    )

    audit_entry = {
        "event": "logger",
        "model": model_name,
        "provider": "anthropic",
        "latency_ms": latency_ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }

    return {
        "messages": [AIMessage(content=response_text)],
        "audit_log": list(state.get("audit_log", [])) + [audit_entry],
    }


def build_workout_logger_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("log", _log_node)
    graph.add_edge(START, "log")
    graph.add_edge("log", END)
    return graph


workout_logger_graph = build_workout_logger_graph().compile()
