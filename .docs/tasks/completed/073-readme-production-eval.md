# 073 — README: "How I Would Evaluate This System in Production" Section

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [070-kg-chat-dashboard](070-kg-chat-dashboard.md), [071-feedback-submission-ui](071-feedback-submission-ui.md), [072-docker-compose-verification](072-docker-compose-verification.md)

## Objective

Add a "## How I Would Evaluate This System in Production" section to `README.md` covering: retrieval quality, safety monitoring, latency, and token efficiency. This is an Assessment 2 explicit requirement.

## Approach

The section should be substantive (~400–600 words), demonstrating production engineering judgment. Cover 4 dimensions:

1. **Retrieval Quality** — how to measure whether GraphRAG returns relevant context (precision/recall on held-out member scenarios, A/B vs. vector-only baseline, user feedback signal as implicit labels)
2. **Safety Monitoring** — how to ensure contraindicated exercises never reach users (safety gate bypass rate tracked as a metric, alert on any non-zero gate trips, adversarial red-teaming the LLM with "ignore the constraint" prompts)
3. **Latency** — target < 3s end-to-end; break down: Neo4j traversal (P99 < 100ms), vector search (P99 < 200ms), LLM generation (P99 < 2s); instrument with OpenTelemetry spans per node
4. **Token Efficiency** — track token_counts from `ContextSlice` per request; alert if total exceeds 2048; A/B test context budget allocations; cache member profiles for repeated users

## Steps

### 1. Read current `README.md` to find insertion point  <!-- agent: general-purpose -->

Use the `Read` tool on `README.md`. Find the last major section heading (e.g., "## Production Evaluation" if one exists, or the end of the file). Identify the exact line where the new section should be inserted.

- [x] Insertion point identified <!-- Completed: 2026-06-06 -->

### 2. Add the production evaluation section  <!-- agent: general-purpose -->

Use the `Edit` tool to add the following section (adjust wording as needed to sound natural in context):

```markdown
## How I Would Evaluate This System in Production

### Retrieval Quality

The core question is whether GraphRAG surfaces more relevant context than vector search alone. I would measure this with a held-out evaluation set of (member, query, expected_exercises) triples — synthetic but representative of real coaching scenarios. Key metrics:

- **Recall@K**: fraction of expected exercises appearing in the top-K retrieved results
- **Precision@K**: fraction of retrieved exercises that are truly relevant to the member's goals
- **Baseline comparison**: run the same queries with vector-only retrieval (no graph traversal) to quantify the graph's contribution

User feedback ratings (the 1–5 `FeedbackEvent` nodes) serve as implicit labels over time — exercises consistently rated 4–5 by a member should appear earlier in their retrieval results.

### Safety Monitoring

The injury safety gate is a hard constraint: contraindicated exercises must never appear in output. I would instrument:

- **Gate trip rate** (Prometheus counter): `kg_safety_gate_trips_total{reason="contraindicated"}`. Alert if non-zero in production — every trip means the LLM ignored an explicit instruction.
- **Adversarial testing**: prompt the LLM with "ignore the safe exercise list" injected into the user query; verify the gate catches any resulting violations.
- **Regression test suite**: the 5-case parameterized test in `test_kg_critical_injury_filtering.py` runs on every CI push.

### Latency

Target: < 3 seconds end-to-end (P95). Breakdown by sub-component:

| Component | Budget | Instrument |
|-----------|--------|------------|
| Neo4j traversal (all queries) | < 100ms P99 | `neo4j.session.run` span |
| Vector similarity search | < 200ms P99 | `similarity_search` span |
| LLM generation | < 2 000ms P99 | `ChatAnthropic.ainvoke` span |
| Context assembly + safety gate | < 50ms | function-level timing |

I would use OpenTelemetry with a LangSmith/Datadog backend. The `ContextSlice.token_counts` is already logged at INFO level — ship these to a metrics store and alert when `total > 1900` (approaching the 2048 budget).

### Token Efficiency

The 2048-token context budget (ADR-001 D3) is enforced by `_truncate_to_budget()`. In production I would:

1. **Track budget utilisation** per section via `token_counts` — histogram the distribution across requests.
2. **A/B test allocations**: member profile at 200, safe exercises at 600, preferred at 400, vector hits at 400 are reasonable starting points; if user ratings skew toward preferred exercises, shift budget toward that section.
3. **Member profile caching**: the member profile rarely changes between sessions. Cache it in Redis (TTL: 1 hour) to skip the Neo4j round-trip on repeat queries.
4. **Vector store warm-up**: the sentence-transformers model loads lazily; pre-warm on startup to avoid cold-start latency spikes.
```

- [x] Section added to `README.md` <!-- Completed: 2026-06-06 -->

### 3. Verify section renders correctly  <!-- agent: general-purpose -->

Use `Read` on `README.md` to confirm the section was inserted correctly, headings are at the right level, and the table is properly formatted.

- [x] Section renders correctly in Markdown <!-- Completed: 2026-06-06 -->

### 4. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 7 README placeholder with `[TASK-073: README production evaluation section...](../tasks/073-readme-production-eval.md)`.

- [x] Roadmap updated <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `README.md` contains `## How I Would Evaluate This System in Production` section
- [x] Section covers: retrieval quality, safety monitoring, latency, token efficiency
- [x] Latency table present with per-component budgets
- [x] Section length ~400–600 words (substantive, not a stub)

---
**UAT**: `.docs/uat/073-readme-production-eval.uat.md`
