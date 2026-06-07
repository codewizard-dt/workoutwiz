# 091 — Promote Muscle / MovementPattern / Equipment to First-Class KG Nodes with Typed Edges

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [090-concept-resolver-3pass](090-concept-resolver-3pass.md), [092-fix-retrieval-double-traversal](092-fix-retrieval-double-traversal.md), [093-neo4j-driver-singleton](093-neo4j-driver-singleton.md)

## Objective

Promote `muscle_groups`, `movement_patterns`, and `equipment_required` from string-array properties on `Exercise` nodes into first-class `Muscle`, `MovementPattern`, and `Equipment` nodes connected by typed edges, so the KG can traverse "which exercises target the quadriceps" (assessment KG 1 requires the muscles / movement patterns / equipment node types with `targets` / `requires` edges).

## Approach

Add three new node labels keyed by `name` (`Muscle`, `MovementPattern`, `Equipment`) plus uniqueness constraints, and during exercise ingest `MERGE` those nodes and the edges `(:Exercise)-[:TARGETS]->(:Muscle)`, `(:Exercise)-[:REQUIRES]->(:Equipment)`, `(:Exercise)-[:HAS_PATTERN]->(:MovementPattern)` — modelled on the existing `_merge_body_structure` / `_merge_part_of` / `_wire_exercise_maps_to` SNOMED pattern in `ingest_snomed.py`. Keep the existing array properties (`muscle_groups`, `movement_patterns`, `equipment_required`) in place for backward-compat (they are still read by `_SAFE_EXERCISES_QUERY` / `get_safe_exercises`); this is a dual-store, non-breaking change, not a migration. Joints are unchanged — they already exist as SNOMED `BodyStructure` nodes reached via `(:Exercise)-[:MAPS_TO]->(:BodyStructure)` from `joints_loaded` (the assessment `stresses` edge), so no joint work is in scope here.

## Prerequisites

- [x] Read `ingest_exercises` in `backend/app/knowledge_graph/ingest_exercises.py` (lines ~26-87) — the single `MERGE (e:Exercise {id})` + `SET e += {...}` that currently stores `muscle_groups` / `movement_patterns` / `equipment_required` as array properties, plus the trailing `CONTRAINDICATED_BY` edge pass.
- [x] Read the SNOMED ingest model to mirror: `_merge_body_structure`, `_merge_part_of`, and `_wire_exercise_maps_to` in `backend/app/knowledge_graph/ingest_snomed.py` (MERGE-by-key node helpers + a single UNWIND edge-wiring pass that returns a count).
- [x] Read `CONSTRAINTS` / `INDEXES` / `init_neo4j_schema` in `backend/app/knowledge_graph/init_schema.py` (lines 33-126) — the `CREATE CONSTRAINT <name> IF NOT EXISTS FOR (x:Label) REQUIRE x.<prop> IS UNIQUE` pattern (e.g. `body_structure_snomed_code`) that the loop in `init_neo4j_schema` executes.
- [x] Confirm the exact value vocabularies in `.docs/guides/2-knowledge-graph/exercises.json`: `muscle_groups` are lowercase tokens (e.g. `"chest"`, `"triceps"`), `movement_patterns` are lowercase phrases (e.g. `"upper push - horizontal"`, `"core - anti-extension"`), `equipment_required` are Title-Case strings (e.g. `"Barbell"`, `"Dumbbell"`, `"Yoga Mat"`). Use each raw string verbatim as the node `name` (no normalization) so edges line up with the retained array properties — spec: 19 muscle groups, 36 movement patterns, 32 equipment types.
- [x] Note the existing test patterns to reuse: `test_ingest_exercises_calls_merge_and_edge_pass` (MagicMock driver/session asserting `session.run` call counts) in `backend/tests/knowledge_graph/test_ingest_exercises.py`, and `_make_driver` (AsyncMock driver returning canned `result.data()`) in `backend/tests/knowledge_graph/test_traversal.py`.
- [x] Pin the chosen edge-type strings used consistently across all steps: **`TARGETS`** (Exercise→Muscle), **`REQUIRES`** (Exercise→Equipment), **`HAS_PATTERN`** (Exercise→MovementPattern).

---

## Steps

### 1. Schema constraints/indexes  <!-- agent: general-purpose -->

- [x] In `backend/app/knowledge_graph/init_schema.py`, append three uniqueness constraints to the `CONSTRAINTS` list following the existing `IF NOT EXISTS` pattern: `muscle_name` → `FOR (m:Muscle) REQUIRE m.name IS UNIQUE`, `movement_pattern_name` → `FOR (p:MovementPattern) REQUIRE p.name IS UNIQUE`, `equipment_name` → `FOR (eq:Equipment) REQUIRE eq.name IS UNIQUE`.
- [x] Do not change `init_neo4j_schema` — it already iterates `CONSTRAINTS`; verify the new entries are valid Cypher so the existing loop creates them (each block is parseable by `_extract_name(cypher, "CONSTRAINT")`). <!-- Completed: 2026-06-07 -->

### 2. Ingest typed nodes & edges  <!-- agent: general-purpose -->

- [x] In `backend/app/knowledge_graph/ingest_exercises.py`, inside the existing per-exercise loop in `ingest_exercises`, after the `MERGE (e:Exercise {id})` statement, run an UNWIND-based pass that `MERGE`s a `Muscle` node per `muscle_groups` value and the edge `(:Exercise)-[:TARGETS]->(:Muscle)` — e.g. `MATCH (e:Exercise {id: $id}) UNWIND $muscle_groups AS mg MERGE (m:Muscle {name: mg}) MERGE (e)-[:TARGETS]->(m)`.
- [x] Add the analogous passes for `(:Exercise)-[:REQUIRES]->(:Equipment {name})` from `equipment_required` and `(:Exercise)-[:HAS_PATTERN]->(:MovementPattern {name})` from `movement_patterns`, reusing the `$id` and existing parameter values already passed to the MERGE (keep passing `muscle_groups` / `movement_patterns` / `equipment_required` as `... or []`).
- [x] Keep the existing `SET e += {muscle_groups, movement_patterns, equipment_required, joints_loaded, ...}` array-property block unchanged (dual-store / backward-compat) and leave the trailing `CONTRAINDICATED_BY` edge pass and `joints_loaded`→`MAPS_TO` SNOMED wiring (handled separately in `ingest_snomed.py`) untouched — no `stresses`/joint changes here.
- [x] Ensure the new MERGEs are idempotent (safe to re-run via `seed.py` → `seed_exercises_neo4j` → `ingest_exercises`) and that empty arrays produce no edges. <!-- Completed: 2026-06-07 -->

### 3. Traversal helpers  <!-- agent: general-purpose -->

- [x] In `backend/app/knowledge_graph/traversal.py`, add an async helper `get_exercises_targeting_muscle(muscle_name, driver, database="neo4j")` that runs `MATCH (e:Exercise)-[:TARGETS]->(:Muscle {name: $muscle_name}) RETURN e.id AS id, e.name AS name, e.priority_tier AS priority_tier ORDER BY e.priority_tier ASC, e.name ASC` and returns `await result.data()`, mirroring the `async with driver.session(database=database)` shape used by `get_safe_exercises`.
- [x] Add an analogous `get_exercises_by_equipment(equipment_name, driver, database="neo4j")` using `(:Exercise)-[:REQUIRES]->(:Equipment {name: $equipment_name})` (and, if useful, `get_exercises_by_pattern` using `[:HAS_PATTERN]->(:MovementPattern {name})`), each defined with a module-level query constant like the existing `_SAFE_EXERCISES_QUERY` and a matching `logger.debug` line. <!-- Completed: 2026-06-07 -->

### 4. Tests  <!-- agent: general-purpose -->

- [x] In `backend/tests/knowledge_graph/test_ingest_exercises.py`, add a test using the existing MagicMock driver/session pattern asserting that `ingest_exercises(mock_driver, SAMPLE)` issues additional `session.run` calls beyond the Exercise MERGE + edge pass (i.e. `call_count` rises to cover the new TARGETS/REQUIRES/HAS_PATTERN passes), and assert the Cypher of the new calls contains `MERGE (m:Muscle`, `:TARGETS`, `:REQUIRES`, and `:HAS_PATTERN` (inspect `mock_session.run.call_args_list`).
- [x] In `backend/tests/knowledge_graph/test_traversal.py`, add tests for `get_exercises_targeting_muscle` and `get_exercises_by_equipment` using the `_make_driver(run_return=[...])` helper: assert they return the canned list of dicts and that the `muscle_name` / `equipment_name` argument is forwarded as a query parameter (assert on `mock_session.run.call_args`).
- [x] Cover the empty case: a muscle/equipment with no matching exercises returns `[]` (driver `run_return=[]`). <!-- Completed: 2026-06-07 -->

### 5. Verification  <!-- agent: general-purpose -->

- [x] Run `backend/.venv/bin/python -m pytest backend/tests/knowledge_graph/test_ingest_exercises.py backend/tests/knowledge_graph/test_traversal.py -q` and confirm all pass (new and existing). <!-- 24 passed in 0.06s — Completed: 2026-06-07 -->
- [ ] [DEFERRED-TO-UAT] Re-run the seed/ingest against a Neo4j instance (`set -a && source .env && set +a && backend/.venv/bin/python -m app.knowledge_graph.seed`, or at minimum `python -m app.knowledge_graph.init_schema` + `ingest_exercises`) and confirm with a Cypher check that the new nodes/edges exist, e.g. `MATCH (e:Exercise)-[:TARGETS]->(m:Muscle {name: 'quadriceps'}) RETURN e.name` returns rows and `MATCH (n:Muscle) RETURN count(n)` / `MATCH (n:Equipment) RETURN count(n)` / `MATCH (n:MovementPattern) RETURN count(n)` are non-zero.

## Acceptance Criteria

- [x] `Muscle`, `MovementPattern`, and `Equipment` nodes exist in Neo4j after seeding, each keyed by a unique `name` (uniqueness constraints created via `init_neo4j_schema`).
- [x] `(:Exercise)-[:TARGETS]->(:Muscle)`, `(:Exercise)-[:REQUIRES]->(:Equipment)`, and `(:Exercise)-[:HAS_PATTERN]->(:MovementPattern)` edges are created during `ingest_exercises` and are queryable (e.g. exercises targeting a given muscle can be retrieved by traversal).
- [x] The existing `muscle_groups` / `movement_patterns` / `equipment_required` array properties and the `joints_loaded`→`MAPS_TO`/`stresses` SNOMED path are unchanged (dual-store, no regression in `get_safe_exercises`).
- [x] `get_exercises_targeting_muscle` and `get_exercises_by_equipment` return the expected exercises for a known muscle/equipment and `[]` when there is no match.
- [x] Ingest is idempotent (re-running seed creates no duplicate nodes/edges) and new + existing tests in `test_ingest_exercises.py` and `test_traversal.py` pass.

---
**UAT**: [`.docs/uat/091-kg-muscle-equipment-pattern-nodes.uat.md`](../uat/091-kg-muscle-equipment-pattern-nodes.uat.md)
