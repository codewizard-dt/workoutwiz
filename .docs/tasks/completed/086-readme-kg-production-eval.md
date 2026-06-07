# 086 — README: KG System Production Evaluation Section

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [087-fix-stale-intent-values-test](087-fix-stale-intent-values-test.md), [088-build-workout-cooldown-phase](088-build-workout-cooldown-phase.md), [089-subagent-llm-error-handling](089-subagent-llm-error-handling.md)

## Objective

Add a clearly-labelled, KG-focused subsection to the root `README.md` that explains how to evaluate the knowledge-graph / GraphRAG system in production, satisfying Assessment 2 requirement 9 (`.docs/guides/2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md`) with a named-metric table covering retrieval quality, injury-safety monitoring, GraphRAG latency, concept-resolution failure modes, and "how you'd know it's working".

## Approach

The root `README.md` already has a `## How I Would Evaluate This System in Production` section (currently subsections: Retrieval Quality, Safety Monitoring, Latency, Token Efficiency) added by completed task 073 — that prose is generic and not framed as a distinct KG subsection, its latency target (< 3 s) conflicts with the Assessment 2 ~5 s target, and it has no named-metric table, no concept-resolution failure modes, and no explicit "how you'd know it's working" summary. Add a new `### Knowledge Graph (GraphRAG) System` subsection that closes those gaps in a scannable metric-table form, mirroring the table style of the `## Production Evaluation` section in `.docs/guides/1-multi-agent/README.md`. Reconcile with the existing prose rather than duplicating it.

## Prerequisites

- [ ] Read the existing `## How I Would Evaluate This System in Production` section in the root `README.md` (currently ~lines 461–502) and note its four subsections (Retrieval Quality, Safety Monitoring, Latency, Token Efficiency) so the new KG subsection complements rather than duplicates them.
- [ ] Read the `## Production Evaluation` → `### Key Metrics to Monitor` table in `.docs/guides/1-multi-agent/README.md` (the `| Metric | Target | How to measure |` table) to mirror its column layout and target-value style.
- [ ] Read Assessment 2 requirement 9 and the Performance note in `.docs/guides/2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md` (the section requires "retrieval quality, safety/failure modes to monitor, latency, and how you'd know it's working"; the Performance note sets the "~5 seconds" AI-response target).

---

## Steps

### 1. Confirm the insertion point and reconcile with the existing section  <!-- agent: general-purpose -->

- [ ] Open the root `README.md` (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md`) and locate the existing `## How I Would Evaluate This System in Production` heading (currently ~line 461) and its `### Token Efficiency` subsection (currently the last subsection, ~line 494).
  - Decide placement: insert the new `### Knowledge Graph (GraphRAG) System` subsection under the existing `## How I Would Evaluate This System in Production` heading, immediately after the `### Token Efficiency` subsection, so all production-eval material stays under one H2.
- [ ] Verify the existing Latency subsection states "< 3 seconds end-to-end". Note that Assessment 2's Performance target is "~5 seconds"; the new KG metric table must use a GraphRAG end-to-end target of **< 5 s (P95)** to align with `KNOWLEDGE_GRAPH_ASSESSMENT.md`. Do not silently contradict the existing 3 s figure — if it is left in place, add a one-line note in the new subsection clarifying that the 5 s figure is the Assessment 2 acceptance target for the full GraphRAG path (member lookup → SNOMED traversal → vector search → assembly → LLM → safety gate).

### 2. Add the KG-focused production-eval subsection  <!-- agent: general-purpose -->

- [ ] Insert a new `### Knowledge Graph (GraphRAG) System` subsection in the root `README.md` under `## How I Would Evaluate This System in Production`, after `### Token Efficiency`, opening with one sentence stating these signals cover the SNOMED-grounded injury-aware retrieval/generation path (route `KNOWLEDGE_GRAPH`).
  - Use the H3/H4 heading levels consistent with the surrounding section (`### Knowledge Graph (GraphRAG) System` as the subsection, `####` for any inner groupings).
- [ ] Add a **named-metric table** with the columns `| Metric | Target | How you'd know it's working |` (mirroring the `.docs/guides/1-multi-agent/README.md` `### Key Metrics to Monitor` table style) containing at least these rows:
  - **Safe-exercise retrieval Recall@K** — Target **≥ 0.95** — measured on a held-out set of (member, query, expected_safe_exercises) triples; fraction of expected safe exercises in top-K.
  - **Safe-exercise retrieval Precision@K** — Target **≥ 0.80** — fraction of retrieved exercises actually relevant to the member's goal/equipment.
  - **Contraindicated-leak rate** — Target **0% (hard gate)** — count of contraindicated exercises that reach the user / total recommendations; mirror the `Invalid ID rate | 0 %` row from `.docs/guides/1-multi-agent/README.md`. Any non-zero value is a release blocker.
  - **Safety-gate trip rate** — Target **0 in prod** — `kg_safety_gate_trips_total{reason="contraindicated"}` Prometheus counter; a non-zero trip means the LLM proposed a contraindicated exercise that the post-generation gate had to filter (the gate held, but the generator regressed).
  - **GraphRAG end-to-end latency (P95)** — Target **< 5 s** — full path member lookup → SNOMED injury traversal → vector search → context assembly → LLM generation → safety gate; cite the Assessment 2 "~5 seconds" Performance target.
  - **Concept-resolution rate** — Target **≥ 0.90** — fraction of free-text injury complaints that resolve to a SNOMED concept / `Disorder` node (vs. falling back to string matching).
  - **Context-window token budget (P95)** — Target **< 2048 tokens/turn** — from `ContextSlice.token_counts`; alert when `total > 1900` (approaching the budget), consistent with the existing `### Token Efficiency` and `### Latency` notes.
- [ ] Add a **per-stage latency breakdown table** (`| Stage | Budget | Instrument |`) so the < 5 s end-to-end target is decomposed, mirroring the existing `### Latency` table but summing to the 5 s GraphRAG target:
  - Neo4j SNOMED injury traversal — < 100 ms P99 — `neo4j.session.run` span.
  - Vector similarity search — < 300 ms P99 — `similarity_search` span.
  - Context assembly + safety gate — < 100 ms — function-level timing.
  - LLM generation — < 4 s P95 — `ChatAnthropic.ainvoke` span (dominant cost; reference the `kg_generation_llm` audit event).
- [ ] Add a **Retrieval quality** paragraph: held-out (member, query, expected_safe_exercises) eval set (synthetic, per `KNOWLEDGE_GRAPH_ASSESSMENT.md` "use synthetic data"); Recall@K / Precision@K as above; A/B baseline vs. vector-only retrieval to prove the graph does real work (the assessment's "is the graph doing real work, or semantic search with extra steps?" criterion); and 1–5 `FeedbackEvent` ratings as implicit relevance labels over time. Cross-reference the existing `### Retrieval Quality` subsection instead of restating it.
- [ ] Add an **Injury-safety monitoring** paragraph: the contraindicated-leak rate is the single most important metric and must stay at **0%**; the safety gate runs *after* LLM generation (post-generation filter, by design, to resist prompt-injection bypass); adversarial red-team prompts ("ignore the safe exercise list" injected into the query) must still produce 0 leaks; and the regression gate is the parameterized injury-filtering critical-path test (`test_kg_critical_injury_filtering.py`) on every CI push.
- [ ] Add a **Concept-resolution failure modes** paragraph (NEW vs. the existing section) covering at least:
  - Free-text complaint fails to map to any SNOMED `Disorder` / `Injury` node (low embedding similarity) → traversal yields no constraints → risk of recommending into an unscreened joint. Signal: `concept_resolution_rate` drop; `result_count=0` / `constraint_count=0` on the `retrieval_injury_traversal` audit event for a member with known injuries.
  - Ambiguous or multi-joint complaints (e.g. "my leg hurts") resolving to the wrong joint or too broad a `BodyStructure`.
  - Missing `MAPS_TO_DISORDER` edges (Injury nodes seeded before SNOMED ingestion) forcing a fallback to `CONTRAINDICATED_BY` string matching instead of graph traversal. Mitigation/signal: `snomed_provenance_records = 0` for a member with active injuries → re-run `ingest_snomed.py`.
  - SNOMED snapshot drift between editions causing stale concept codes.
- [ ] Add a short **"How you'd know it's working"** wrap-up (explicitly required by Assessment 2 req 9): in steady state, contraindicated-leak rate and safety-gate trip rate are both 0, Recall@K/Precision@K hold above target on the held-out set, GraphRAG P95 stays under 5 s, concept-resolution rate stays above 0.90, and every recommendation carries a SNOMED-grounded provenance trace (reference the `Injury-Aware Recommendation — Live Trace` block already in the README).

### 3. Verification  <!-- agent: general-purpose -->

- [ ] Re-read the edited `README.md` and confirm the new `### Knowledge Graph (GraphRAG) System` subsection renders under `## How I Would Evaluate This System in Production`, all tables have aligned pipes and a header separator row, and heading levels are consistent with neighbours.
- [ ] Confirm the subsection covers all five required topics: retrieval quality (Recall@K / Precision@K), injury-safety monitoring (contraindicated-leak rate = 0%), GraphRAG latency (< 5 s target), concept-resolution failure modes, and an explicit "how you'd know it's working" summary.
- [ ] Confirm every metric target traces to a real source: the `0 %` hard-gate framing matches `.docs/guides/1-multi-agent/README.md`'s `Invalid ID rate` row, the `< 5 s` figure matches the `KNOWLEDGE_GRAPH_ASSESSMENT.md` Performance note, and the 2048-token budget matches the existing `### Token Efficiency` subsection.
- [ ] Confirm code fences (if any added) are balanced (even count) and all relative links/anchors referenced in the subsection resolve.

## Acceptance Criteria

- [ ] Root `README.md` contains a distinct `### Knowledge Graph (GraphRAG) System` subsection dedicated to evaluating the KG/GraphRAG system in production.
- [ ] The subsection includes a named-metric table covering Recall@K, Precision@K, contraindicated-leak rate (0% hard gate), safety-gate trip rate, GraphRAG end-to-end latency (< 5 s P95), and concept-resolution rate.
- [ ] Concept-resolution failure modes and an explicit "how you'd know it's working" summary are present (closing the gaps left by the pre-existing generic section).
- [ ] Metric targets are reconciled with the multi-agent `### Key Metrics to Monitor` table and the Assessment 2 ~5 s Performance target; no unresolved contradiction with the existing `### Latency` (< 3 s) figure.
- [ ] Markdown renders cleanly — tables aligned, headings consistent, no unclosed code fences, links resolve.

---

> **UAT**: [`.docs/uat/086-readme-kg-production-eval.uat.md`](../uat/086-readme-kg-production-eval.uat.md)
