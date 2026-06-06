# 074 — Write Observability Stack ADR

> **Depends on**: none
> **Blocks**: [075-instrument-kg-hub-node](075-instrument-kg-hub-node.md), [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md), [078-instrument-explainability-tool](078-instrument-explainability-tool.md)
> **Parallel-safe with**: none

## Objective

Document the decision to extend the existing in-process `audit_log` pattern from the hub router to all agent sub-graphs and knowledge graph layers, establishing a lightweight observability stack with no external dependencies. This ADR will define the audit entry schema, token tracking strategy, endpoint exposure, and scope, enabling instrumentation tasks to proceed with a clear, reviewed design.

## Approach

The ADR will follow the project's decision template (see `.docs/adr/README.md`) with the following key sections:

1. **Status**: Proposed (will be finalized after feedback)
2. **Decision blocks** (D1–D4):
   - **D1**: Audit entry schema — extensible dictionary with event, latency_ms, tokens, model/provider, and node-specific fields (route, source_type, etc.)
   - **D2**: Token tracking strategy — conservative fallback (missing metadata → 0, no crash), per-node counting
   - **D3**: Endpoint exposure — extend existing `/audit/{session_id}` pattern to KG layer (`/kg/audit/{session_id}`) and add source provenance fields to `RecommendedExercise`
   - **D4**: Scope — in-process only, no external observability stack (LangFuse, OpenLLMetry, Grafana), trade-off: demo-suitable but not horizontally scalable

3. **References**: External ADR patterns from openemr and ai-adversary (for context, not implementation)

4. **Trade-offs section**: Document why in-process is correct for this assessment (lightweight, no operational overhead, sufficient for explainability and audit), but note limitations for production use

5. **Alternatives considered**: Brief section on LangFuse/OpenLLMetry/Grafana stacks and why they're out of scope

## Steps

### 1. Create ADR file structure  <!-- agent: general-purpose -->

Create `.docs/adr/0005-observability-stack.md` with:
- Front matter: title, status (proposed), created date, owner (David Taylor)
- Executive summary (2–3 sentences explaining in-process audit_log extension)
- Context section describing existing audit_log in hub.py lines 44–78, current `/audit/{session_id}` endpoint, and gap: no KG layer or sub-agent instrumentation

- [x] ADR file created with front matter and context section <!-- Completed: 2026-06-06 -->

### 2. Document decision D1: Audit entry schema  <!-- agent: general-purpose -->

Under `## D1: Audit Entry Schema`, write:
- Current schema (event, latency_ms, tokens_in, tokens_out, model, provider, user_id, route, confidence)
- Proposed extensions: source_type (SAFE_SET | PREFERRED | VECTOR_SEARCH | FALLBACK), source_id (optional), node_name (clarification, coach, generator, logger, kg_retrieval, kg_generation)
- Rationale: every node becomes observable without schema migration (append-only, backward-compatible)
- Constraints: no external payload storage, string/number/dict only (no binary)

- [x] D1 decision block written with schema table and rationale <!-- Completed: 2026-06-06 -->

### 3. Document decision D2: Token tracking strategy  <!-- agent: general-purpose -->

Under `## D2: Token Tracking`, write:
- Current approach: extract from LLM response.usage_metadata
- Defensive fallback: missing metadata → 0 (not crash)
- Proposed scope: hub router, coach, generator, logger nodes. KG nodes (retrieval, generation) may not have direct LLM calls; capture Neo4j query timing separately
- Rationale: token counts help assess LLM cost and latency; fallback prevents runtime errors in mocks or uncounted nodes

- [x] D2 decision block written with strategy and examples <!-- Completed: 2026-06-06 -->

### 4. Document decision D3: Endpoint exposure and RecommendedExercise fields  <!-- agent: general-purpose -->

Under `## D3: Endpoint Exposure`, write:
- Extend `/audit/{session_id}` to `/kg/audit/{session_id}` for knowledge graph-specific entries (retrieval, generation, explainability)
- Add fields to `RecommendedExercise` model (backend/app/kg/generation_graph.py line 29):
  - `source_type: Literal["SAFE_SET" | "PREFERRED" | "VECTOR_SEARCH" | "FALLBACK"]`
  - `source_id: str | None` — reference to the origin node/query
  - `confidence: float | None` — from explain_skipped_exercise()
- Response schema: `KgAuditResponse` with session_id, audit_log, total_entries (mirror of `/chat/audit`)

- [x] D3 decision block written with endpoint contracts and RecommendedExercise schema <!-- Completed: 2026-06-06 -->

### 5. Document decision D4: Scope — in-process only  <!-- agent: general-purpose -->

Under `## D4: Scope — In-Process Only`, write:
- Decision: no external observability stack (no LangFuse, OpenLLMetry, Prometheus, Grafana, Arize Phoenix)
- Rationale:
  - Assessment context: lightweight, no operational overhead, self-contained repo
  - In-memory `audit_log` sufficient for: explaining recommendations, auditing routing decisions, tracking token usage, debugging agent behavior
  - Explainability tool (explain_skipped_exercise) reads Neo4j + audit_log to construct rationale
- Trade-offs table:
  - In-process: simple, no external deps, but unscalable, no distributed tracing, limited retention (session-scoped)
  - LangFuse/OpenLLMetry: scalable, distributed, but adds operational complexity, external SaaS/infra cost, not needed for assessment
- Conclusion: accept the limitation; external stack can be swapped later (SDKs are LLM-agnostic)

- [x] D4 decision block written with rationale, trade-offs table, and scope boundary <!-- Completed: 2026-06-06 -->

### 6. Write alternatives section  <!-- agent: general-purpose -->

Under `## Alternatives Considered`, briefly list (one line each):
- LangFuse Cloud + OTel collector (from openemr ADR-0002) — out of scope, requires SaaS integration
- OpenLLMetry → Arize Phoenix (from ai-adversary ADR-0011) — out of scope, requires external infrastructure
- In-process + JSON file export — deferred (not needed for assessment)
- In-process + PostgreSQL event log table — rejected (violates YAGNI, complicates schema)

- [x] Alternatives section written <!-- Completed: 2026-06-06 -->

### 7. Add rationale and implementation notes  <!-- agent: general-purpose -->

Add section `## Implementation Notes` with:
- Token extraction pattern (defensive fallback from LangChain response.usage_metadata)
- Per-node responsibility: each node appends its own entry to audit_log before returning
- No correlation IDs yet: future enhancement if needed (not in scope for Phase 1)
- Confidence scoring: explain_skipped_exercise() derives from Neo4j path depth/strength (out of scope for ADR; implementation detail for Phase 3)

- [x] Implementation notes section added <!-- Completed: 2026-06-06 -->

### 8. Finalize status and get feedback  <!-- agent: general-purpose -->

Review the ADR for completeness:
- All 4 decisions documented with rationale
- Links to reference code (hub.py, state.py, chat.py, generation_graph.py)
- No unresolved questions or TBDs in decision sections
- Status remains "Proposed" (to be finalized after review)

Leave `### Links` section empty (will be filled when this task links to the ADR).

- [x] ADR reviewed for completeness; status set to "Proposed" <!-- Completed: 2026-06-06 -->
- [x] File committed with message referencing ROADMAP-005 <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] ADR file exists at `.docs/adr/0005-observability-stack.md`
- [x] All 4 decision blocks (D1–D4) are documented with Status, Rationale, and Alternatives
- [x] Decision D1 specifies the audit entry schema (including source_type, source_id, confidence)
- [x] Decision D2 specifies token tracking strategy (defensive fallback pattern)
- [x] Decision D3 specifies endpoint contracts (/kg/audit/{session_id}, RecommendedExercise fields)
- [x] Decision D4 documents in-process scope with trade-offs table
- [x] All decisions reference the existing code (hub.py, state.py, chat.py, generation_graph.py) by line number
- [x] ADR is committed to the repository <!-- Completed: 2026-06-06 -->
