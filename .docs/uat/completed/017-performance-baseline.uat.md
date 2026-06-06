# UAT: Performance Baseline

> **Source task**: [`.docs/tasks/017-performance-baseline.md`](../tasks/017-performance-baseline.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [x] PostgreSQL running and accessible
- [x] Backend server running on `http://localhost:8000`
- [x] Alembic migrations applied (`cd backend && .venv/bin/alembic upgrade head`)
- [x] `backend/.venv` exists with all dependencies installed (including `httpx`)
- [x] Working directory for script commands: `backend/`

---

## File Existence Tests

### UAT-FILE-001: perf_baseline.py script exists

Verify the performance measurement script was created at the required path.

**Command**:
```bash
python3 -c "import pathlib; p = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/scripts/perf_baseline.py'); assert p.exists(), f'Missing: {p}'; print('PASS: perf_baseline.py exists')"
```

**Expected**: `PASS: perf_baseline.py exists`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-002: PERFORMANCE.md exists with measured values

Verify the performance document was created and contains actual numeric measurements (not placeholder `X.X` values).

**Command**:
```bash
python3 -c "
import pathlib, re
text = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/PERFORMANCE.md').read_text()
assert 'X.X' not in text, 'PERFORMANCE.md still contains placeholder X.X values'
# Verify it has a table with numeric data
assert re.search(r'\|\s*GET /exercises/\s*\|\s*[\d.]+', text), 'No numeric avg for GET /exercises/'
assert re.search(r'\|\s*GET /workouts/\s*\|\s*[\d.]+', text), 'No numeric avg for GET /workouts/'
print('PASS: PERFORMANCE.md contains measured numeric values')
"
```

**Expected**: `PASS: PERFORMANCE.md contains measured numeric values`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-003: GIN index migration file exists

Verify the Alembic migration for GIN indexes was created.

**Command**:
```bash
python3 -c "
import pathlib, glob
versions_dir = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/migrations/versions')
matches = list(versions_dir.glob('*gin*'))
assert matches, f'No GIN migration file found in {versions_dir}'
print(f'PASS: GIN migration found: {matches[0].name}')
"
```

**Expected**: `PASS: GIN migration found: <filename>_add_gin_indexes_for_exercise_arrays.py` (or similar)

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-004: GIN migration contains both required indexes

Verify the migration file creates GIN indexes for both `muscle_groups` and `equipment_required`.

**Command**:
```bash
python3 -c "
import pathlib, glob
versions_dir = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/migrations/versions')
match = next(versions_dir.glob('*gin*'))
text = match.read_text()
assert 'ix_exercises_muscle_groups_gin' in text, 'muscle_groups GIN index missing from migration'
assert 'ix_exercises_equipment_required_gin' in text, 'equipment_required GIN index missing from migration'
assert 'USING GIN' in text, 'USING GIN clause missing from migration'
print('PASS: Both GIN indexes present in migration')
"
```

**Expected**: `PASS: Both GIN indexes present in migration`

- [x] Pass <!-- 2026-06-04 -->

---

## Script Execution Tests

### UAT-SCRIPT-001: perf_baseline.py script structure is valid Python

Verify the script parses without syntax errors and contains the required `measure` and `main` async functions.

**Command**:
```bash
python3 -c "
import ast, pathlib
src = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/scripts/perf_baseline.py').read_text()
tree = ast.parse(src)
async_fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]
assert 'measure' in async_fns, 'measure() async function missing'
assert 'main' in async_fns, 'main() async function missing'
print('PASS: perf_baseline.py is valid Python with measure() and main()')
"
```

**Expected**: `PASS: perf_baseline.py is valid Python with measure() and main()`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-SCRIPT-002: perf_baseline.py covers all required endpoints

Verify the script measures all four required endpoints from the task spec.

**Command**:
```bash
python3 -c "
import pathlib
text = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/scripts/perf_baseline.py').read_text()
required = ['/exercises/', '/exercises/?name=squat', '/exercises/?muscle_groups=chest', '/workouts/']
for ep in required:
    assert ep in text, f'Endpoint {ep} not measured in script'
print('PASS: All 4 required endpoints are measured')
"
```

**Expected**: `PASS: All 4 required endpoints are measured`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-SCRIPT-003: perf_baseline.py runs against live server and prints table

Run the script against the running server. Verifies no server errors and that avg/P95 columns are printed.

**Prerequisites**: Server must be running on `http://localhost:8000` before running this test.

**Command**:
```bash
cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && .venv/bin/python scripts/perf_baseline.py
```

**Expected**:
- Exit code 0 (no assertion errors)
- Output table with header row `Endpoint`, `Avg (ms)`, `P95 (ms)`
- Four data rows, one per measured endpoint
- All numeric values printed (no errors or tracebacks)

- [x] Pass <!-- 2026-06-04 -->

---

## PERFORMANCE.md Content Tests

### UAT-PERF-001: PERFORMANCE.md targets met — exercises avg < 50ms

Verify the recorded avg response times for exercise endpoints are below the 50ms target.

**Command**:
```bash
python3 -c "
import pathlib, re
text = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/PERFORMANCE.md').read_text()
# Extract avg values for exercise endpoints
rows = re.findall(r'\|\s*(GET /exercises/[^|]*)\|\s*([\d.]+)\s*\|', text)
assert rows, 'No exercise endpoint rows found in PERFORMANCE.md table'
for label, avg in rows:
    avg_f = float(avg)
    assert avg_f < 50.0, f'{label.strip()} avg {avg_f}ms exceeds 50ms target'
    print(f'PASS: {label.strip()} avg={avg_f}ms < 50ms')
"
```

**Expected**: Three `PASS` lines (one per exercise endpoint), each showing avg < 50ms.

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-PERF-002: PERFORMANCE.md targets met — workouts avg < 100ms

Verify the recorded avg response time for `GET /workouts/` is below the 100ms target.

**Command**:
```bash
python3 -c "
import pathlib, re
text = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/PERFORMANCE.md').read_text()
match = re.search(r'\|\s*GET /workouts/\s*\|\s*([\d.]+)\s*\|', text)
assert match, 'GET /workouts/ row not found in PERFORMANCE.md'
avg = float(match.group(1))
assert avg < 100.0, f'GET /workouts/ avg {avg}ms exceeds 100ms target'
print(f'PASS: GET /workouts/ avg={avg}ms < 100ms')
"
```

**Expected**: `PASS: GET /workouts/ avg=<number>ms < 100ms`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-PERF-003: PERFORMANCE.md documents GIN index notes

Verify the document includes the index notes section referencing both GIN indexes.

**Command**:
```bash
python3 -c "
import pathlib
text = pathlib.Path('/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/PERFORMANCE.md').read_text()
assert 'ix_exercises_muscle_groups_gin' in text, 'muscle_groups GIN index not documented'
assert 'ix_exercises_equipment_required_gin' in text, 'equipment_required GIN index not documented'
print('PASS: Both GIN indexes documented in PERFORMANCE.md')
"
```

**Expected**: `PASS: Both GIN indexes documented in PERFORMANCE.md`

- [x] Pass <!-- 2026-06-04 -->

---

## Coverage Summary

| Area | Tests | Criteria |
|------|-------|----------|
| File existence | 4 | perf_baseline.py, PERFORMANCE.md, GIN migration file, migration content |
| Script validity | 2 | Python syntax + required functions, all 4 endpoints present |
| Script execution | 1 | Runs against live server, prints table, no errors |
| PERFORMANCE.md content | 3 | Exercise avg < 50ms, workouts avg < 100ms, GIN indexes documented |
| **Total** | **10** | All must pass |
