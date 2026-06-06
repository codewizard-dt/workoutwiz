# 026 — Clarification Node Finalization

> **Depends on**: [024-router-node](024-router-node.md)
> **Blocks**: none
> **Parallel-safe with**: [025-conditional-edge-routing](025-conditional-edge-routing.md)

## Objective

Finalize the clarification node so it returns a well-formed, assessor-visible clarification message with the routing reasoning included — no sub-agent is invoked, no silent misroute occurs — and appends an audit log entry documenting why clarification was triggered.

## Approach

The clarification node was stubbed in task 023. This task replaces the stub with a production-quality node: it reads `route_decision.reasoning` from state (if present) to explain why the message was ambiguous, returns a user-friendly message listing the three capabilities, and appends a `clarification` audit entry. The node lives in `hub.py`.

## Steps

### 1. Replace clarification stub in hub.py  <!-- agent: general-purpose -->

Replace `_clarification_node` in `1-multi-agent/src/workout_wiz/hub.py` with:

```python
def _clarification_node(state: AgentState) -> dict:
    """Returns a clarification prompt when routing confidence is below threshold or intent is FALLBACK."""
    from langchain_core.messages import AIMessage

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
```

- [ ] `_clarification_node` reads `route_decision.reasoning` and includes it in the message (if present)
- [ ] Message lists all three capabilities: coaching, planning, logging
- [ ] Audit entry appended with `event: clarification`, trigger, confidence, user_id
- [ ] Message ends with a question ("Could you rephrase your request?")

### 2. Test clarification node  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_clarification.py`:

```python
from langchain_core.messages import HumanMessage
from workout_wiz.hub import hub
from workout_wiz.state import RouteDecision, Intent


def test_clarification_message_format():
    """Clarification node should list all three capabilities."""
    result = hub.invoke({
        "messages": [HumanMessage(content="what?")],
        "route_decision": RouteDecision(
            intent=Intent.FALLBACK, confidence=0.3, reasoning="completely off-topic"
        ),
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
    result = hub.invoke({
        "messages": [HumanMessage(content="hmm")],
        "route_decision": RouteDecision(
            intent=Intent.COACH, confidence=0.4, reasoning="ambiguous"
        ),
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
    result = hub.invoke({
        "messages": [HumanMessage(content="xyz")],
        "route_decision": RouteDecision(
            intent=Intent.FALLBACK, confidence=0.1, reasoning="no recognizable keywords"
        ),
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    })
    last = result["messages"][-1].content
    assert "no recognizable keywords" in last
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_clarification.py -v`

- [ ] All 3 tests pass

## Acceptance Criteria

- [ ] `_clarification_node` in `hub.py` includes `route_decision.reasoning` in the response message
- [ ] Message lists all three system capabilities (coaching, planning, logging)
- [ ] Audit log gets a `clarification` entry with trigger, confidence, user_id
- [ ] `pytest tests/test_clarification.py` passes (3/3)
