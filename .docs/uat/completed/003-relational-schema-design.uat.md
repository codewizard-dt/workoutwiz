# UAT: Relational Schema Design

> **Source task**: [`.docs/tasks/completed/003-relational-schema-design.md`](../tasks/completed/003-relational-schema-design.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] `backend/.venv` exists with SQLAlchemy and its PostgreSQL dialect packages installed
- [ ] Working directory is the repo root (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz`)
- [ ] No running database required — all tests are static (AST / import / introspection checks)

---

## Static Model Tests

### UAT-STATIC-001: Exercise model — table name and column types

- **File**: `backend/app/models/exercise.py`
- **Description**: Verify `Exercise.__tablename__` is `"exercises"` and that `muscle_groups`, `equipment_required`, and `movement_patterns` use the correct PostgreSQL dialect column types (ARRAY and JSON), and that `id` uses UUID.
- **Steps**:
  1. Run the command below. It imports the model via `sys.path` manipulation and introspects the mapped columns.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.models.exercise import Exercise
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID as PGUUID
from sqlalchemy import inspect as sainspect
mapper = sainspect(Exercise)
cols = {c.key: c for c in mapper.mapper.column_attrs}
assert Exercise.__tablename__ == 'exercises', f'bad tablename: {Exercise.__tablename__}'
mg_type = cols['muscle_groups'].columns[0].type
eq_type = cols['equipment_required'].columns[0].type
mp_type = cols['movement_patterns'].columns[0].type
id_type = cols['id'].columns[0].type
assert isinstance(mg_type, ARRAY), f'muscle_groups not ARRAY: {mg_type}'
assert isinstance(eq_type, ARRAY), f'equipment_required not ARRAY: {eq_type}'
assert isinstance(mp_type, JSON), f'movement_patterns not JSON: {mp_type}'
assert isinstance(id_type, PGUUID), f'id not UUID: {id_type}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-002: Exercise model — all required fields present

- **File**: `backend/app/models/exercise.py`
- **Description**: Verify all fields from the exercises.json schema are represented as mapped columns on the `Exercise` model.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.models.exercise import Exercise
from sqlalchemy import inspect as sainspect
mapper = sainspect(Exercise)
col_keys = {c.key for c in mapper.mapper.column_attrs}
required = {'id','name','category','muscle_groups','equipment_required','movement_patterns','is_reps','is_duration','supports_weight','is_bilateral','bilateral_pair_id','priority_tier','description'}
missing = required - col_keys
assert not missing, f'Missing columns: {missing}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-003: Workout and WorkoutSequence models exist with correct FK relationships

- **File**: `backend/app/models/workout.py`
- **Description**: Verify `Workout.__tablename__ == "workouts"`, `WorkoutSequence.__tablename__ == "workout_sequences"`, and that `WorkoutSequence.workout_id` has a FK to `workouts.id` with `CASCADE` delete.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.models.workout import Workout, WorkoutSequence
from sqlalchemy import inspect as sainspect
assert Workout.__tablename__ == 'workouts', f'bad tablename: {Workout.__tablename__}'
assert WorkoutSequence.__tablename__ == 'workout_sequences', f'bad tablename: {WorkoutSequence.__tablename__}'
mapper = sainspect(WorkoutSequence)
wid_col = mapper.mapper.column_attrs['workout_id'].columns[0]
fks = wid_col.foreign_keys
assert fks, 'workout_id has no foreign keys'
fk = list(fks)[0]
assert 'workouts.id' in str(fk.target_fullname), f'FK target wrong: {fk.target_fullname}'
assert fk.ondelete and fk.ondelete.upper() == 'CASCADE', f'ondelete not CASCADE: {fk.ondelete}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-004: WorkoutSet model exists with correct FK relationships

- **File**: `backend/app/models/workout.py`
- **Description**: Verify `WorkoutSet.__tablename__ == "workout_sets"`, FK from `sequence_id` → `workout_sequences.id` (CASCADE), and FK from `exercise_id` → `exercises.id` (no cascade).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.models.workout import WorkoutSet
from sqlalchemy import inspect as sainspect
assert WorkoutSet.__tablename__ == 'workout_sets', f'bad tablename: {WorkoutSet.__tablename__}'
mapper = sainspect(WorkoutSet)
seq_col = mapper.mapper.column_attrs['sequence_id'].columns[0]
seq_fks = list(seq_col.foreign_keys)
assert seq_fks, 'sequence_id has no foreign keys'
seq_fk = seq_fks[0]
assert 'workout_sequences.id' in str(seq_fk.target_fullname), f'FK target wrong: {seq_fk.target_fullname}'
assert seq_fk.ondelete and seq_fk.ondelete.upper() == 'CASCADE', f'sequence_id ondelete not CASCADE: {seq_fk.ondelete}'
ex_col = mapper.mapper.column_attrs['exercise_id'].columns[0]
ex_fks = list(ex_col.foreign_keys)
assert ex_fks, 'exercise_id has no foreign keys'
ex_fk = ex_fks[0]
assert 'exercises.id' in str(ex_fk.target_fullname), f'exercise FK target wrong: {ex_fk.target_fullname}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-005: WorkoutPhase enum has warmup/main/cooldown values

- **File**: `backend/app/models/workout.py`
- **Description**: Verify `WorkoutPhase` is a Python enum with string values `"warmup"`, `"main"`, `"cooldown"`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.models.workout import WorkoutPhase
values = {m.value for m in WorkoutPhase}
assert values == {'warmup', 'main', 'cooldown'}, f'Unexpected values: {values}'
assert WorkoutPhase.WARMUP.value == 'warmup'
assert WorkoutPhase.MAIN.value == 'main'
assert WorkoutPhase.COOLDOWN.value == 'cooldown'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-006: SetType enum has STRENGTH/CARDIO values

- **File**: `backend/app/models/workout.py`
- **Description**: Verify `SetType` is a Python enum with string values `"STRENGTH"` and `"CARDIO"`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.models.workout import SetType
values = {m.value for m in SetType}
assert values == {'STRENGTH', 'CARDIO'}, f'Unexpected values: {values}'
assert SetType.STRENGTH.value == 'STRENGTH'
assert SetType.CARDIO.value == 'CARDIO'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-007: models/__init__.py exports all 6 required symbols

- **File**: `backend/app/models/__init__.py`
- **Description**: Verify the package exports exactly these 6 symbols via `__all__`: `Exercise`, `Workout`, `WorkoutSequence`, `WorkoutSet`, `WorkoutPhase`, `SetType`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
import app.models as m
required = {'Exercise','Workout','WorkoutSequence','WorkoutSet','WorkoutPhase','SetType'}
assert hasattr(m, '__all__'), '__all__ not defined in app.models'
exported = set(m.__all__)
missing = required - exported
extra = exported - required
assert not missing, f'Missing from __all__: {missing}'
assert not extra, f'Unexpected in __all__: {extra}'
for sym in required:
    assert hasattr(m, sym), f'{sym} not importable from app.models'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-008: Migration file contains exercises and workouts table creates

- **File**: `backend/migrations/versions/077a1da3f52a_create_exercises_workouts_sequences_sets.py`
- **Description**: Verify the migration file under `migrations/versions/` contains `create_table` calls for both `'exercises'` and `'workouts'` (and by extension the full schema).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import ast, glob, os, sys
versions_dir = 'backend/migrations/versions'
py_files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and f != '__init__.py' and f != '.gitkeep']
assert py_files, 'No migration files found in backend/migrations/versions/'
found_exercises = False
found_workouts = False
for fname in py_files:
    src = open(os.path.join(versions_dir, fname)).read()
    if 'exercises' in src and 'workouts' in src:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                fname_str = getattr(func, 'attr', None) or getattr(func, 'id', None)
                if fname_str == 'create_table':
                    if node.args and isinstance(node.args[0], ast.Constant):
                        tname = node.args[0].value
                        if tname == 'exercises':
                            found_exercises = True
                        if tname == 'workouts':
                            found_workouts = True
assert found_exercises, 'No create_table(\"exercises\", ...) found in any migration'
assert found_workouts, 'No create_table(\"workouts\", ...) found in any migration'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-009: All Python model and migration files are syntactically valid

- **Description**: Verify that all `.py` files under `backend/app/models/` and `backend/migrations/versions/` parse without `SyntaxError`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import ast, os
dirs = ['backend/app/models', 'backend/migrations/versions']
files_checked = 0
for d in dirs:
    for fname in os.listdir(d):
        if not fname.endswith('.py'):
            continue
        path = os.path.join(d, fname)
        src = open(path).read()
        try:
            ast.parse(src)
            files_checked += 1
        except SyntaxError as e:
            raise AssertionError(f'SyntaxError in {path}: {e}')
assert files_checked > 0, 'No Python files found to check'
print(f'PASS ({files_checked} files checked)')
"
  ```
- **Expected Result**: Prints `PASS (N files checked)` with exit code 0 where N >= 3.
- [x] Pass <!-- 2026-06-04 -->
