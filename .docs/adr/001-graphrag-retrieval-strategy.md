# ADR-001: GraphRAG Retrieval Strategy

- **Status**: proposed
- **Date**: 2026-06-06
- **Deciders**: David Taylor
- **Tags**: graphrag, neo4j, embeddings, retrieval

## Context

The coaching system's generation agent must produce injury-aware, personalized workout recommendations. To do this it needs a context slice — a compact, token-budgeted block of structured information about the member — assembled before the LLM call. Two complementary retrieval mechanisms produce that context: **graph traversal** (Cypher queries against Neo4j using the typed schema in `.docs/knowledge-graph-schema.md`) and **vector search** (approximate nearest-neighbor over exercise description embeddings stored in the `exercise_embeddings` vector index).

Graph traversal gives precise, relationship-grounded signals: which exercises are contraindicated by a member's active injuries, which exercises the member has rated highly, and which exercises appeared in recent sessions. Vector search gives semantic coverage: exercises whose descriptions are semantically close to a natural-language coaching prompt (e.g. "upper body push with no shoulder loading"), surfacing relevant exercises that have not yet been rated or recently performed.

The two mechanisms are complementary but overlapping: the same exercise can appear as a graph-traversal hit (because the member rated it 5 stars) and as a vector hit (because its description matches the prompt). Without a defined merge and deduplication strategy, the context slice will bloat, exceed the token budget, and cause the generation agent to produce incoherent or repetitive output.

Decisions D1–D4 below lock in the traversal depth, embedding model, token budget, and merge strategy that all downstream tasks (TASK-055 through TASK-059) must follow. These decisions are made now because they constrain the vector index schema (dimensions, similarity function), the Cypher query shape (1-hop vs 2-hop), and the context assembler data contract.

## Decision

### D1. Traversal Depth

**Decision**: Use **effective 1-hop traversal** from the `Member` node for all retrieval queries, leveraging pre-computed edges (`CONTRAINDICATED_BY`, `RATED`) and property-array intersection for joint matching.

**Rationale**: The schema's `CONTRAINDICATED_BY` edge is pre-computed at ingestion time (Injury ingestion writes `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)` for every joint-overlap pair), so filtering unsafe exercises requires only a 1-hop check from Exercise to Injury — no intermediate node traversal. The `RATED` relationship is a direct `(Member)-[:RATED]->(Exercise)` denormalized edge (copied from `FeedbackEvent` nodes at ingestion), making preference lookup a single hop. Workout history traversal (`Member → WorkoutSession → Exercise`) is technically 2 hops but is expressed as a single Cypher `MATCH` path with two relationship steps — this is a path pattern, not a conceptually deeper traversal. All patterns stay within a single Cypher query and return results in O(log N) time against indexed nodes.

**Consequences**:
- Positive: All Cypher queries can be expressed without APOC or variable-length path operators, keeping them simple, auditable, and fast (all traversal anchors are on indexed properties).
- Positive: The `CONTRAINDICATED_BY` pre-computation means the safety-critical path is a property lookup, not a runtime set-intersection join.
- Negative: If the schema later requires multi-hop reasoning (e.g. "friend-of-a-friend who performed this exercise also reported this injury"), the traversal layer will need to be extended. This is acceptable given YAGNI — no such requirement exists now.

---

### D2. Embedding Model

**Decision**: Use **`text-embedding-3-small`** (OpenAI API, 1536 dimensions, cosine similarity).

**Rationale**: The knowledge graph schema (`description_embedding` field on `Exercise`, vector index declaration in `.docs/knowledge-graph-schema.md`) already specifies `vector.dimensions: 1536` and references `text-embedding-3-small` / `text-embedding-ada-002` as the intended model. Changing to a 384-dim local model (e.g. `sentence-transformers/all-MiniLM-L6-v2`) would require rebuilding the vector index and changing the schema — an incompatible change. Additionally, the project already requires an OpenAI API key for the LangGraph hub router (LLM structured output), so the API key is available at runtime; there is no offline-capability benefit to a local model in this deployment context. `text-embedding-3-small` at 1536 dimensions provides higher retrieval quality on short fitness domain text than 384-dim sentence-transformers models, and its per-token cost ($0.02/1M tokens as of mid-2025) is negligible given the exercise corpus size (50 exercises × ~100 tokens each = ~5 000 tokens per full re-embed, < $0.0001).

**Consequences**:
- Positive: Schema consistency — the vector index schema and `Exercise.description_embedding` field are already specified for 1536 dimensions; no migration needed.
- Positive: Higher-quality semantic retrieval for fitness domain text compared to general-purpose 384-dim models.
- Positive: No additional Python dependency or model download required at container startup.
- Negative: Requires an OpenAI API key (`OPENAI_API_KEY`) to be present at ingestion and retrieval time; pure offline operation is not possible.
- Negative: Embedding calls incur network latency (~100–300 ms per query embedding at runtime). This is mitigated by running the query embedding asynchronously while graph traversal queries execute in parallel.

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

**Rationale**: A 2 048-token retrieval context slice leaves adequate room for the system prompt (~500 tokens), the member's natural-language coaching request (~100 tokens), and the generation output (~1 000–1 500 tokens) within a standard 4 096-token context window, or comfortably within an 8 192-token window. Per-section allocations are sized to the expected content density: the member profile summary (goals, equipment, availability) is terse structured text (~200 tokens); safe exercises are rendered as `name | muscle_groups | priority_tier` rows at ~60 tokens each, yielding ~10 exercises; preferred exercises include a "why preferred" annotation (rating or recency signal) at ~40 tokens each, yielding ~10 exercises; vector hits include a similarity score and are rendered without annotations at ~40 tokens each, yielding ~10 hits. The 448-token buffer absorbs section headers, deduplication overhead, and prompt template boilerplate.

**Consequences**:
- Positive: The context assembler has a deterministic, testable budget — it can truncate or skip lower-priority sections without exceeding the ceiling.
- Positive: The per-section caps prevent any single retrieval mechanism from crowding out the others (e.g. a member with 50 rated exercises does not flood the preferred-exercises section).
- Negative: With a 60-token-per-exercise rendering budget, rich exercise descriptions cannot be included verbatim; only `name`, `muscle_groups`, and `priority_tier` are included in the safe-exercises section.

---

### D4. Merge Strategy

**Decision**: Graph traversal results are primary; vector hits are appended only if their `exercise_id` does not already appear in the safe-exercises or preferred-exercises sets. Within each section, exercises are ranked by `priority_tier` ascending (tier 1 = highest quality first). Deduplication key is `exercise_id`. Section priority order for deduplication: safe-exercises > preferred-exercises > vector-hits (i.e. if an exercise appears in both safe and vector-hits, it is kept in safe and dropped from vector-hits).

**Rationale**: Graph traversal results carry stronger personalization signal (they are grounded in the member's actual injury record and explicit ratings) and must therefore take precedence in the final context slice. Vector hits provide semantic coverage for exercises not yet in the member's preference graph, so they are additive rather than competitive. Deduplication by `exercise_id` before token counting ensures the budget is not wasted on duplicate information. Ranking by `priority_tier` within each section ensures the highest-quality exercises appear first when a section must be truncated to fit its token budget.

**Consequences**:
- Positive: The context slice is deduplicated by construction — the generation agent never sees the same exercise in two sections.
- Positive: The ranking rule (`priority_tier ASC`) is deterministic and stable across runs, making the system's output easier to test and audit.
- Negative: An exercise that scores very highly on vector similarity but also appears in the safe-exercises set will be dropped from the vector-hits section; its semantic relevance score is not surfaced to the generation agent. This is an acceptable loss — the exercise is already in context via a higher-priority signal.

## Alternatives Considered

- **`sentence-transformers/all-MiniLM-L6-v2` (384-dim, local)**: Rejected because the schema already specifies a 1536-dim vector index. Rebuilding the index for 384 dimensions would break the schema contract established in TASK-043 and TASK-044 without a clear quality or cost benefit, since the OpenAI API key is already required for the hub router LLM.

- **2-hop traversal** (e.g. `Member → HAS_INJURY → Injury → CONTRAINDICATED_BY → Exercise` as a graph path rather than a pre-computed edge): Rejected because the `CONTRAINDICATED_BY` edge is pre-computed at injury ingestion time, making this pattern redundant. Variable-length or multi-hop Cypher patterns are harder to optimize and more brittle under schema evolution.

- **Flat merge with score-weighted ranking** (combine graph and vector results into a single ranked list by blending traversal relevance and cosine similarity scores): Rejected because the two retrieval mechanisms produce incommensurable scores (graph traversal returns categorical signals like rating and recency; vector search returns a cosine distance). A blended ranking would require arbitrary score normalization weights that are difficult to tune and explain. The section-based merge strategy is simpler, more explainable, and directly maps to the token budget structure.

## Links

- ROADMAP-004 Phase 4: `.docs/roadmaps/004-knowledge-graph-coaching-system.md`
- Schema: `.docs/knowledge-graph-schema.md`
- Source task: `.docs/tasks/054-graphrag-adr.md` — **proposed** (added 2026-06-06)
