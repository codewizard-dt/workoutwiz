# Feedback Methodology — FeedbackEvent & the Knowledge Graph

This document records how member feedback enters the knowledge graph, what nodes and edges
it creates, and how it influences recommendations. It is the authoritative reference for the
`FeedbackEvent` node, the denormalized `RATED` edge, and the preference-weighting traversal.

See also: [`SNOMED_METHODOLOGY.md`](./SNOMED_METHODOLOGY.md) (safety layer). Feedback is the
**preference** layer; the two are orthogonal — feedback ranks, safety filters.

---

## What feedback is for

A coach or member rates how an exercise (or set, or whole workout) felt on a 1–5 scale. That
signal does two things in the graph:

1. **Preserves an audit trail** — every rating is a discrete `FeedbackEvent` node with a
   timestamp and optional free text, queryable longitudinally.
2. **Nudges future recommendations** — positively-rated exercises are surfaced as *preferred*
   during retrieval, so the generator favours exercises the member already likes.

Feedback **never overrides safety.** A contraindicated exercise that was rated 5★ is still
filtered out by the SNOMED traversal. Preference is additive ranking; safety is subtractive.

---

## Dual-store architecture

Feedback lives in two places with different jobs:

| Store | Table / Label | Role | Written by |
|-------|--------------|------|-----------|
| PostgreSQL | `exercise_feedback` | System of record (durable, relational, FK-enforced) | Seed pipeline |
| Neo4j | `(:FeedbackEvent)` | Graph signal for traversal + ranking | Seed pipeline, runtime API, PG→Neo4j sync |

**Three write paths:**

- **Seed** (`seed.py::seed_feedback`) — writes *both* PostgreSQL and Neo4j (20 events/member).
- **PG→Neo4j sync** (`ingest_feedback.py::ingest_all_feedback`) — reads every `ExerciseFeedback`
  row and upserts the corresponding graph nodes/edges via `_upsert_feedback_batch`.
- **Runtime API** (`feedback_service.py::write_feedback`, behind `POST /kg/feedback`) — writes
  **both Neo4j and PostgreSQL** (via `pg_session: AsyncSession`). Fully dual-writes on the live
  path, matching the seed path.

---

## The `FeedbackEvent` node

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` (UUID, unique) | Primary key; uniqueness constraint in `init_schema.py` |
| `rating` | `integer` | 1 (poor) – 5 (excellent) |
| `feedback_text` | `string \| null` | Optional free-text comment |
| `context_type` | `string` | `exercise` \| `set` \| `workout` (`FeedbackContextType` enum) |
| `created_at` | `datetime` (ISO string) | When submitted; indexed in `init_schema.py` |

The PostgreSQL source row (`ExerciseFeedback` in `models/feedback.py`) additionally carries
the FK columns `user_id`, `exercise_id`, `workout_id`, `workout_set_id` — in the graph these
become *edges* rather than properties.

---

## Context types → edges

The `context_type` determines which edges a `FeedbackEvent` grows. This is the crux of how
feedback "affects the graph." Branch logic lives in `feedback_service.py::write_feedback` and
`ingest_feedback.py::_upsert_feedback_batch` (they mirror each other).

### `exercise` (default)

```
(Member)-[:RATED {rating, feedback_text, created_at}]->(Exercise)   ← denormalized fast-path
(FeedbackEvent)-[:ABOUT]->(Exercise)                                 ← audit trail
```

### `workout`

```
(FeedbackEvent)-[:ABOUT]->(WorkoutSession)
```

### `set`

```
(FeedbackEvent)-[:ABOUT]->(Set)
(FeedbackEvent)-[:ABOUT]->(Exercise)    ← when exercise_id present
(Member)-[:RATED ...]->(Exercise)        ← when exercise_id present
```

`(:Set)` and `(:WorkoutSession)` nodes are MERGE-created on demand by the SET / WORKOUT edges,
so feedback can reference them even if workout-history ingestion hasn't created them yet.

---

## Why `RATED` is denormalized

`FeedbackEvent` and `(Member)-[:RATED]->(Exercise)` encode the *same* exercise rating two ways
— this is deliberate:

- **`FeedbackEvent`** is the immutable, append-style event log: one node per rating, full
  history, every timestamp preserved. Use it for longitudinal analysis ("how has her opinion
  of squats trended?").
- **`RATED`** is a denormalized, mutable aggregate edge: one edge per (member, exercise) pair,
  carrying the latest rating. It exists purely so the preference traversal is a single cheap
  hop instead of walking through intermediate `FeedbackEvent` nodes on the hot path.

Both are written in the same transaction. `RATED` uses `ON CREATE SET … ON MATCH SET …` so a
re-rating overwrites the edge; the `FeedbackEvent` log keeps the prior events.

---

## How feedback affects recommendations (the read path)

The preference signal enters retrieval through one traversal:

```cypher
-- traversal.py :: _PREFERRED_EXERCISES_QUERY
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating >= $min_rating          -- default 4
RETURN e.id, e.name, e.muscle_groups, e.movement_patterns,
       e.equipment_required, e.priority_tier,
       avg(r.rating)  AS avg_rating,
       count(r)       AS feedback_count
ORDER BY avg_rating DESC, e.name ASC
```

Flow into generation:

```
POST /kg/recommend
  → retrieval_graph :: run_preference_traversal
      → get_preferred_exercises(member_id)   -- the query above, min_rating=4
      → preferred_exercises[]  into RetrievalState
  → assemble_context
      → preferred section, token-budgeted (ADR-001 D3), deduped against safe set
  → generation_graph
      → LLM picks from context; exercises traced to the preferred list get
        source_type = "PREFERRED" in the provenance trace
```

So a 4–5★ rating makes an exercise more likely to appear *and* labels its provenance as
preference-driven. A 1–3★ rating simply omits it from the preferred set (it is not penalized
or excluded — it can still surface via the safe set or vector search).

**Ordering of layers in retrieval:** safety filter (SNOMED) produces the *allowed* set first;
preference traversal ranks *within* what's allowed. Feedback can never reintroduce a
contraindicated exercise.

---

## Negative signal — avoided exercises

Exercises rated 1–2★ are collected by `get_avoided_exercises` in `traversal.py` and passed
through the retrieval pipeline as a hard exclusion signal:

```cypher
-- traversal.py :: _AVOIDED_EXERCISES_QUERY
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating <= 2
RETURN e.id, e.name, e.muscle_groups, e.movement_patterns,
       e.equipment_required, e.priority_tier,
       r.rating, r.feedback_text
ORDER BY r.rating ASC, e.name ASC
```

These IDs are stored in `ContextSlice.avoided_exercises`. The assembler injects them into the
generation prompt under an **"EXERCISES TO AVOID"** heading so the LLM explicitly knows not to
recommend them — even if they otherwise appear in the safe pool.

This is stronger than merely omitting them from the *preferred* set: a rated-2★ exercise that
the vector search or equipment filter would otherwise surface is now explicitly blocked.

---

## Trend analysis — FeedbackEvent audit trail

The `RATED` edge is mutable and holds only the latest rating. To query how a member's opinion
has changed over time, use `get_rating_history` in `traversal.py`, which walks `FeedbackEvent`
nodes directly:

```cypher
-- traversal.py :: _RATING_HISTORY_QUERY  (illustrative)
MATCH (m:Member {id: $member_id})-[:GAVE]->(f:FeedbackEvent)-[:ABOUT]->(e:Exercise)
RETURN e.id, e.name, f.rating, f.feedback_text, f.created_at
ORDER BY f.created_at DESC
```

Use cases:
- Detect recency: a member once rated an exercise 2★ but has rated it 5★ in the last three
  sessions — the `RATED` edge now shows 5★ (positive preference); the history shows the
  earlier discomfort.
- Identify instability: wildly fluctuating ratings may indicate form uncertainty or pain
  that isn't captured as a formal injury.

---

## Cypher reference (verbatim)

All constants live in `ingest_feedback.py` and are imported (not re-written) by
`feedback_service.py`.

```cypher
-- _MERGE_FEEDBACK_EVENT
MERGE (f:FeedbackEvent {id: $id})
ON CREATE SET
  f.rating = $rating, f.feedback_text = $feedback_text,
  f.context_type = $context_type, f.created_at = $created_at
ON MATCH SET
  f.rating = $rating, f.feedback_text = $feedback_text
```

```cypher
-- _EDGE_EXERCISE_ABOUT
MATCH (f:FeedbackEvent {id: $feedback_id})
MATCH (e:Exercise {id: $exercise_id})
MERGE (f)-[:ABOUT]->(e)
```

```cypher
-- _EDGE_MEMBER_RATED  (denormalized fast-path)
MATCH (m:Member {id: $member_id})
MATCH (e:Exercise {id: $exercise_id})
MERGE (m)-[r:RATED]->(e)
ON CREATE SET r.rating = $rating, r.feedback_text = $feedback_text, r.created_at = $created_at
ON MATCH  SET r.rating = $rating, r.feedback_text = $feedback_text, r.created_at = $created_at
```

```cypher
-- _EDGE_WORKOUT_ABOUT
MATCH (f:FeedbackEvent {id: $feedback_id})
MATCH (ws:WorkoutSession {id: $workout_id})
MERGE (f)-[:ABOUT]->(ws)
```

```cypher
-- _EDGE_SET_ABOUT  (MERGE-creates the Set node if absent)
MERGE (s:Set {id: $workout_set_id})
WITH s
MATCH (f:FeedbackEvent {id: $feedback_id})
MERGE (f)-[:ABOUT]->(s)
```

---

## Idempotency & schema

- Every write `MERGE`s on `id` — re-running the seed or sync is safe (no duplicate nodes/edges).
- `init_schema.py` enforces `CONSTRAINT feedback_event_id` (unique `FeedbackEvent.id`) and an
  index on `FeedbackEvent.created_at`.
- `RATED` overwrites on match; `FeedbackEvent` history accumulates.

---

## Synthetic seed profile

`seed.py::seed_feedback` generates **20 FeedbackEvents per member** (all `context_type=exercise`):

- **Rating distribution** — positively skewed: weights `[3, 7, 20, 35, 35]` for ratings 1–5
  (i.e. ~70% are 4–5★), realistic for a coaching product where members keep exercises they like.
- **Free text** — present on ~60% of events (Faker sentence, 5–15 words).
- **Timestamps** — spread across the last 90 days.
- **Exercise pool** — drawn from each persona's *safe* pool (`_safe_pool`) where available, so
  seeded ratings never contradict the member's injuries.

This gives every member a non-empty `RATED` neighbourhood so the preference traversal returns
signal during demos.

---

## Known characteristics / resolved items

1. ✅ **Fixed — runtime API now dual-writes.** `write_feedback` (behind `POST /kg/feedback`) now
   also inserts into the PostgreSQL `exercise_feedback` table via the SQLAlchemy ORM. A
   `pg_session: AsyncSession` parameter was added so the endpoint writes both stores in the same
   request, matching the parity of the seed path.
2. ✅ **Fixed — `get_rating_history` added for trend analysis.** `get_rating_history` was added
   to `traversal.py`; it queries `FeedbackEvent` nodes directly (via the `ABOUT` edge) to return
   the full chronological rating history for a (member, exercise) pair. The denormalized `RATED`
   edge still reflects only the latest rating on purpose — use `get_rating_history` for
   longitudinal queries.
3. ✅ **Fixed — avoided exercises surfaced and injected into generation.** `get_avoided_exercises`
   was added to `traversal.py`; it queries `(Member)-[:RATED]->(Exercise)` with `rating ≤ 2`.
   The result is carried in `ContextSlice.avoided_exercises` and injected into the generation
   prompt under an "EXERCISES TO AVOID" heading so the LLM never recommends exercises a member
   has flagged negatively.
4. ✅ **Fixed — workout/set feedback consumed by retrieval.** `get_workout_feedback` was added to
   `traversal.py`; `ContextSlice` now carries a `recent_workout_feedback` field. The
   `run_preference_traversal` node in `retrieval_graph.py` fetches avoided exercises alongside
   preferred exercises so both negative and positive signals are available to the assembler.

---

## Files

| File | Role |
|------|------|
| `backend/app/models/feedback.py` | `ExerciseFeedback` table + `FeedbackContextType` enum |
| `backend/app/schemas/kg.py` | `FeedbackPayload` (API contract) |
| `backend/app/routers/kg.py` | `POST /kg/feedback` endpoint |
| `backend/app/kg/feedback_service.py` | `write_feedback` — runtime dual-write (Neo4j + PostgreSQL via `pg_session`), branches on context |
| `backend/app/knowledge_graph/ingest_feedback.py` | Cypher constants + PG→Neo4j sync (`ingest_all_feedback`) |
| `backend/app/knowledge_graph/seed.py` | `seed_feedback` — synthetic dual-write |
| `backend/app/knowledge_graph/traversal.py` | `get_preferred_exercises`, `get_avoided_exercises`, `get_rating_history`, `get_workout_feedback` + their Cypher constants |
| `backend/app/kg/retrieval_graph.py` | `run_preference_traversal` node — fetches preferred and avoided exercises into `RetrievalState` |
| `backend/app/knowledge_graph/init_schema.py` | `FeedbackEvent` uniqueness constraint + `created_at` index |
| `.docs/knowledge-graph-schema.md` | Node/edge reference (`FeedbackEvent`, `RATED`) |
