# 021 — Shared Typed State and Route Schema

> **Depends on**: [019-python-package-setup](019-python-package-setup.md)
> **Blocks**: none
> **Parallel-safe with**: [020-install-core-dependencies](020-install-core-dependencies.md)

## Objective

Define the shared data contracts used across the entire multi-agent system: the `AgentState` TypedDict (the LangGraph graph state) and the `RouteDecision` Pydantic model (the structured output from the router node). These types are the single source of truth for all inter-node communication.

## Approach

All shared types live in `src/workout_wiz/state.py`. `AgentState` is a `TypedDict` as required by LangGraph's `StateGraph`. `RouteDecision` is a Pydantic `BaseModel` used with `with_structured_output()` — its field descriptions are critical for LLM grounding. The intent enum is defined as a `str` enum for JSON serialization compatibility.

## Steps

### 1. Create src/workout_wiz/state.py  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/state.py` with the following content:

```python
from enum import Enum
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Intent(str, Enum):
    COACH = "COACH"
    WORKOUT_GENERATE = "WORKOUT_GENERATE"
    WORKOUT_LOG = "WORKOUT_LOG"
    FALLBACK = "FALLBACK"


class RouteDecision(BaseModel):
    """Structured output from the router node. Used with with_structured_output()."""

    intent: Intent = Field(
        description=(
            "The most likely intent of the user message. "
            "COACH for general fitness questions, "
            "WORKOUT_GENERATE to create a new workout plan, "
            "WORKOUT_LOG to record a completed workout, "
            "FALLBACK when the message is unclear or off-topic."
        )
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score between 0.0 and 1.0. "
            "Use < 0.6 only when the intent is genuinely ambiguous."
        ),
    )
    reasoning: str = Field(
        description="One sentence explaining why this intent was chosen."
    )


class AgentState(TypedDict):
    """Shared state flowing through the hub StateGraph and all sub-agent graphs."""

    # Conversation history — LangGraph accumulates messages with add_messages reducer
    messages: Annotated[list, add_messages]

    # Set by the router node after classification
    route_decision: RouteDecision | None

    # User identity — populated by the FastAPI layer before graph invocation
    user_id: str | None

    # Audit fields — populated as the graph executes
    session_id: str | None
    audit_log: list[dict]
```

- [x] `1-multi-agent/src/workout_wiz/state.py` exists
- [x] `Intent` enum has exactly four values: COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK
- [x] `RouteDecision` has `intent`, `confidence` (0.0–1.0), and `reasoning` fields with descriptions
- [x] `AgentState` uses `Annotated[list, add_messages]` for the `messages` field
- [x] `AgentState` includes `route_decision`, `user_id`, `session_id`, `audit_log` fields

### 2. Verify imports  <!-- agent: general-purpose -->

From `1-multi-agent/`, activate the venv and confirm the module imports cleanly:

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "from workout_wiz.state import AgentState, RouteDecision, Intent; print('OK')"
```

- [x] Import exits 0 with "OK" printed
- [x] No import errors (langgraph, pydantic, typing_extensions all available)

### 3. Write a smoke test  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/__init__.py` (empty) and `1-multi-agent/tests/test_state.py`:

```python
from workout_wiz.state import AgentState, RouteDecision, Intent


def test_route_decision_valid():
    rd = RouteDecision(intent=Intent.COACH, confidence=0.9, reasoning="General fitness question")
    assert rd.intent == Intent.COACH
    assert rd.confidence == 0.9


def test_route_decision_confidence_bounds():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RouteDecision(intent=Intent.COACH, confidence=1.5, reasoning="too high")


def test_intent_values():
    assert set(Intent) == {Intent.COACH, Intent.WORKOUT_GENERATE, Intent.WORKOUT_LOG, Intent.FALLBACK}
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_state.py -v`

- [x] `tests/__init__.py` exists
- [x] `tests/test_state.py` exists with three test functions
- [x] All three tests pass

## Acceptance Criteria

- [x] `src/workout_wiz/state.py` exists with `Intent`, `RouteDecision`, and `AgentState` defined
- [x] `RouteDecision` confidence field enforces 0.0–1.0 range via Pydantic validator
- [x] `AgentState.messages` uses `add_messages` reducer
- [x] `pytest tests/test_state.py` passes (3/3)

---
**UAT**: [`.docs/uat/021-shared-state-and-route-schema.uat.md`](../uat/021-shared-state-and-route-schema.uat.md)
