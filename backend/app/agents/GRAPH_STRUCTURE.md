# Agent Graph Structure

This document is the authoritative reference for the LangGraph multi-agent architecture in `backend/app/agents/`. It covers the hub StateGraph, all nodes, conditional routing logic, sub-agent graphs, shared state, and audit log contract.

---

## Overview

```
POST /chat/
    │
    ▼
Hub StateGraph (hub.py)
    │
    ├─ router node  ──────────────────────────────────────────────────────────┐
    │   LLM structured output → RouteDecision{intent, confidence, reasoning}  │
    │                                                                          │
    │   _route_selector() dispatches:                                          │
    │     confidence < 0.6  ──────────────────────────────► clarification     │
    │     Intent.FALLBACK   ──────────────────────────────► clarification     │
    │     Intent.COACH      ──────────────────────────────► coach             │
    │     Intent.WORKOUT_LOG ─────────────────────────────► workout_log       │
    │     Intent.KNOWLEDGE_GRAPH ─────────────────────────► knowledge_graph   │
    │     (unknown fallthrough) ──────────────────────────► clarification     │
    │                                                                          │
    ├─ clarification node                                                      │
    ├─ coach node          (compiled sub-graph)                                │
    ├─ workout_log node    (compiled sub-graph)                                │
    └─ knowledge_graph node (inline async node)                               │
              │                                                                │
             END ◄────────────────────────────────────────────────────────────┘
```

All nodes share a single `AgentState` TypedDict. Each terminal node appends to `audit_log` and writes to `messages`; control then returns to `END`.

---

## Shared State — `AgentState` (`state.py`)

```python
class AgentState(TypedDict):
    messages:       Annotated[list[Any], add_messages]  # conversation history; LangGraph accumulates via add_messages reducer
    route_decision: RouteDecision | None                 # written by router node
    user_id:        str | None                           # injected by FastAPI before invocation
    user_email:     str | None                           # injected by FastAPI before invocation
    session_id:     str | None                           # injected by FastAPI before invocation
    audit_log:      list[dict[str, Any]]                 # appended by every node
    kg_result:      dict[str, Any] | None                # written by knowledge_graph node only
```

### `RouteDecision` (structured output schema)

```python
class RouteDecision(BaseModel):
    intent:     Intent   # one of COACH | WORKOUT_LOG | KNOWLEDGE_GRAPH | FALLBACK
    confidence: float    # 0.0–1.0; < 0.6 triggers clarification regardless of intent
    reasoning:  str      # one sentence explaining the classification
```

### `Intent` enum

| Value | Meaning |
|-------|---------|
| `COACH` | Fitness question, advice, education, or motivation — not a workout generation request |
| `WORKOUT_LOG` | User is recording a workout they already completed |
| `KNOWLEDGE_GRAPH` | User wants a workout built/generated — with or without injury context |
| `FALLBACK` | Off-topic, unclear, or unmappable message |

---

## Hub Graph — `hub.py`

### Node: `router` (`_router_node`)

| Property | Value |
|----------|-------|
| Type | `async` |
| Model | `settings.router_model` (default: `claude-haiku-4-5-20251001`) |
| Structured output | `with_structured_output(RouteDecision, include_raw=True)` |
| Input | Last `HumanMessage` from `state["messages"]` |
| Writes | `route_decision`, appends `audit_log` entry |

**Input to LLM:** only the last human message (not full history) — routing is stateless per turn.

**Routing guard in `_route_selector()`:**

```
if route_decision is None  →  "clarification"
if confidence < 0.6        →  "clarification"
Intent.COACH               →  "coach"
Intent.WORKOUT_LOG         →  "workout_log"
Intent.KNOWLEDGE_GRAPH     →  "knowledge_graph"
Intent.FALLBACK            →  "clarification"
unknown                    →  "clarification"   (safe default)
```

**Audit log entry emitted:**
```json
{
  "event":      "router",
  "model":      "<model_name>",
  "provider":   "anthropic",
  "route":      "<intent value>",
  "confidence": 0.95,
  "latency_ms": 420,
  "user_id":    "<uuid>",
  "tokens_in":  110,
  "tokens_out": 22
}
```

---

### Node: `clarification` (`_clarification_node`)

| Property | Value |
|----------|-------|
| Type | sync |
| Trigger | `confidence < 0.6` OR `Intent.FALLBACK` OR missing `route_decision` |
| Input | `route_decision.reasoning` (optional, used in message text) |
| Writes | Appends static clarification `AIMessage` to `messages`, appends `audit_log` entry |

**No LLM call.** Returns a static prompt listing the three supported capabilities.

**Audit log entry emitted:**
```json
{
  "event":      "clarification",
  "trigger":    "low_confidence" | "fallback_intent",
  "confidence": 0.45,
  "user_id":    "<uuid>"
}
```

---

### Node: `knowledge_graph` (`_knowledge_graph_node`)

| Property | Value |
|----------|-------|
| Type | `async` inline node (not a compiled sub-graph) |
| Trigger | `Intent.KNOWLEDGE_GRAPH` — all workout generation requests, with or without injury context |
| Pipeline | `build_retrieval_graph()` → `build_generation_graph()` |
| Input | Last human message content + `user_id` from state |
| Writes | Appends formatted `AIMessage` to `messages`; sets `kg_result`; appends retrieval + generation + hub audit entries |

**Pipeline:**
1. **Retrieval graph** (`kg/retrieval_graph.py`) — queries Neo4j for member context, injuries, and matching exercises; emits its own `audit_log` entries
2. **Generation graph** (`kg/generation_graph.py`) — LLM call with retrieved context to produce a `WorkoutRecommendation`; emits its own `audit_log` entries
3. Hub node formats the recommendation into a human-readable message and sets `kg_result`

**`kg_result` shape (written to state):**
```json
{
  "overall_reasoning": "...",
  "fallback_used": false,
  "exercises": [
    {
      "id": "<uuid>",
      "name": "Dumbbell Bench Press",
      "sets": 3,
      "reps": "10-12",
      "duration_seconds": null,
      "reasoning": "Safe for your shoulder — avoids overhead load"
    }
  ]
}
```

**Hub audit log entry emitted:**
```json
{
  "event":      "kg_hub",
  "model":      "n/a",
  "provider":   "neo4j",
  "intent":     "KNOWLEDGE_GRAPH",
  "latency_ms": 2100,
  "user_id":    "<uuid>",
  "tokens_in":  0,
  "tokens_out": 0
}
```
*(Retrieval and generation sub-graphs emit their own audit entries; these are accumulated into `audit_log` before the hub entry.)*

---

## Sub-Agent Graph: `coach_graph` (`coach.py`)

```
START → chat → END
```

| Property | Value |
|----------|-------|
| Nodes | 1: `chat` (`_chat_node`) |
| Type | sync, compiled `StateGraph(AgentState)` |
| Model | `settings.coach_model` (default: `claude-haiku-4-5-20251001`) |
| Tools | None — raw LLM invocation only |
| Structured output | No |

**`_chat_node` behaviour:**
- Extracts `user_email` from state → prepends `"The user's name is <Name> (email: …).\n\n"` to system prompt
- Passes full `messages` history to LLM (not just the last message)
- Returns updated `messages` + appended `audit_log` entry

**System prompt intent:** Fitness education and coaching Q&A. Explicitly instructs the LLM *not* to generate workout plans or log workouts.

**What it has access to:** email identity, full conversation history.  
**What it does NOT have:** workout history, injuries, profile data, Neo4j context.

**Audit log entry emitted:**
```json
{
  "event":      "coach",
  "model":      "<model_name>",
  "provider":   "anthropic",
  "latency_ms": 810,
  "tokens_in":  340,
  "tokens_out": 195
}
```

---

## Sub-Agent Graph: `workout_logger_graph` (`workout_logger.py`)

```
START → log → END
```

| Property | Value |
|----------|-------|
| Nodes | 1: `log` (`_log_node`) |
| Type | sync, compiled `StateGraph(AgentState)` |
| Model | `settings.logger_model` (default: `claude-haiku-4-5-20251001`) |
| Tools | None |
| Structured output | `with_structured_output(WorkoutLog, include_raw=True)` |

**`_log_node` behaviour:**
1. LLM parses message history into `WorkoutLog` (structured output)
2. Each `LoggedSet` without an explicit exercise ID is fuzzy-matched against the exercise database via `_fuzzy_match_exercise()` (RapidFuzz, threshold 70%)
3. Unrecognised exercises recorded in `WorkoutLog.unrecognized`
4. Returns human-readable confirmation message + appended `audit_log` entry

**`WorkoutLog` schema:**
```python
class LoggedSet(BaseModel):
    exercise_name:    str
    exercise_id:      str | None       # resolved by fuzzy match
    canonical_name:   str | None       # resolved name from DB
    match_confidence: float | None     # 0.0–1.0
    sets:             int | None
    reps:             int | None
    weight_kg:        float | None
    duration_s:       int | None

class WorkoutLog(BaseModel):
    logged_sets:   list[LoggedSet]
    unrecognized:  list[str]           # names that couldn't be matched
```

**Audit log entry emitted:**
```json
{
  "event":      "logger",
  "model":      "<model_name>",
  "provider":   "anthropic",
  "latency_ms": 650,
  "tokens_in":  280,
  "tokens_out": 90
}
```

---

## Audit Log Contract

Every node appends to `state["audit_log"]`. The full list is persisted to PostgreSQL via `persist_audit_log()` (`audit_persist.py`) after graph execution.

**Event names by node:**

| Node | `event` value |
|------|--------------|
| router | `"router"` |
| clarification | `"clarification"` |
| coach | `"coach"` |
| workout_log | `"logger"` |
| knowledge_graph (hub) | `"kg_hub"` |
| retrieval sub-graph | `"kg_retrieval"` (or as emitted by `retrieval_graph.py`) |
| generation sub-graph | `"kg_generation"` (or as emitted by `generation_graph.py`) |

---

## Files

| File | Responsibility |
|------|---------------|
| `state.py` | `AgentState`, `Intent`, `RouteDecision` |
| `hub.py` | Hub `StateGraph`, router node, clarification node, knowledge_graph node, `_route_selector` |
| `coach.py` | `coach_graph` — single-node Q&A sub-graph |
| `workout_logger.py` | `workout_logger_graph` — single-node structured-output logger sub-graph |
| `workout_generator.py` | Legacy generator sub-graph — **not routed to by hub**; retained for reference |
| `audit_persist.py` | `persist_audit_log()` — writes `audit_log` entries to PostgreSQL |
| `exercises.py` | `get_all_exercises()` — cached exercise list from DB (used by logger) |
