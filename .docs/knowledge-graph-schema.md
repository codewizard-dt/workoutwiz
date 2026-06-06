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
| `name` | `string` | Condition name, e.g. `"Knee Tendinopathy"` |
| `affected_joints` | `string[]` | Joints affected, e.g. `["knee"]` |
| `severity` | `string` | One of `mild`, `moderate`, `severe` |
| `onset_date` | `date\|null` | When the condition started |
| `status` | `string` | `active` or `resolved` |

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

A member rated this exercise directly. Derived from `FeedbackEvent` nodes where `context_type = "exercise"`. Also stored as a direct relationship for fast traversal.

- **Cardinality**: many-to-many (a member rates many exercises; an exercise is rated by many members)
- **Properties**:
  - `rating` (`integer`, 1–5)
  - `feedback_text` (`string\|null`)
  - `created_at` (`datetime`)

---

### `(Injury)-[:AFFECTS_JOINT]->(string)`

Conceptual relationship — encoded as the `affected_joints` property array on `Injury` nodes, not as separate string nodes. Resolved at query time via `ANY(j IN i.affected_joints WHERE j IN e.joints_loaded)`.

---

### `(Exercise)-[:LOADS_JOINT]->(string)`

Conceptual relationship — encoded as the `joints_loaded` property array on `Exercise` nodes. Resolved at query time.

---

### `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)`

Derived edge: this exercise is contraindicated by this injury because the exercise loads at least one joint affected by the injury. Written during injury ingestion and updated when new exercises are added.

- **Cardinality**: many-to-many
- **Properties**: none (the overlap rationale is recoverable via `joints_loaded` and `affected_joints`)

---

## Key Traversal Patterns

### Injury-Aware Exercise Filtering

Return all exercises that are safe for a given member (no contraindicated joints):

```cypher
// Find exercises a member CAN perform given their active injuries
MATCH (m:Member {id: $member_id})
OPTIONAL MATCH (m)-[:HAS_INJURY]->(i:Injury {status: 'active'})
WITH m, collect(i.affected_joints) AS injured_joint_lists
WITH m, [j IN apoc.coll.flatten(injured_joint_lists) | j] AS all_injured_joints

MATCH (e:Exercise)
WHERE NONE(j IN e.joints_loaded WHERE j IN all_injured_joints)
RETURN e.id, e.name, e.muscle_groups, e.priority_tier
ORDER BY e.priority_tier ASC
LIMIT 20
```

Alternative using the derived `CONTRAINDICATED_BY` edge (faster when edge is pre-computed):

```cypher
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(i:Injury {status: 'active'})
WITH m, collect(i) AS injuries

MATCH (e:Exercise)
WHERE NOT EXISTS {
    MATCH (e)-[:CONTRAINDICATED_BY]->(bad_i:Injury)
    WHERE bad_i IN injuries
}
RETURN e.id, e.name, e.muscle_groups, e.priority_tier
ORDER BY e.priority_tier ASC
LIMIT 20
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

1. **Joint overlap is the contraindication signal.** The `CONTRAINDICATED_BY` edge is pre-computed at ingestion time by comparing `Injury.affected_joints` with `Exercise.joints_loaded`. This avoids expensive set-intersection at query time when generating recommendations.

2. **`RATED` is both a node and a relationship.** `FeedbackEvent` nodes preserve the full audit trail; the `[:RATED]` relationship on the `(Member)->(Exercise)` edge is a denormalized copy for fast traversal. Both are written during feedback ingestion.

3. **`joints_loaded` on Exercise is the bridge field.** It must be populated during exercise ingestion from `exercises.json`. The `exercises.json` dataset does not include `joints_loaded` directly — it must be derived from `muscle_groups` + `movement_patterns` during Phase 3 ingestion (see ROADMAP-004 Phase 3).

4. **PostgreSQL remains the system of record for auth and workout sets.** Neo4j holds the coaching graph only. The `Member.id` and `WorkoutSession.id` in Neo4j match their PostgreSQL counterparts to enable cross-store joins when needed.
