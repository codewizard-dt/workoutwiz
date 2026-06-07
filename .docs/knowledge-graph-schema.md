# Knowledge Graph Schema

> Authoritative reference for the Neo4j coaching graph used in ROADMAP-004.
> All ingestion, retrieval, and generation code must conform to this schema.

---

## Node Labels

### `Member`

Represents a registered user of the coaching system.

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` (UUID) | Unique identifier; matches the PostgreSQL `users.id` |
| `email` | `string` | User email address (indexed) |
| `name` | `string` | Display name |
| `goals` | `string[]` | Training goals, e.g. `["strength", "fat_loss"]` |
| `equipment_available` | `string[]` | Equipment the member can access, e.g. `["barbell", "dumbbell"]` |
| `sessions_per_week` | `integer` | Target training frequency |
| `created_at` | `datetime` | When the profile was created |

---

### `Exercise`

Represents a single exercise drawn from `exercises.json`. Loaded once via the seed ingestion pipeline.

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` (UUID) | UUID from `exercises.json`; primary key |
| `name` | `string` | Human-readable exercise name (indexed) |
| `category` | `string` | Broad category, e.g. `"Strength"`, `"Cardio"` |
| `muscle_groups` | `string[]` | Primary and secondary muscles targeted |
| `joints_loaded` | `string[]` | Joints placed under load (used for injury filtering) |
| `movement_patterns` | `string[]` | Fundamental movement patterns, e.g. `["squat", "hinge"]` |
| `equipment_required` | `string[]` | Equipment needed |
| `is_reps` | `boolean` | Tracked by repetition count |
| `is_duration` | `boolean` | Tracked by time duration |
| `supports_weight` | `boolean` | Weight can be added |
| `priority_tier` | `integer` | Programming quality signal; 1 = highest priority |
| `is_bilateral` | `boolean` | Works both sides simultaneously |
| `bilateral_pair_id` | `string\|null` | UUID of paired unilateral variant, if any |
| `description` | `string\|null` | Optional longer description |
| `description_embedding` | `float[]` | 1536-dimensional vector embedding of name + description (populated during Phase 4) |

---

### `Injury`

A member's active or historical injury/condition.

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` (UUID) | Unique identifier |
| `name` | `string` | Condition name, e.g. `"Left knee tendinopathy"` |
| `affected_joints` | `string[]` | Joints affected, e.g. `["knee"]` |
| `severity` | `string` | One of `mild`, `moderate`, `severe` |
| `onset_date` | `date\|null` | When the condition started |
| `status` | `string` | `active` or `resolved` |
| `region` | `string\|null` | Explicit laterality + body part, e.g. `"left knee"` |
| `notes` | `string\|null` | Clinical guidance: restrictions and tolerated movements |
| `snomedct_hint` | `string\|null` | Label used to resolve this injury to a SNOMED CT `Disorder` node |

---

### `BodyStructure`

A SNOMED CT anatomical concept — catalog joint roots and their sub-structures.
Seeded from `backend/data/snomed_subset.json` by `ingest_snomed.py`.

| Property | Type | Description |
|----------|------|-------------|
| `snomed_code` | `string` (unique) | SNOMED CT concept code |
| `snomed_name` | `string` | SNOMED preferred term |
| `catalog_term` | `string\|null` | Matching `joints_loaded` value from the exercise catalog (e.g. `"knee"`); null for sub-structures |
| `skos_relation` | `string\|null` | `exactMatch` or `closeMatch` — how the catalog term relates to the SNOMED concept |

---

### `Disorder`

A SNOMED CT clinical disorder mapped from an injury label.
Seeded from `backend/data/snomed_subset.json` by `ingest_snomed.py`.

| Property | Type | Description |
|----------|------|-------------|
| `snomed_code` | `string` (unique) | SNOMED CT concept code |
| `snomed_name` | `string` | SNOMED preferred term |
| `label` | `string` | Human-readable resolver label (matches `Injury.snomedct_hint`) |
| `expected_joint` | `string` | Catalog joint this disorder is associated with |
| `finding_site_code` | `string\|null` | SNOMED code of the anatomical finding site |
| `finding_site_name` | `string\|null` | Name of the finding site |
| `validated` | `boolean` | Whether the finding site was confirmed via graph traversal or keyword match |

---

### `FeedbackEvent`

A discrete feedback signal from a member about a specific exercise, set, or workout.

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` (UUID) | Unique identifier |
| `rating` | `integer` | 1–5 stars |
| `feedback_text` | `string\|null` | Optional free-text comment |
| `context_type` | `string` | One of `exercise`, `set`, `workout` |
| `created_at` | `datetime` | When the feedback was submitted (indexed) |

---

### `WorkoutSession`

A single training session performed by a member.

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` (UUID) | Unique identifier; matches PostgreSQL `workouts.id` |
| `started_at` | `datetime` | Session start timestamp (indexed) |
| `ended_at` | `datetime\|null` | Session end timestamp |
| `phase` | `string` | One of `warmup`, `main`, `cooldown` |

---

### `Preference`

Deprecated in favour of `FeedbackEvent`. Kept as a reserved label — do not use in new code.

---

## Relationship Types

### `(Member)-[:HAS_INJURY]->(Injury)`

A member has this injury or condition. Active injuries drive contraindication filtering.

- **Cardinality**: many-to-many (a member can have multiple injuries; an injury type can affect multiple members)
- **Properties**: none

---

### `(Member)-[:PERFORMED]->(WorkoutSession)`

A member completed this training session.

- **Cardinality**: one Member → many WorkoutSessions
- **Properties**: none

---

### `(WorkoutSession)-[:INCLUDED]->(Exercise)`

This exercise was performed in the session.

- **Cardinality**: many-to-many (a session includes multiple exercises; an exercise appears in many sessions)
- **Properties**:
  - `sets` (`integer`) — number of sets performed
  - `reps` (`integer[]` or `null`) — reps per set
  - `weight_kg` (`float[]` or `null`) — weight per set
  - `duration_s` (`integer[]` or `null`) — duration per set (for timed exercises)

---

### `(Member)-[:RATED {rating, feedback_text, created_at}]->(Exercise)`

**Denormalized fast-path.** A member rated this exercise directly. This is a single cheap hop for preference retrieval — one edge per (member, exercise) pair, carrying the *latest* rating. The edge is written (and updated) at the same time as the `FeedbackEvent` audit-trail node, so the two are always in sync.

For longitudinal trend analysis (e.g. "how has her opinion of squats changed over time?") query `FeedbackEvent` nodes via the `ABOUT` edge instead — see the FeedbackEvent audit-trail traversal pattern below.

- **Cardinality**: many-to-many (a member rates many exercises; an exercise is rated by many members)
- **Properties**:
  - `rating` (`integer`, 1–5) — most recent rating; prior values are preserved in `FeedbackEvent` history
  - `feedback_text` (`string\|null`)
  - `created_at` (`datetime`)

---

### `(FeedbackEvent)-[:ABOUT]->(Exercise | WorkoutSession | Set)`

**Audit-trail edge.** Links every discrete feedback signal to the entity it describes. This is the append-only event log counterpart to the denormalized `RATED` fast-path — each `FeedbackEvent` node grows exactly one `ABOUT` edge (two edges when `context_type = "set"` and an `exercise_id` is present).

- **Cardinality**: one FeedbackEvent → one target node (many-to-one); each Exercise/WorkoutSession/Set can be the target of many FeedbackEvents
- **Properties**: none
- **Target by context type:**
  - `context_type = "exercise"` → `(FeedbackEvent)-[:ABOUT]->(Exercise)`
  - `context_type = "workout"` → `(FeedbackEvent)-[:ABOUT]->(WorkoutSession)`
  - `context_type = "set"` → `(FeedbackEvent)-[:ABOUT]->(Set)` and optionally `(FeedbackEvent)-[:ABOUT]->(Exercise)` when `exercise_id` is present

---

### `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)`

Legacy derived edge: written during injury ingestion when `Exercise.joints_loaded` overlaps `Injury.affected_joints`. Retained as a fallback for Injury nodes that predate SNOMED ingestion (i.e. nodes with no `MAPS_TO_DISORDER` edge). New code should prefer the SNOMED traversal path.

- **Cardinality**: many-to-many
- **Properties**: none

---

### `(Exercise)-[:MAPS_TO]->(BodyStructure)`

SNOMED-grounded mapping from an exercise's `joints_loaded` catalog term to the corresponding `BodyStructure` node. Written by `ingest_snomed.py`.

- **Cardinality**: many-to-many (one exercise may load several joints; one BodyStructure is shared by many exercises)
- **Properties**: `catalog_term` (string) — the `joints_loaded` value that triggered this edge

---

### `(Disorder)-[:FINDING_SITE]->(BodyStructure)`

SNOMED role edge: this disorder's anatomical finding site. Written by `ingest_snomed.py` from the `Has finding site` relationship in the SNOMED CT concept record.

- **Cardinality**: many-to-one (a disorder has one finding site; many disorders may point to the same structure)
- **Properties**: none

---

### `(BodyStructure)-[:PART_OF]->(BodyStructure)`

Hierarchical containment: a body sub-structure is part of a parent joint. Two varieties:
- **Ontology edges** — direct children of the 9 catalog joint roots from SNOMED `/children` API
- **Bridge edges** — finding-site nodes matched via keyword that sit in a parallel SNOMED hierarchy; bridged directly to the catalog joint root to close the safety traversal loop

- **Cardinality**: many-to-one per edge; a structure may be part of multiple parents in practice
- **Properties**: none

---

### `(Injury)-[:MAPS_TO_DISORDER]->(Disorder)`

Links an `Injury` node to its SNOMED CT `Disorder` by matching `Injury.snomedct_hint` to `Disorder.label`. Written by `ingest_snomed.py`.

- **Cardinality**: many-to-one (multiple lateralized injuries collapse to one non-lateralized Disorder)
- **Properties**: none

---

## Key Traversal Patterns

### SNOMED-Grounded Safety Traversal (primary)

Deterministic injury-aware filtering using the full SNOMED path:

```cypher
// Contraindicated exercise IDs via SNOMED graph
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(inj:Injury {status: 'active'})
      -[:MAPS_TO_DISORDER]->(d:Disorder)
      -[:FINDING_SITE]->(bs:BodyStructure)
      -[:PART_OF*0..]->(joint:BodyStructure)
      <-[:MAPS_TO]-(ex:Exercise)
RETURN DISTINCT ex.id AS exercise_id,
       inj.name        AS injury_name,
       d.snomed_code   AS disorder_code,
       bs.snomed_name  AS finding_site_name,
       joint.catalog_term AS matched_joint
```

```cypher
// Safe exercises: NOT reachable via the SNOMED path
MATCH (m:Member {id: $member_id})
MATCH (e:Exercise)
WHERE NOT EXISTS {
    MATCH (m)-[:HAS_INJURY]->(inj:Injury {status: 'active'})
          -[:MAPS_TO_DISORDER]->(d:Disorder)
          -[:FINDING_SITE]->(bs:BodyStructure)
          -[:PART_OF*0..]->(joint:BodyStructure)
          <-[:MAPS_TO]-(e)
}
RETURN e.id, e.name, e.priority_tier
ORDER BY e.priority_tier ASC
```

### Legacy Safety Filter (fallback)

Used when an `Injury` node has no `MAPS_TO_DISORDER` edge (pre-SNOMED data):

```cypher
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(i:Injury {status: 'active'})
                                 <-[:CONTRAINDICATED_BY]-(e:Exercise)
RETURN DISTINCT e.id AS exercise_id
```

---

### Member Preference and Feedback Lookup

Surface exercises a member has rated highly and exercises they have flagged negatively:

```cypher
// Top-rated exercises for a member
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating >= 4
RETURN e.id, e.name, r.rating, r.feedback_text, r.created_at
ORDER BY r.rating DESC, r.created_at DESC
LIMIT 10
```

```cypher
// Exercises a member has rated poorly (to deprioritize or avoid)
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating <= 2
RETURN e.id, e.name, r.rating, r.feedback_text
ORDER BY r.rating ASC
```

---

### Rating History — FeedbackEvent Audit Trail

Full per-exercise rating history for a member, including timestamp of each signal. Use this for trend analysis rather than the denormalized `RATED` edge (which only holds the latest rating).

```cypher
// Full rating history for a member across all exercises
MATCH (m:Member {id: $member_id})-[:GAVE]->(f:FeedbackEvent)-[:ABOUT]->(e:Exercise)
RETURN e.id, e.name, f.rating, f.feedback_text, f.created_at
ORDER BY e.name ASC, f.created_at DESC
```

```cypher
// Rating trend for a specific exercise — has the member's opinion improved or declined?
MATCH (m:Member {id: $member_id})-[:GAVE]->(f:FeedbackEvent)-[:ABOUT]->(e:Exercise {id: $exercise_id})
RETURN f.rating, f.feedback_text, f.created_at
ORDER BY f.created_at ASC
```

---

### Avoided Exercises

Exercises a member has rated 1–2★ — surfaced by `get_avoided_exercises` and injected into the generation prompt as "EXERCISES TO AVOID" to prevent the LLM from recommending them.

```cypher
// Exercises flagged as avoided (rating ≤ 2 via denormalized RATED edge — fast path)
MATCH (m:Member {id: $member_id})-[r:RATED]->(e:Exercise)
WHERE r.rating <= 2
RETURN e.id, e.name, e.muscle_groups, e.movement_patterns,
       e.equipment_required, e.priority_tier,
       r.rating, r.feedback_text
ORDER BY r.rating ASC, e.name ASC
```

---

### Workout History Traversal

Find the most recent exercises a member performed (for variety / frequency tracking):

```cypher
MATCH (m:Member {id: $member_id})-[:PERFORMED]->(ws:WorkoutSession)-[:INCLUDED]->(e:Exercise)
RETURN e.id, e.name, ws.started_at
ORDER BY ws.started_at DESC
LIMIT 30
```

---

## Vector Index Specification

The `exercise_embeddings` vector index enables semantic similarity search over exercise descriptions:

```cypher
CREATE VECTOR INDEX exercise_embeddings IF NOT EXISTS
FOR (e:Exercise) ON (e.description_embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

- **Dimensions**: 1536 (OpenAI `text-embedding-3-small` / `text-embedding-ada-002` output size)
- **Similarity**: cosine (appropriate for normalized embedding vectors)
- **Input text**: concatenation of `e.name` + `" "` + `e.description` at ingestion time
- **Query pattern**: used in Phase 4 GraphRAG retrieval to find semantically similar exercises from a natural-language prompt

Example vector query:

```cypher
CALL db.index.vector.queryNodes('exercise_embeddings', 10, $query_embedding)
YIELD node AS e, score
WHERE score > 0.75
RETURN e.id, e.name, score
ORDER BY score DESC
```

---

## Design Notes

1. **SNOMED graph traversal is the primary safety mechanism.** The path `Injury → MAPS_TO_DISORDER → Disorder → FINDING_SITE → BodyStructure → PART_OF*0.. → BodyStructure ← MAPS_TO ← Exercise` enforces contraindication deterministically through graph structure, not string comparison or prompt instructions. The `CONTRAINDICATED_BY` edge is retained as a fallback for legacy Injury nodes that predate SNOMED ingestion.

2. **SNOMED codes are frozen at build time.** `backend/scripts/build_snomed_subset.py` fetches from the public NCI EVS REST API once and writes `backend/data/snomed_subset.json`. The running application never calls SNOMED CT. Re-run the script to pick up ontology updates.

3. **PART_OF edges come in two kinds.** Ontology edges connect SNOMED sub-structures to their parent joint roots (from the SNOMED `/children` API). Bridge edges connect finding-site structures that are anatomically at a joint but in a parallel SNOMED hierarchy (matched via keyword during build); these are added during `ingest_snomed.py` to close the traversal loop.

4. **`RATED` duality — denormalized edge vs. `FeedbackEvent` audit trail.** The same exercise rating is stored two ways simultaneously. `(Member)-[:RATED]->(Exercise)` is a single mutable edge per (member, exercise) pair that always reflects the *latest* rating — it exists so the preference traversal in `get_preferred_exercises` and `get_avoided_exercises` is a cheap single hop on the hot path. `FeedbackEvent` nodes (linked via `(FeedbackEvent)-[:ABOUT]->(Exercise)`) are immutable, append-style records — one node per rating event, full history, every timestamp preserved. Use `FeedbackEvent` for trend analysis and longitudinal queries; use `RATED` for current-preference retrieval. Both are written in the same transaction in `write_feedback` and `_upsert_feedback_batch`; `RATED` uses `ON MATCH SET` to overwrite, while `FeedbackEvent` accumulates.

5. **PostgreSQL remains the system of record for auth and workout sets.** Neo4j holds the coaching graph only. The `Member.id` and `WorkoutSession.id` in Neo4j match their PostgreSQL counterparts to enable cross-store joins when needed.
