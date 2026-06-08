# UAT: Promote Muscle / MovementPattern / Equipment to First-Class KG Nodes

> **Source task**: [`.docs/tasks/091-kg-muscle-equipment-pattern-nodes.md`](../tasks/091-kg-muscle-equipment-pattern-nodes.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] Neo4j instance is running and accessible at `bolt://localhost:7687` (or the value of `NEO4J_URI` in `.env`)
- [ ] `.env` file is present in the project root with valid `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `DATABASE_URL`
- [ ] Python virtual environment is initialized at `backend/.venv/`
- [ ] The seed has been run at least once so Exercise nodes exist in Neo4j (or the ingest-only command is run in UAT-SEED-001 below)

---

## Seed / Schema Tests

### UAT-SEED-001: Schema constraints for Muscle, MovementPattern, Equipment exist after init

- **Description**: Verify `init_neo4j_schema` creates the three new uniqueness constraints (`muscle_name`, `movement_pattern_name`, `equipment_name`) using `IF NOT EXISTS`, so the call is idempotent.
- **Steps**:
  1. Run the command below from the project root. It loads `.env`, runs `init_neo4j_schema`, then queries Neo4j for the new constraint names.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j
import os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
from app.knowledge_graph.init_schema import init_neo4j_schema
init_neo4j_schema(driver)
with driver.session() as s:
    result = s.run('SHOW CONSTRAINTS YIELD name WHERE name IN [\"muscle_name\", \"movement_pattern_name\", \"equipment_name\"] RETURN name ORDER BY name')
    names = [r['name'] for r in result]
print('constraints found:', names)
driver.close()
"
  ```
- **Expected Result**: Prints `constraints found: ['equipment_name', 'movement_pattern_name', 'muscle_name']` (all three names present; order may vary but all three must appear).
- [x] Pass <!-- 2026-06-08 -->

### UAT-SEED-002: ingest_exercises creates Muscle, Equipment, MovementPattern nodes

- **Description**: After running `ingest_exercises` (via seed or directly), Muscle, Equipment, and MovementPattern nodes must exist in Neo4j with non-zero counts matching the dataset vocabulary (19 muscles, 32 equipment types, 36 movement patterns).
- **Steps**:
  1. Run the command below, which re-seeds exercises (idempotent) and then checks node counts.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
from app.knowledge_graph.ingest_exercises import ingest_exercises, load_exercises
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
exercises = load_exercises()
ingest_exercises(driver, exercises)
with driver.session() as s:
    muscle_count = s.run('MATCH (n:Muscle) RETURN count(n) AS c').single()['c']
    equip_count = s.run('MATCH (n:Equipment) RETURN count(n) AS c').single()['c']
    pattern_count = s.run('MATCH (n:MovementPattern) RETURN count(n) AS c').single()['c']
print(f'Muscle={muscle_count}, Equipment={equip_count}, MovementPattern={pattern_count}')
driver.close()
"
  ```
- **Expected Result**: Prints `Muscle=19, Equipment=32, MovementPattern=36`. All three counts must match the dataset vocabulary exactly.
- [x] Pass <!-- 2026-06-08 -->

### UAT-SEED-003: TARGETS edges connect Exercise nodes to Muscle nodes

- **Description**: After ingest, `(:Exercise)-[:TARGETS]->(:Muscle)` edges must exist and be traversable. Exercises targeting `quads` are known from the dataset (Med Ball Scoop Toss, Kettlebell Goblet Cyclist Squat, RNT Split Squat at minimum).
- **Steps**:
  1. Run the command below to traverse the TARGETS edge for the `quads` muscle.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
with driver.session() as s:
    result = s.run('MATCH (e:Exercise)-[:TARGETS]->(m:Muscle {name: \$name}) RETURN e.name AS name ORDER BY e.name', name='quads')
    names = [r['name'] for r in result]
print('exercises targeting quads:', names)
driver.close()
"
  ```
- **Expected Result**: Output includes `'Kettlebell Goblet Cyclist Squat'`, `'Med Ball Scoop Toss'`, and `'RNT Split Squat'` in the returned list. The list must be non-empty and contain only exercises whose `muscle_groups` array contains `'quads'`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-SEED-004: REQUIRES edges connect Exercise nodes to Equipment nodes

- **Description**: After ingest, `(:Exercise)-[:REQUIRES]->(:Equipment)` edges must be traversable. `Barbell Decline Bench Press` requires `Barbell` per the dataset.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
with driver.session() as s:
    result = s.run('MATCH (e:Exercise)-[:REQUIRES]->(eq:Equipment {name: \$name}) RETURN e.name AS name ORDER BY e.name', name='Barbell')
    names = [r['name'] for r in result]
    total_requires = s.run('MATCH ()-[:REQUIRES]->() RETURN count(*) AS c').single()['c']
print('exercises requiring Barbell:', names)
print('total REQUIRES edges:', total_requires)
driver.close()
"
  ```
- **Expected Result**: The list includes `'Barbell Decline Bench Press'`. `total_requires` must be greater than 0. The list is non-empty.
- [x] Pass <!-- 2026-06-08 -->

### UAT-SEED-005: HAS_PATTERN edges connect Exercise nodes to MovementPattern nodes

- **Description**: After ingest, `(:Exercise)-[:HAS_PATTERN]->(:MovementPattern)` edges must be traversable. `Barbell Decline Bench Press` has pattern `upper push - horizontal` per the dataset.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
with driver.session() as s:
    result = s.run('MATCH (e:Exercise)-[:HAS_PATTERN]->(p:MovementPattern {name: \$name}) RETURN e.name AS name ORDER BY e.name', name='upper push - horizontal')
    names = [r['name'] for r in result]
    total_patterns = s.run('MATCH ()-[:HAS_PATTERN]->() RETURN count(*) AS c').single()['c']
print('exercises with upper push - horizontal:', names)
print('total HAS_PATTERN edges:', total_patterns)
driver.close()
"
  ```
- **Expected Result**: The list includes `'Barbell Decline Bench Press'`. `total_patterns` must be greater than 0.
- [x] Pass <!-- 2026-06-08 -->

### UAT-SEED-006: Ingest is idempotent — re-running does not duplicate nodes or edges

- **Description**: Running `ingest_exercises` twice must produce the same node and edge counts as running it once. The `MERGE` semantics guarantee no duplicates.
- **Steps**:
  1. Run the command below, which calls `ingest_exercises` twice then checks counts.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
from app.knowledge_graph.ingest_exercises import ingest_exercises, load_exercises
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
exercises = load_exercises()
ingest_exercises(driver, exercises)
ingest_exercises(driver, exercises)
with driver.session() as s:
    mc = s.run('MATCH (n:Muscle) RETURN count(n) AS c').single()['c']
    ec = s.run('MATCH (n:Equipment) RETURN count(n) AS c').single()['c']
    pc = s.run('MATCH (n:MovementPattern) RETURN count(n) AS c').single()['c']
    te = s.run('MATCH ()-[:TARGETS]->() RETURN count(*) AS c').single()['c']
    re_ = s.run('MATCH ()-[:REQUIRES]->() RETURN count(*) AS c').single()['c']
    hp = s.run('MATCH ()-[:HAS_PATTERN]->() RETURN count(*) AS c').single()['c']
print(f'Muscle={mc}, Equipment={ec}, MovementPattern={pc}')
print(f'TARGETS={te}, REQUIRES={re_}, HAS_PATTERN={hp}')
driver.close()
"
  ```
- **Expected Result**: Counts are identical to UAT-SEED-002: `Muscle=19, Equipment=32, MovementPattern=36`. Edge counts remain stable across the two runs (not doubled). All six values must be non-zero.
- [x] Pass <!-- 2026-06-08 -->

### UAT-SEED-007: Existing array properties are preserved (dual-store, no regression)

- **Description**: The `muscle_groups`, `movement_patterns`, and `equipment_required` array properties must still exist on Exercise nodes after the new ingest (dual-store, backward-compatible). Verifies no regression in `get_safe_exercises`.
- **Steps**:
  1. Run the command below, which checks one known exercise retains its array properties.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
with driver.session() as s:
    result = s.run('MATCH (e:Exercise {name: \$name}) RETURN e.muscle_groups AS mg, e.equipment_required AS eq, e.movement_patterns AS mp', name='Barbell Decline Bench Press')
    row = result.single()
print('muscle_groups:', row['mg'])
print('equipment_required:', row['eq'])
print('movement_patterns:', row['mp'])
driver.close()
"
  ```
- **Expected Result**: `muscle_groups` includes `'chest'` and `'triceps'`; `equipment_required` includes `'Barbell'`; `movement_patterns` includes `'upper push - horizontal'`. None of the three properties are `None` or empty.
- [x] Pass <!-- 2026-06-08 -->

---

## Traversal Helper Tests

### UAT-TRAV-001: get_exercises_targeting_muscle returns exercises for a known muscle

- **Description**: The `get_exercises_targeting_muscle('quads', driver)` helper must return a non-empty list of dicts, each with at minimum `id`, `name`, and `priority_tier` keys, ordered by `priority_tier ASC, name ASC`. The list must include the known quad exercises.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import asyncio, neo4j, os
from neo4j import AsyncGraphDatabase
from app.knowledge_graph.traversal import get_exercises_targeting_muscle
async def run():
    driver = AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    result = await get_exercises_targeting_muscle('quads', driver)
    await driver.close()
    return result
rows = asyncio.run(run())
print('count:', len(rows))
print('keys in first row:', list(rows[0].keys()) if rows else 'EMPTY')
print('names:', [r['name'] for r in rows])
"
  ```
- **Expected Result**: `count` is greater than 0. `keys in first row` includes `id`, `name`, `priority_tier`. `names` includes `'Med Ball Scoop Toss'`, `'Kettlebell Goblet Cyclist Squat'`, and `'RNT Split Squat'`. Results are ordered by `priority_tier` ascending then name ascending.
- [x] Pass <!-- 2026-06-08 -->

### UAT-TRAV-002: get_exercises_targeting_muscle returns empty list for unknown muscle

- **Description**: `get_exercises_targeting_muscle` for a muscle name not in the dataset must return `[]` (not raise an exception).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import asyncio, os
from neo4j import AsyncGraphDatabase
from app.knowledge_graph.traversal import get_exercises_targeting_muscle
async def run():
    driver = AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    result = await get_exercises_targeting_muscle('nonexistent_muscle_xyz', driver)
    await driver.close()
    return result
rows = asyncio.run(run())
print('result:', rows)
"
  ```
- **Expected Result**: Prints `result: []` with no exception raised.
- [x] Pass <!-- 2026-06-08 -->

### UAT-TRAV-003: get_exercises_by_equipment returns exercises for a known equipment

- **Description**: `get_exercises_by_equipment('Dumbbell', driver)` must return a non-empty list of dicts. The list must include known dumbbell exercises from the dataset (`Alternating Dumbbell Decline Bench Press` et al.).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import asyncio, os
from neo4j import AsyncGraphDatabase
from app.knowledge_graph.traversal import get_exercises_by_equipment
async def run():
    driver = AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    result = await get_exercises_by_equipment('Dumbbell', driver)
    await driver.close()
    return result
rows = asyncio.run(run())
print('count:', len(rows))
print('names (first 5):', [r['name'] for r in rows[:5]])
"
  ```
- **Expected Result**: `count` is greater than 0. `names` includes `'Alternating Dumbbell Decline Bench Press'`. Each dict has at minimum `id`, `name`, `priority_tier` keys.
- [x] Pass <!-- 2026-06-08 -->

### UAT-TRAV-004: get_exercises_by_equipment returns empty list for unknown equipment

- **Description**: `get_exercises_by_equipment` for an equipment name not in the dataset must return `[]` (not raise an exception).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import asyncio, os
from neo4j import AsyncGraphDatabase
from app.knowledge_graph.traversal import get_exercises_by_equipment
async def run():
    driver = AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    result = await get_exercises_by_equipment('NonexistentEquipmentXYZ', driver)
    await driver.close()
    return result
rows = asyncio.run(run())
print('result:', rows)
"
  ```
- **Expected Result**: Prints `result: []` with no exception raised.
- [x] Pass <!-- 2026-06-08 -->

---

## Unit Test Regression Tests

### UAT-UNIT-001: Existing + new unit tests all pass

- **Description**: The pytest suite for `test_ingest_exercises.py` and `test_traversal.py` must pass in full, including: the new tests asserting `MERGE (m:Muscle`, `:TARGETS`, `:REQUIRES`, `:HAS_PATTERN` are present in `session.run` call args, and the new traversal helper tests using `_make_driver`.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -m pytest backend/tests/knowledge_graph/test_ingest_exercises.py backend/tests/knowledge_graph/test_traversal.py -v
  ```
- **Expected Result**: All tests pass (exit code 0). Output includes at minimum:
  - `test_ingest_exercises_calls_merge_and_edge_pass PASSED`
  - `test_load_exercises_returns_50 PASSED`
  - At least one test name containing `targeting_muscle` or `by_equipment` PASSED
  - Zero failures, zero errors
- [x] Pass <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: Empty equipment_required array produces no REQUIRES edges for that exercise

- **Description**: An exercise with `equipment_required: []` (e.g., a bodyweight exercise) must not create any `[:REQUIRES]` edges. The `UNWIND [] AS ...` pattern produces no rows and therefore no MERGE. This verifies the `or []` guard in `ingest_exercises`.
- **Steps**:
  1. Run the command below, which queries for a known bodyweight exercise (`Med Ball Scoop Toss` has no equipment per the dataset check).
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import json, neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
# First find an exercise with no equipment
with open('.docs/guides/1-multi-agent/exercises.json') as f:
    exercises = json.load(f)
bodyweight = [ex for ex in exercises if not ex.get('equipment_required')]
print('bodyweight exercises (no equipment_required):', [ex['name'] for ex in bodyweight[:3]])
if bodyweight:
    ex_name = bodyweight[0]['name']
    with driver.session() as s:
        result = s.run('MATCH (e:Exercise {name: \$name})-[:REQUIRES]->(eq) RETURN count(eq) AS c', name=ex_name)
        c = result.single()['c']
    print(f'REQUIRES edges for \"{ex_name}\":', c)
driver.close()
"
  ```
- **Expected Result**: The bodyweight exercise list is non-empty. The `REQUIRES` edge count for a bodyweight exercise is `0`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-002: Muscle node names match verbatim dataset values (no normalization)

- **Description**: Muscle node `name` properties must be stored exactly as they appear in `exercises.json` (lowercase, verbatim — e.g. `'hip adductors'`, `'lower back'`, not `'Hip Adductors'`). The task spec states no normalization.
- **Steps**:
  1. Run the command below to retrieve all Muscle node names and compare against known dataset values.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
with driver.session() as s:
    result = s.run('MATCH (m:Muscle) RETURN m.name AS name ORDER BY name')
    names = [r['name'] for r in result]
print('Muscle names:', names)
# Verify multi-word names are lowercase verbatim
multi_word = [n for n in names if ' ' in n]
print('Multi-word names:', multi_word)
driver.close()
"
  ```
- **Expected Result**: `Muscle names` list contains exactly 19 entries. The list includes `'hip adductors'`, `'lower back'`, `'middle back'`, `'upper back'`, `'hip flexors'`, `'rotator cuff'` (all lowercase, space-separated, verbatim from dataset). No title-case or normalized variants appear.
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-003: Equipment node names match verbatim dataset values (Title Case)

- **Description**: Equipment node `name` properties must be stored exactly as they appear in `exercises.json` (Title Case strings — e.g. `'Adjustable Bench - Decline'`, `'Yoga Mat'`).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/python -c "
import neo4j, os
driver = neo4j.GraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
with driver.session() as s:
    result = s.run('MATCH (eq:Equipment) RETURN eq.name AS name ORDER BY name')
    names = [r['name'] for r in result]
print('Equipment count:', len(names))
print('Equipment names:', names[:10])
driver.close()
"
  ```
- **Expected Result**: Exactly 32 equipment nodes. The list includes `'Adjustable Bench - Decline'`, `'Barbell'`, `'Dumbbell'` (Title Case, verbatim). No lowercase variants appear.
- [x] Pass <!-- 2026-06-08 -->
