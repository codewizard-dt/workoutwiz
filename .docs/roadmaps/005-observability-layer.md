# Roadmap 005: Observability Layer

> Instrument every agent routing decision and KG sub-graph node with in-process audit tracing, add source provenance and explainability confidence metrics, and expose all telemetry via REST endpoints — no external stack required.

- **Status**: active
- **Created**: 2026-06-06
- **Last updated**: 2026-06-06
- **Owner**: David Taylor
- **Linked PRD**: —
- **Linked ADRs**: —
- **Tags**: observability, agents, kg

## Goal

Every agent routing decision in the hub and all knowledge graph sub-graph nodes is traced via the existing in-process `audit_log` pattern (ported from the hub router). Recommended exercises carry `source_type` (SAFE_SET | PREFERRED | VECTOR_SEARCH | FALLBACK) and `source_id`. The explainability tool returns a `confidence` score derived from Neo4j path traversal. All telemetry is accessible without an external stack via `/chat/audit/{session_id}` and a new `/kg/audit/{session_id}` endpoint.

## Phase 1: ADR

> Document the observability stack decision before writing any instrumentation code.

- [ ] Write ADR for observability stack — adapt openemr ADR-0002 and ai-adversary ADR-0011, deciding on in-process audit_log extension (no external stack)

## Phase 2: Instrumentation

> Extend audit_log coverage to every KG layer node that currently has zero observability.

- [ ] Instrument KG hub node routing trace — add audit entry capturing intent, confidence, and latency for the KG invocation decision
- [ ] Instrument retrieval sub-graph nodes — add timing and result-count audit entries to lookup_member, run_injury_traversal, run_preference_traversal, run_vector_search, and assemble nodes
- [ ] Instrument generation sub-graph nodes — add audit entries to safety gate, generation, and fallback handler nodes with exercise in/out counts and safety violations filtered
- [ ] Instrument explainability tool — add Neo4j query latency and result-count audit entry to explain_skipped_exercise()

## Phase 3: Metrics

> Add structured metric fields that the assessor and future monitoring can query against.

- [ ] Add source_id/source_type to RecommendedExercise — extend with source_type enum (SAFE_SET | PREFERRED | VECTOR_SEARCH | FALLBACK) and source_id, populated during recommendation assembly
- [ ] Add explainability confidence score — return a confidence float from explain_skipped_exercise() based on Neo4j path traversal depth/strength
- [ ] Add GET /kg/audit/{session_id} endpoint — expose KG-specific audit log entries separate from /chat/audit

## Phase 4: Tests

> Verify trace coverage and metric population end-to-end.

- [ ] Test routing trace coverage — assert audit_log contains hub, retrieval, and generation node entries with non-zero latency_ms after a KG recommendation call
- [ ] Test source_id/source_type population — assert every exercise in a recommendation response has source_type set
- [ ] Test explainability confidence — assert explain_skipped_exercise() returns a confidence float between 0 and 1
- [ ] Test audit endpoint — assert GET /kg/audit/{session_id} returns a non-empty list with expected event keys

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
