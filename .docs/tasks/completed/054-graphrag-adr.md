# 054 — ADR: GraphRAG Retrieval Strategy

> **Depends on**: none
> **Blocks**: [055-vector-embeddings](055-vector-embeddings.md), [056-injury-traversal-queries](056-injury-traversal-queries.md), [057-preference-feedback-traversal](057-preference-feedback-traversal.md), [058-context-assembler](058-context-assembler.md), [059-retrieval-subgraph](059-retrieval-subgraph.md)
> **Parallel-safe with**: [033-critical-path-router-test](completed/033-critical-path-router-test.md), [034-critical-path-generator-test](completed/034-critical-path-generator-test.md), [049-injury-ingestion](049-injury-ingestion.md), [050-exercise-neo4j-ingestion](050-exercise-neo4j-ingestion.md), [051-member-profile-ingestion](051-member-profile-ingestion.md), [052-ingest-workout-history-neo4j](052-ingest-workout-history-neo4j.md), [053-feedback-ingestion-neo4j](053-feedback-ingestion-neo4j.md)

## Objective

Create an Architecture Decision Record (ADR) for the GraphRAG retrieval strategy, covering traversal depth, embedding model choice, context token budget, and the merge strategy for combining graph traversal results with vector search hits. This is a **design-only task** — no code is written; the output is a single ADR markdown file in `.docs/adr/`.

## Approach

Phase 4 of ROADMAP-004 begins with an intentional architecture pause. All downstream tasks (vector embeddings, traversal queries, context assembler, retrieval sub-graph) depend on decisions made here. The ADR must be written and marked `accepted` before any retrieval or generation code is written.

The ADR follows the standard format used in this project: Status, Context, Decision, Consequences, with a `### Links` section for task back-references.

Key decisions to resolve:
1. **Traversal depth**: 1-hop (direct HAS_INJURY / PERFORMED / FeedbackEvent edges) vs 2-hop (through intermediate nodes). Deeper traversal returns richer context but increases Cypher query latency and result set size.
2. **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (local, free, 384-dim) vs `text-embedding-3-small` (OpenAI API, 1536-dim, pay-per-use). Trade-offs: latency, cost, quality, offline capability.
3. **Context token budget**: Total ceiling (e.g. 2 048 tokens) and per-section allocation (safe exercises, preferred exercises, vector hits, member profile summary).
4. **Merge strategy**: How graph traversal results and vector similarity hits are deduplicated and ranked before being handed to the context assembler.

## Steps

### 1. Create the `.docs/adr/` directory if it does not exist  <!-- agent: general-purpose -->

Check whether `.docs/adr/` exists using `mcp__serena__list_dir` on `.docs/`. If the `adr` subdirectory is absent, create it by writing the ADR file directly into it (the `Write` tool will create intermediate directories as needed on most systems; alternatively use `Bash`: `mkdir -p .docs/adr`).

- [x] `.docs/adr/` directory exists before the ADR file is written <!-- Completed: 2026-06-06 -->

### 2. Research embedding model trade-offs  <!-- agent: general-purpose -->

Use Context7 and Brave Search (sequentially, 1 req/sec) to gather current data on:
- `sentence-transformers/all-MiniLM-L6-v2`: embedding quality on short fitness/exercise text, inference latency on CPU, memory footprint
- `text-embedding-3-small`: pricing per 1M tokens (check OpenAI pricing page), typical latency, 1536-dim vs 384-dim quality difference for short domain-specific text
- `langchain-neo4j` `Neo4jVector` class: which embedding providers it supports natively and how vector indexes are created

Queries to run (sequential):
1. Brave: `"sentence-transformers all-MiniLM-L6-v2" fitness exercise embedding quality benchmark 2024`
2. Context7: resolve `langchain-neo4j`, query `Neo4jVector embedding model configuration`
3. Brave: `OpenAI text-embedding-3-small vs sentence-transformers short text quality 2024`

- [x] Embedding model comparison notes captured for the ADR Context section <!-- Completed: 2026-06-06 -->
- [x] Neo4jVector supported embedding providers confirmed <!-- Completed: 2026-06-06 -->

### 3. Research graph traversal depth trade-offs  <!-- agent: general-purpose -->

Review the existing Neo4j schema in `.docs/knowledge-graph-schema.md` to identify all edges reachable from a `Member` node. Determine which edges are available at 1-hop vs 2-hop:

- 1-hop from Member: `HAS_INJURY`, `PERFORMED` (WorkoutSession), `HAS_GOAL`, `HAS_EQUIPMENT`, `HAS_AVAILABILITY`
- 2-hop from Member via WorkoutSession: `INCLUDED` → Exercise; via FeedbackEvent: `RATED` → Exercise
- 2-hop from Member via HAS_INJURY: through Injury → `CONTRAINDICATED_BY` → Exercise

Assess: does 2-hop traversal for injury filtering and feedback preference require 2-hop, or can it be expressed as a 1-hop pattern with relationship chaining in a single Cypher query (not truly 2-hop in the hop-count sense)?

- [x] Traversal depth decision justified with reference to schema edges <!-- Completed: 2026-06-06 -->

### 4. Define the context token budget  <!-- agent: general-purpose -->

Using the embedding model and traversal research, calculate a realistic token budget:
- Assume a total context ceiling of **2 048 tokens** for the retrieval context slice (leaving room for the system prompt and generation output in a 4k–8k context window).
- Allocate per-section budgets:
  - Member profile summary (goals, equipment, availability): ~200 tokens
  - Safe exercises (injury-filtered candidates, name + muscle_groups + movement_patterns): ~600 tokens (≈10 exercises × 60 tokens each)
  - Preferred exercises (high-rated + recently performed, name + why preferred): ~400 tokens
  - Vector similarity hits (top-k semantically similar, name + score): ~400 tokens
  - Buffer / merging overhead: ~448 tokens
- Document how deduplication works when the same exercise appears in multiple sections (prefer the section with the richest annotation; drop duplicates from lower-priority sections).

- [x] Token budget table defined with per-section allocations and deduplication rule <!-- Completed: 2026-06-06 -->

### 5. Write the ADR file  <!-- agent: general-purpose -->

Create `.docs/adr/001-graphrag-retrieval-strategy.md` using the `Write` tool. The file must follow this exact structure:

```markdown
# ADR-001: GraphRAG Retrieval Strategy

- **Status**: proposed
- **Date**: 2026-06-06
- **Deciders**: David Taylor
- **Tags**: graphrag, neo4j, embeddings, retrieval

## Context

[2–4 paragraphs explaining the problem, constraints, and why a decision is needed now.
Cover: what GraphRAG is in this system's context, the two retrieval mechanisms
(graph traversal + vector search), and why the merge strategy and token budget
matter for the generation agent downstream.]

## Decision

### D1. Traversal Depth

**Decision**: [1-hop or 2-hop — pick one and justify]

**Rationale**: [2–3 sentences]

**Consequences**:
- Positive: [...]
- Negative: [...]

---

### D2. Embedding Model

**Decision**: [sentence-transformers/all-MiniLM-L6-v2 OR text-embedding-3-small — pick one and justify]

**Rationale**: [2–3 sentences covering quality, cost, offline capability]

**Consequences**:
- Positive: [...]
- Negative: [...]

---

### D3. Context Token Budget

**Decision**: 2 048-token ceiling with the following per-section allocations:

| Section | Token budget |
|---------|-------------|
| Member profile summary | 200 |
| Safe exercises (injury-filtered) | 600 |
| Preferred exercises (feedback + history) | 400 |
| Vector similarity hits | 400 |
| Buffer | 448 |
| **Total** | **2 048** |

**Rationale**: [2–3 sentences]

**Consequences**:
- Positive: [...]
- Negative: [...]

---

### D4. Merge Strategy

**Decision**: [Describe how graph traversal results and vector hits are merged, deduplicated, and ranked. E.g.: "Graph traversal results are primary; vector hits are appended only if they do not duplicate an exercise already in the safe or preferred sets. Within each section, exercises are sorted by priority_tier (ascending). Deduplication key is exercise_id."]

**Rationale**: [2–3 sentences]

**Consequences**:
- Positive: [...]
- Negative: [...]

## Alternatives Considered

- [Alternative embedding model not chosen and why]
- [Alternative traversal depth not chosen and why]
- [Alternative merge strategy not chosen and why]

## Links

- ROADMAP-004 Phase 4: `.docs/roadmaps/004-knowledge-graph-coaching-system.md`
- Schema: `.docs/knowledge-graph-schema.md`
- Source task(s): `.docs/tasks/054-graphrag-adr.md` — **WIP** (added 2026-06-06)
```

Fill in all `[...]` placeholders with the actual decisions from steps 2–4. Do not leave any placeholder text in the final file.

- [x] ADR file created at `.docs/adr/001-graphrag-retrieval-strategy.md` <!-- Completed: 2026-06-06 -->
- [x] All 4 decision blocks (D1–D4) are filled with real decisions and rationale (no placeholder text) <!-- Completed: 2026-06-06 -->
- [x] Status is `proposed` (it becomes `accepted` after stakeholder review; this task only creates the proposed ADR) <!-- Completed: 2026-06-06 -->
- [x] Links section references ROADMAP-004, the schema doc, and this source task <!-- Completed: 2026-06-06 -->

### 6. Update the ROADMAP-004 Phase 4 section  <!-- agent: general-purpose -->

Read `.docs/roadmaps/004-knowledge-graph-coaching-system.md` with the `Read` tool. Replace the inline placeholder:

```
- [ ] ADR: GraphRAG retrieval strategy (traversal patterns, embedding model, context assembly token budget)
```

with:

```
- [ ] [TASK-054: ADR — GraphRAG retrieval strategy](../tasks/054-graphrag-adr.md)
```

Use the `Edit` tool. Update the `**Last updated**` line to `2026-06-06`.

- [x] Roadmap placeholder replaced with task link <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `.docs/adr/001-graphrag-retrieval-strategy.md` exists and is well-formed (all 4 decision blocks present, no placeholder text, status: proposed) <!-- Completed: 2026-06-06 -->
- [x] D1 (traversal depth) decision is justified with reference to schema edges <!-- Completed: 2026-06-06 -->
- [x] D2 (embedding model) decision is justified with cost/quality trade-off data <!-- Completed: 2026-06-06 -->
- [x] D3 (token budget) decision includes a per-section allocation table that sums to ≤ 2 048 <!-- Completed: 2026-06-06 -->
- [x] D4 (merge strategy) defines deduplication key and sort order <!-- Completed: 2026-06-06 -->
- [x] ROADMAP-004 Phase 4 inline item replaced with task link <!-- Completed: 2026-06-06 -->
- [x] `.docs/tasks/README.md` Active Tasks table updated with this task (TASK-054) <!-- Already present -->

---
**UAT**: [`.docs/uat/completed/054-graphrag-adr.uat.md`](../uat/completed/054-graphrag-adr.uat.md)
