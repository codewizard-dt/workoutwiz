# Roadmap 005: Observability Layer

> Instrument every agent routing decision and KG sub-graph node with in-process audit tracing, add source provenance and explainability confidence metrics, and expose all telemetry via REST endpoints — no external stack required.

- **Status**: active
- **Created**: 2026-06-06
- **Last updated**: 2026-06-06 (TASK-082 completed)
- **Owner**: David Taylor
- **Linked PRD**: —
- **Linked ADRs**: —
- **Tags**: observability, agents, kg

## Goal

Every agent routing decision in the hub and all knowledge graph sub-graph nodes is traced via the existing in-process `audit_log` pattern (ported from the hub router). Recommended exercises carry `source_type` (SAFE_SET | PREFERRED | VECTOR_SEARCH | FALLBACK) and `source_id`. The explainability tool returns a `confidence` score derived from Neo4j path traversal. All telemetry is accessible without an external stack via `/chat/audit/{session_id}` and a new `/kg/audit/{session_id}` endpoint.

## Phase 1: ADR

> Document the observability stack decision before writing any instrumentation code.

- [x] [TASK-074: Write Observability Stack ADR](../tasks/completed/074-observability-adr.md)

## Phase 1.5: Persistence

> Persist audit entries to Postgres so telemetry survives beyond the in-memory session lifetime and can be queried directly.

- [x] [TASK-083: Persist audit_log entries to Postgres](../tasks/completed/083-persist-audit-log-to-postgres.md)

## Phase 2: Instrumentation

> Extend audit_log coverage to every KG layer node that currently has zero observability.

- [x] [TASK-075: Instrument KG Hub Node Routing Trace](../tasks/completed/075-instrument-kg-hub-node.md)
- [x] [TASK-076: Instrument Retrieval Sub-Graph Nodes](../tasks/completed/076-instrument-retrieval-nodes.md)
- [x] [TASK-077: Instrument Generation Sub-Graph Nodes](../tasks/completed/077-instrument-generation-nodes.md)
- [x] [TASK-078: Instrument Explainability Tool](../tasks/completed/078-instrument-explainability-tool.md)

## Phase 3: Metrics

> Add structured metric fields that the assessor and future monitoring can query against.

- [x] [TASK-079: Add source_id/source_type to RecommendedExercise](../tasks/completed/079-add-source-fields-to-recommended-exercise.md)
- [x] [TASK-080: Add Explainability Confidence Score](../tasks/completed/080-add-explainability-confidence-score.md)
- [ ] [TASK-081: Add GET /kg/audit/{session_id} Endpoint](../tasks/081-add-kg-audit-endpoint.md)

## Phase 4: Tests

> Verify trace coverage and metric population end-to-end.

- [x] [TASK-082: Test Routing Trace Coverage](../tasks/completed/082-test-routing-trace-coverage.md)
- [ ] [TASK-084: Test source_id/source_type population](../tasks/084-test-source-type-population.md)
- [x] Test explainability confidence — assert explain_skipped_exercise() returns a confidence float between 0 and 1
- [ ] [TASK-085: Test KG Audit Endpoint](../tasks/085-test-kg-audit-endpoint.md)

## Notes

Reference ADRs (external repos, for context):
- `openemr/.docs/adr/0002-agent-observability-stack.md` — LangFuse Cloud + OTel Collector hybrid (superseded in openemr by ADR-0007)
- `ai-adversary/.docs/adr/completed/0011-observability-stack.md` — OpenLLMetry → Arize Phoenix + Prometheus + Grafana

Key existing files for implementors:
- `backend/app/agents/hub.py` lines 44–78 — reference audit entry pattern (timing + tokens)
- `backend/app/agents/state.py` lines 41–56 — `AgentState` TypedDict with `audit_log` field
- `backend/app/kg/retrieval_graph.py` — retrieval sub-graph nodes, no instrumentation yet
- `backend/app/kg/generation_graph.py` line 29 — `RecommendedExercise` model, needs source_type/source_id
- `backend/app/kg/explainability.py` — `explain_skipped_exercise()`, no instrumentation yet
- `backend/app/routers/chat.py` lines 36–141 — reference audit endpoint pattern
