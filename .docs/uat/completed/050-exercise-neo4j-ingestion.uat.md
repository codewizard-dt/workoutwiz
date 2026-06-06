# UAT: Exercise Neo4j Ingestion

> **Source task**: [`.docs/tasks/050-exercise-neo4j-ingestion.md`](../tasks/050-exercise-neo4j-ingestion.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Working directory is the repo root (`workout-wiz/`)
- [ ] Python virtual environment is activated with backend dependencies installed (`cd backend && pip install -e ".[dev]"`)
- [ ] `backend/app/knowledge_graph/ingest_exercises.py` exists and is importable
- [ ] `backend/tests/knowledge_graph/__init__.py` exists
- [ ] `backend/tests/knowledge_graph/test_ingest_exercises.py` exists
- [ ] `.docs/guides/1-multi-agent/exercises.json` exists and contains 50 records
- [ ] For live Neo4j tests: `docker-compose up -d neo4j` is running and healthy (port 7687 open)

---

## Script / Module Tests

### UAT-SCRIPT-001: Unit test suite passes with mocked driver

- **Description**: Verifies that both unit tests in `test_ingest_exercises.py` pass without a live Neo4j connection — the mocked-driver MERGE/edge-pass flow and the `exercises.json` count assertion.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -m pytest tests/knowledge_graph/test_ingest_exercises.py -v
  ```
- **Expected Result**: Both tests pass — output includes `PASSED tests/knowledge_graph/test_ingest_exercises.py::test_ingest_exercises_calls_merge_and_edge_pass` and `PASSED tests/knowledge_graph/test_ingest_exercises.py::test_load_exercises_returns_50`. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-002: `load_exercises` returns exactly 50 records with required fields

- **Description**: Verifies `load_exercises()` reads `exercises.json` and returns a list of 50 dicts each containing `id` and `joints_loaded` keys — directly matching the `test_load_exercises_returns_50` acceptance criterion.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "from app.knowledge_graph.ingest_exercises import load_exercises; data = load_exercises(); print(len(data)); assert len(data) == 50; assert all('id' in ex and 'joints_loaded' in ex for ex in data); print('OK')"
  ```
- **Expected Result**: Prints `50` then `OK`. No exception raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-003: `ingest_exercises` with mocked driver returns correct count and calls session.run the right number of times

- **Description**: Verifies that calling `ingest_exercises(mock_driver, exercises)` with a 3-exercise list calls `session.run` exactly 4 times (3 MERGE calls + 1 edge-pass call) and returns `3`.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises

sample = [
    {'id': 'aaa-001', 'name': 'Squat', 'muscle_groups': ['quads'], 'joints_loaded': ['knee'], 'movement_patterns': ['squat'], 'equipment_required': [], 'is_bilateral': True, 'side': None, 'priority_tier': 1, 'is_reps': True, 'is_duration': False, 'supports_weight': True, 'estimated_rep_duration': 1.0, 'bilateral_pair_id': None},
    {'id': 'aaa-002', 'name': 'Lunge', 'muscle_groups': ['quads'], 'joints_loaded': ['knee'], 'movement_patterns': ['lunge'], 'equipment_required': [], 'is_bilateral': False, 'side': 'left', 'priority_tier': 2, 'is_reps': True, 'is_duration': False, 'supports_weight': False, 'estimated_rep_duration': None, 'bilateral_pair_id': None},
    {'id': 'aaa-003', 'name': 'Plank', 'muscle_groups': ['core'], 'joints_loaded': [], 'movement_patterns': ['hold'], 'equipment_required': [], 'is_bilateral': True, 'side': None, 'priority_tier': 2, 'is_reps': False, 'is_duration': True, 'supports_weight': False, 'estimated_rep_duration': None, 'bilateral_pair_id': None},
]
mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

result = ingest_exercises(mock_driver, sample)
assert result == 3, f'Expected 3, got {result}'
assert mock_session.run.call_count == 4, f'Expected 4 session.run calls (3 MERGE + 1 edge pass), got {mock_session.run.call_count}'
print(f'OK: returned {result}, session.run called {mock_session.run.call_count} times')
"
  ```
- **Expected Result**: Prints `OK: returned 3, session.run called 4 times`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-004: `ingest_exercises` uses MERGE not CREATE in Cypher

- **Description**: Verifies the Cypher sent to `session.run` for each exercise starts with `MERGE (e:Exercise {id:` (not `CREATE`), ensuring idempotence.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises

sample = [{'id': 'aaa-001', 'name': 'Squat', 'muscle_groups': [], 'joints_loaded': [], 'movement_patterns': [], 'equipment_required': [], 'is_bilateral': True, 'side': None, 'priority_tier': 1, 'is_reps': True, 'is_duration': False, 'supports_weight': False, 'estimated_rep_duration': None, 'bilateral_pair_id': None}]
mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

ingest_exercises(mock_driver, sample)
exercise_call = mock_session.run.call_args_list[0]
cypher = exercise_call[0][0]
assert 'MERGE' in cypher, 'Expected MERGE in exercise Cypher'
assert 'CREATE' not in cypher, 'Found CREATE in exercise Cypher — must use MERGE for idempotence'
assert 'Exercise' in cypher and 'id' in cypher, 'Exercise node pattern not found'
print('OK: MERGE used, CREATE absent')
"
  ```
- **Expected Result**: Prints `OK: MERGE used, CREATE absent`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-005: `ingest_exercises` sets all 13 required Exercise properties

- **Description**: Verifies that the Cypher statement for each exercise sets all 13 non-id properties: `name`, `muscle_groups`, `joints_loaded`, `movement_patterns`, `equipment_required`, `is_reps`, `is_duration`, `supports_weight`, `priority_tier`, `is_bilateral`, `bilateral_pair_id`, `side`, `estimated_rep_duration`.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises

sample = [{'id': 'aaa-001', 'name': 'Squat', 'muscle_groups': [], 'joints_loaded': [], 'movement_patterns': [], 'equipment_required': [], 'is_bilateral': True, 'side': None, 'priority_tier': 1, 'is_reps': True, 'is_duration': False, 'supports_weight': False, 'estimated_rep_duration': 1.5, 'bilateral_pair_id': None}]
mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

ingest_exercises(mock_driver, sample)
cypher = mock_session.run.call_args_list[0][0][0]
required_props = ['name', 'muscle_groups', 'joints_loaded', 'movement_patterns', 'equipment_required', 'is_reps', 'is_duration', 'supports_weight', 'priority_tier', 'is_bilateral', 'bilateral_pair_id', 'side', 'estimated_rep_duration']
missing = [p for p in required_props if p not in cypher]
assert not missing, f'Missing properties in Cypher: {missing}'
print(f'OK: all {len(required_props)} properties present in Cypher')
"
  ```
- **Expected Result**: Prints `OK: all 13 properties present in Cypher`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-006: `ingest_exercises` passes correct default values for missing fields

- **Description**: Verifies the default parameter handling — `is_reps` defaults to `True`, `is_duration` defaults to `False`, `supports_weight` defaults to `False`, `priority_tier` defaults to `3`, `is_bilateral` defaults to `True`, and list fields default to `[]` when absent from the exercise dict.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock, call
from app.knowledge_graph.ingest_exercises import ingest_exercises

# Exercise with only id and name — all other fields absent
sample = [{'id': 'minimal-001', 'name': 'Minimal'}]
mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

ingest_exercises(mock_driver, sample)
# kwargs passed to session.run for the exercise MERGE
kwargs = mock_session.run.call_args_list[0][1]
assert kwargs['muscle_groups'] == [], f'muscle_groups: {kwargs[\"muscle_groups\"]}'
assert kwargs['joints_loaded'] == [], f'joints_loaded: {kwargs[\"joints_loaded\"]}'
assert kwargs['movement_patterns'] == [], f'movement_patterns: {kwargs[\"movement_patterns\"]}'
assert kwargs['equipment_required'] == [], f'equipment_required: {kwargs[\"equipment_required\"]}'
assert kwargs['is_reps'] == True, f'is_reps: {kwargs[\"is_reps\"]}'
assert kwargs['is_duration'] == False, f'is_duration: {kwargs[\"is_duration\"]}'
assert kwargs['supports_weight'] == False, f'supports_weight: {kwargs[\"supports_weight\"]}'
assert kwargs['priority_tier'] == 3, f'priority_tier: {kwargs[\"priority_tier\"]}'
assert kwargs['is_bilateral'] == True, f'is_bilateral: {kwargs[\"is_bilateral\"]}'
assert kwargs['bilateral_pair_id'] is None, f'bilateral_pair_id: {kwargs[\"bilateral_pair_id\"]}'
print('OK: all defaults correct')
"
  ```
- **Expected Result**: Prints `OK: all defaults correct`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-007: `ingest_exercises` converts bilateral_pair_id to string when present

- **Description**: Verifies that a non-null `bilateral_pair_id` UUID in the exercise dict is converted to a string (via `str()`) before being passed to Cypher, and that a null `bilateral_pair_id` becomes `None`.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises
import uuid

pair_id = uuid.UUID('aaaaaaaa-0000-0000-0000-000000000002')
sample = [
    {'id': 'aaa-L', 'name': 'Left Lunge', 'bilateral_pair_id': pair_id},
    {'id': 'aaa-N', 'name': 'Plank', 'bilateral_pair_id': None},
]
mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

ingest_exercises(mock_driver, sample)
kwargs_first = mock_session.run.call_args_list[0][1]
kwargs_second = mock_session.run.call_args_list[1][1]
assert isinstance(kwargs_first['bilateral_pair_id'], str), f'Expected str, got {type(kwargs_first[\"bilateral_pair_id\"])}'
assert kwargs_first['bilateral_pair_id'] == str(pair_id)
assert kwargs_second['bilateral_pair_id'] is None
print('OK: bilateral_pair_id conversion correct')
"
  ```
- **Expected Result**: Prints `OK: bilateral_pair_id conversion correct`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-008: `ingest_exercises` runs CONTRAINDICATED_BY edge pass after all MERGE nodes

- **Description**: Verifies the edge-pass Cypher fires after all exercise MERGE calls, contains `CONTRAINDICATED_BY`, `Injury`, `status: 'active'`, and the joint-overlap `ANY()` clause.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises

sample = [
    {'id': 'aaa-001', 'name': 'Squat'},
    {'id': 'aaa-002', 'name': 'Lunge'},
]
mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

ingest_exercises(mock_driver, sample)
# Edge pass is the LAST call (index 2 for 2 exercises)
edge_call = mock_session.run.call_args_list[-1]
edge_cypher = edge_call[0][0]
assert 'CONTRAINDICATED_BY' in edge_cypher, 'Missing CONTRAINDICATED_BY'
assert 'Injury' in edge_cypher, 'Missing Injury node'
assert \"active\" in edge_cypher, 'Missing active status filter'
assert 'ANY' in edge_cypher, 'Missing ANY() joint-overlap clause'
assert 'joints_loaded' in edge_cypher, 'Missing joints_loaded in overlap check'
assert 'affected_joints' in edge_cypher, 'Missing affected_joints in overlap check'
print('OK: edge-pass Cypher contains all required clauses')
"
  ```
- **Expected Result**: Prints `OK: edge-pass Cypher contains all required clauses`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-009: `ingest_exercises` with `exercises=None` calls `load_exercises` (full 50-exercise path)

- **Description**: Verifies that passing `exercises=None` (or omitting the argument) causes `ingest_exercises` to load from `exercises.json` automatically, and that a mocked driver receives 51 `session.run` calls (50 MERGE + 1 edge pass).
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises

mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

result = ingest_exercises(mock_driver)  # exercises=None — should auto-load
assert result == 50, f'Expected 50, got {result}'
assert mock_session.run.call_count == 51, f'Expected 51 session.run calls (50 MERGE + 1 edge pass), got {mock_session.run.call_count}'
print(f'OK: auto-loaded {result} exercises, {mock_session.run.call_count} session.run calls')
"
  ```
- **Expected Result**: Prints `OK: auto-loaded 50 exercises, 51 session.run calls`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-010: `seed_exercises_neo4j` in `seed.py` delegates to `ingest_exercises`

- **Description**: Verifies that `seed.py`'s `seed_exercises_neo4j` function is a thin wrapper that calls `ingest_exercises(driver, exercises)` — no duplicated logic.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock, patch
from app.knowledge_graph.seed import seed_exercises_neo4j

sample = [{'id': 'aaa-001', 'name': 'Squat'}]
mock_driver = MagicMock()

with patch('app.knowledge_graph.seed.ingest_exercises') as mock_ingest:
    seed_exercises_neo4j(mock_driver, sample)
    mock_ingest.assert_called_once_with(mock_driver, sample)
    print('OK: seed_exercises_neo4j delegates to ingest_exercises')
"
  ```
- **Expected Result**: Prints `OK: seed_exercises_neo4j delegates to ingest_exercises`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Module is importable without a live Neo4j connection

- **Description**: Verifies the module can be imported in isolation — no import-time connection attempt, no side effects.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "import app.knowledge_graph.ingest_exercises; print('OK: module imported cleanly')"
  ```
- **Expected Result**: Prints `OK: module imported cleanly`. No connection error or import error.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: `__main__` entry point is runnable as a module (dry-run with mocked driver)

- **Description**: Verifies the module is invokable via `python -m app.knowledge_graph.ingest_exercises` and that the entry point wires settings correctly. Uses a mock to avoid requiring a live Neo4j instance.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock, patch
from app.config import settings

mock_session = MagicMock()
mock_driver_instance = MagicMock()
mock_driver_instance.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver_instance.session.return_value.__exit__ = MagicMock(return_value=False)
mock_driver_instance.__enter__ = MagicMock(return_value=mock_driver_instance)
mock_driver_instance.__exit__ = MagicMock(return_value=False)

with patch('neo4j.GraphDatabase.driver', return_value=mock_driver_instance) as mock_gd:
    import runpy
    runpy.run_module('app.knowledge_graph.ingest_exercises', run_name='__main__')
    mock_gd.assert_called_once_with(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    print('OK: __main__ called GraphDatabase.driver with correct settings')
"
  ```
- **Expected Result**: Prints `OK: __main__ called GraphDatabase.driver with correct settings` along with log output starting with `INFO`. No exception raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: Live `__main__` run against real Neo4j prints correct completion message

- **Description**: When a real Neo4j instance is running, the `__main__` entry point should print `Done. 50 exercises ingested.` to stdout.
- **Prerequisite**: Neo4j running at `bolt://localhost:7687` with user `neo4j` / password `password` (or as configured in `.env`)
- **Steps**:
  1. Ensure Neo4j is running: `docker-compose up -d neo4j`
  2. Wait for Neo4j to be healthy (check with `docker-compose ps`)
  3. From the repo root, source environment and run the module
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.ingest_exercises
  ```
- **Expected Result**: stdout contains `Done. 50 exercises ingested.` and INFO log line `Ingested 50 exercises; CONTRAINDICATED_BY edges merged.`. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-004: Idempotence — running ingestion twice produces no duplicates

- **Description**: Running `ingest_exercises` twice against a live Neo4j (using `MERGE`) must not create duplicate Exercise nodes. The second run should update existing nodes, not create new ones.
- **Prerequisite**: Neo4j running and healthy (UAT-EDGE-003 already run at least once)
- **Steps**:
  1. Run the ingestion twice (the second run should be idempotent)
  2. Then count Exercise nodes in Neo4j
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.ingest_exercises && python -c "
import neo4j, os
uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
user = os.environ.get('NEO4J_USER', 'neo4j')
password = os.environ.get('NEO4J_PASSWORD', 'password')
with neo4j.GraphDatabase.driver(uri, auth=(user, password)) as driver:
    with driver.session() as session:
        result = session.run('MATCH (e:Exercise) RETURN count(e) AS cnt')
        cnt = result.single()['cnt']
        assert cnt == 50, f'Expected 50 Exercise nodes, found {cnt}'
        print(f'OK: exactly {cnt} Exercise nodes — no duplicates')
"
  ```
- **Expected Result**: Prints `OK: exactly 50 Exercise nodes — no duplicates`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: `exercises.json` all 50 exercises ingested with correct field types

- **Description**: Verifies end-to-end that `ingest_exercises` processes all 50 real exercises from `exercises.json` with a mocked driver, and that all required fields are present and correctly typed in the kwargs passed to `session.run`.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises, load_exercises

mock_session = MagicMock()
mock_driver = MagicMock()
mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

exercises = load_exercises()
result = ingest_exercises(mock_driver, exercises)

assert result == 50
# Validate every exercise MERGE call (first 50 calls, last is edge pass)
exercise_calls = mock_session.run.call_args_list[:50]
assert len(exercise_calls) == 50

errors = []
for i, c in enumerate(exercise_calls):
    kw = c[1]
    if not isinstance(kw.get('muscle_groups'), list): errors.append(f'ex[{i}] muscle_groups not list')
    if not isinstance(kw.get('joints_loaded'), list): errors.append(f'ex[{i}] joints_loaded not list')
    if not isinstance(kw.get('movement_patterns'), list): errors.append(f'ex[{i}] movement_patterns not list')
    if not isinstance(kw.get('equipment_required'), list): errors.append(f'ex[{i}] equipment_required not list')
    if not isinstance(kw.get('is_reps'), bool): errors.append(f'ex[{i}] is_reps not bool')
    if not isinstance(kw.get('is_duration'), bool): errors.append(f'ex[{i}] is_duration not bool')
    if not isinstance(kw.get('supports_weight'), bool): errors.append(f'ex[{i}] supports_weight not bool')
    if not isinstance(kw.get('priority_tier'), int): errors.append(f'ex[{i}] priority_tier not int')
    if not isinstance(kw.get('is_bilateral'), bool): errors.append(f'ex[{i}] is_bilateral not bool')
    if not isinstance(kw.get('name'), str): errors.append(f'ex[{i}] name not str')
    if not isinstance(kw.get('id'), str): errors.append(f'ex[{i}] id not str')

if errors:
    for e in errors[:10]: print('FAIL:', e)
    raise AssertionError(f'{len(errors)} type errors found')
print(f'OK: all 50 exercises processed with correct field types')
"
  ```
- **Expected Result**: Prints `OK: all 50 exercises processed with correct field types`. No assertion error.
- [x] Pass <!-- 2026-06-06 -->
