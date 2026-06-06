---
title: Observability Stack — In-Process audit_log Extension
status: Proposed
created: 2026-06-06
owner: David Taylor
roadmap: ROADMAP-005
---

## Executive Summary

The observability strategy extends the existing in-process `audit_log` pattern established in the hub router to all agent sub-graphs and knowledge graph (KG) layer nodes. No external observability stack (LangFuse, OpenLLMetry, Grafana, Prometheus) is introduced — all telemetry is session-scoped, in-memory, and exposed via REST endpoints. This is appropriate for the assessment context: lightweight, self-contained, and zero operational overhead.

---

## Context

### Existing Pattern: audit_log in hub.py

`backend/app/agents/hub.py` lines 44–78 establishes the baseline instrumentation pattern. Each node in the hub StateGraph appends a structured dict to `state["audit_log"]` containing the following fields:

- `event` — the name of the node or action (e.g., `"router"`, `"coach"`, `"workout_gen"`)
- `latency_ms` — wall-clock duration of the node execution in milliseconds
- `tokens_in` — input token count reported by the LLM response
- `tokens_out` — output token count reported by the LLM response
- `model` — the model identifier used for the invocation
- `provider` — the LLM provider (e.g., `"anthropic"`, `"openai"`)
- `user_id` — the authenticated user's ID, threaded through from the session context

This pattern captures per-node telemetry in a single append-only list without requiring any external sink or background thread.

### Existing State Schema: AgentState in state.py

`backend/app/agents/state.py` lines 41–56 defines the `AgentState` TypedDict. The `audit_log: list[dict[str, Any]]` field is already declared as part of the shared state, meaning all nodes in the hub graph have read/write access to the log without additional wiring.

### Existing REST Exposure: /chat/audit/{session_id}

`backend/app/routers/chat.py` lines 96–122 exposes the accumulated audit log for a given session via a GET endpoint at `/chat/audit/{session_id}`. The endpoint retrieves the in-memory session state and returns the `audit_log` list as a JSON array. This provides a zero-dependency way to inspect per-session telemetry from the frontend or external tooling.

### The Gap: KG Layer Nodes Have Zero Instrumentation

The knowledge graph layer — comprising `retrieval_graph.py`, `generation_graph.py`, and `explainability.py` — currently appends nothing to `audit_log`. As a result:

- KG retrieval latency is invisible (no way to distinguish slow Neo4j queries from slow LLM calls)
- Token usage for KG generation passes is untracked
- Explainability node execution is entirely opaque to the audit endpoint
- Any session that exercises the KG path produces an incomplete audit trace

Extending the existing `audit_log` pattern to these nodes closes the gap without introducing new infrastructure.

---

## Decisions

---

## D1: Audit Entry Schema

**Status**: Proposed

### Current Schema

Each node in `backend/app/agents/hub.py` (lines 64–73) appends a dict with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `event` | `str` | Node name (e.g., `"router"`, `"coach"`, `"workout_gen"`) |
| `latency_ms` | `int` | Wall-clock duration of node execution in milliseconds |
| `tokens_in` | `int` | Input token count from LLM response metadata |
| `tokens_out` | `int` | Output token count from LLM response metadata |
| `model` | `str` | Model identifier (e.g., `"claude-3-5-haiku-20241022"`) |
| `provider` | `str` | LLM provider (e.g., `"anthropic"`) |
| `user_id` | `str \| None` | Authenticated user ID from session context |
| `route` | `str \| None` | Routing intent value (router node only) |
| `confidence` | `float \| None` | Routing confidence score (router node only) |

### Proposed Extensions

Three fields are added for KG layer nodes and sub-agents:

| Field | Type | Description |
|-------|------|-------------|
| `node_name` | `str` | Fully qualified node name (e.g., `"kg_retrieval"`, `"kg_generation"`, `"clarification"`, `"coach"`, `"generator"`, `"logger"`) |
| `source_type` | `str \| None` | Exercise source classification: `"SAFE_SET"`, `"PREFERRED"`, `"VECTOR_SEARCH"`, or `"FALLBACK"` (KG generation node only) |
| `source_id` | `str \| None` | Reference to origin Neo4j node ID or query string (KG nodes only) |

### Rationale

The schema is append-only and backward-compatible: existing hub nodes continue working without changes. KG nodes add the new fields; hub nodes leave them absent (`None`). No schema migration is required. The `node_name` field disambiguates between multiple nodes that emit the same `event` string during a single session (e.g., multiple `"coach"` invocations).

### Constraints

- No external payload storage: all entries are string, number, or nested dict — no binary blobs
- Entries are session-scoped and lost when the session is evicted from `_sessions` in `chat.py`
- No correlation IDs in Phase 1 (deferred enhancement)

---

## D2: Token Tracking Strategy

**Status**: Proposed

### Current Approach

`backend/app/agents/hub.py` lines 53–60 extract token counts from `raw_response.usage_metadata`:

```python
usage_meta = getattr(raw_response, "usage_metadata", None) or {}
tokens_in = usage_meta.get("input_tokens", 0)
tokens_out = usage_meta.get("output_tokens", 0)
```

The `or {}` guard and `.get(..., 0)` defaults ensure a missing or `None` `usage_metadata` attribute never causes a `KeyError` or `AttributeError`.

### Defensive Fallback Rule

Missing LLM metadata → `tokens_in = 0`, `tokens_out = 0`. The node still appends its audit entry. No exception is raised. This pattern is used uniformly across all nodes.

### Scope

| Node | LLM calls | Token tracking |
|------|-----------|---------------|
| Hub router (`backend/app/agents/hub.py` lines 43–78) | Yes — `ChatAnthropic` | Already implemented |
| Coach sub-agent | Yes — `ChatAnthropic` | Extend with defensive fallback |
| Generator sub-agent | Yes — `ChatAnthropic` | Extend with defensive fallback |
| Logger sub-agent | Yes — `ChatAnthropic` | Extend with defensive fallback |
| KG retrieval (`backend/app/kg/retrieval_graph.py`) | No direct LLM calls — Neo4j Cypher | Capture Neo4j query timing (`latency_ms`); set `tokens_in = 0`, `tokens_out = 0` |
| KG generation (`backend/app/kg/generation_graph.py`) | Yes — `ChatAnthropic` | Extend with defensive fallback |
| Explainability (`backend/app/kg/explainability.py`) | No direct LLM calls — Neo4j path traversal | Capture traversal timing; set `tokens_in = 0`, `tokens_out = 0` |

### Rationale

Token counts are the primary signal for LLM cost estimation. Defensive fallback prevents runtime errors during unit tests (where LLM calls are mocked and return synthetic objects without `usage_metadata`) and prevents crashes if the provider API changes the response shape.

---

## D3: Endpoint Exposure and RecommendedExercise Fields

**Status**: Proposed

### Existing Endpoint

`backend/app/routers/chat.py` lines 95–121 exposes:

```
GET /chat/audit/{session_id}
→ { session_id: str, audit_log: list[dict], total_entries: int }
```

### Proposed KG Audit Endpoint

Add a parallel endpoint for KG-specific audit entries:

```
GET /kg/audit/{session_id}
→ KgAuditResponse { session_id: str, audit_log: list[dict], total_entries: int }
```

`KgAuditResponse` mirrors the structure returned by `/chat/audit/{session_id}`. The KG router filters the session's `audit_log` to entries where `node_name` is one of `"kg_retrieval"`, `"kg_generation"`, `"kg_explainability"`.

### RecommendedExercise Schema Extensions

`backend/app/kg/generation_graph.py` lines 28–35 defines `RecommendedExercise`. Add three fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source_type` | `Literal["SAFE_SET", "PREFERRED", "VECTOR_SEARCH", "FALLBACK"]` | `"FALLBACK"` | How this exercise was selected by the KG layer |
| `source_id` | `str \| None` | `None` | Neo4j node ID or query reference for provenance |
| `confidence` | `float \| None` | `None` | Confidence score from `explain_skipped_exercise()` (Phase 3) |

These fields are optional with defaults, so existing callers that construct `RecommendedExercise` without them are unaffected.

### Rationale

`/kg/audit/{session_id}` provides a scoped view for KG debugging without polluting the chat audit endpoint. `RecommendedExercise` provenance fields close the explainability loop: the frontend can display why a specific exercise was recommended (SAFE_SET → curated; VECTOR_SEARCH → semantic match; FALLBACK → default).

---

## D4: Scope — In-Process Only

**Status**: Proposed

### Decision

No external observability stack is introduced: no LangFuse, OpenLLMetry, Prometheus, Grafana, or Arize Phoenix. All telemetry remains in-process, session-scoped, and in-memory.

### Rationale

This is an assessment-context decision. The `audit_log` pattern (established in `backend/app/agents/hub.py` lines 44–78) is sufficient for the observable requirements:

- **Explaining recommendations**: `explain_skipped_exercise()` reads `audit_log` entries and Neo4j path data to construct a rationale for each skipped exercise
- **Auditing routing decisions**: every intent classification and confidence score is captured by the router node
- **Tracking token usage**: per-node token counts support cost attribution
- **Debugging agent behavior**: ordered event sequence + latency per node is sufficient for local debugging

### Trade-offs

| Dimension | In-Process (chosen) | LangFuse / OpenLLMetry |
|-----------|--------------------|-----------------------|
| Operational overhead | None — no external services | High — requires SaaS account or self-hosted infra |
| Horizontal scalability | None — per-instance, in-memory | Full — centralized storage and dashboards |
| Distributed tracing | Not supported | Yes — OpenTelemetry traces span services |
| Data retention | Session lifetime only | Persistent, queryable |
| Setup complexity | Zero | Moderate to high |
| Assessment suitability | Ideal | Excessive |

### Scope Boundary

The in-process pattern can be replaced later: LangFuse and OpenLLMetry both offer SDK wrappers that accept the same event dicts. The `audit_log` list can be replayed into any external sink by changing only the node implementations, not the state schema or the REST endpoints.

---

## Alternatives Considered

- **LangFuse Cloud + OTel collector** (referenced in openemr ADR-0002) — out of scope; requires SaaS account, OTel collector sidecar, and external network access
- **OpenLLMetry → Arize Phoenix** (referenced in ai-adversary ADR-0011) — out of scope; requires self-hosted Arize Phoenix or Phoenix Cloud, adds Python SDK dependency
- **In-process + JSON file export** — deferred; not needed for assessment; straightforward to add as a background flush task
- **In-process + PostgreSQL event log table** — rejected; violates YAGNI, complicates the DB schema, adds migration overhead for a debug concern

---

## Implementation Notes

### Token Extraction Pattern

Defensive fallback used uniformly in all LLM-calling nodes:

```python
usage_meta = getattr(raw_response, "usage_metadata", None) or {}
tokens_in = usage_meta.get("input_tokens", 0)
tokens_out = usage_meta.get("output_tokens", 0)
```

This pattern is safe when `raw_response` is `None`, is a mock object without `usage_metadata`, or when the provider returns a response with a `None` metadata field.

### Per-Node Responsibility

Each node appends its own audit entry to `audit_log` before returning its state delta. The `AgentState` field `audit_log: list[dict[str, Any]]` (defined in `backend/app/agents/state.py` lines 40–54) is shared across all nodes in the hub graph. KG sub-graphs carry their own audit list and merge it into the session log at graph boundary.

### No Correlation IDs (Phase 1)

Individual audit entries are not linked by a trace ID. The ordered sequence within a session is the only correlation mechanism. Correlation IDs are a future enhancement (not in scope for ROADMAP-005 Phase 1).

### Confidence Scoring

`explain_skipped_exercise()` in `backend/app/kg/explainability.py` derives a confidence value from the Neo4j path depth and relationship strength. The exact algorithm is an implementation detail for Phase 3 of ROADMAP-005 and is out of scope for this ADR. The `RecommendedExercise.confidence` field (defined above in D3) reserves the slot.

---

## Links

<!-- To be filled when downstream tasks reference this ADR -->
