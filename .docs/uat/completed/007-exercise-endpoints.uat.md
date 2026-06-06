# UAT: Exercise Endpoints

> **Source task**: [`.docs/tasks/completed/007-exercise-endpoints.md`](../tasks/completed/007-exercise-endpoints.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] PostgreSQL running on localhost:5432 with database `workoutwiz`
- [ ] Alembic migrations applied and exercise seed data loaded (50 exercises from `1-multi-agent/exercises.json`)
- [ ] `backend/.venv/bin/python` available

---

## API Tests

All tests below are in-process Python scripts using `httpx.AsyncClient` with `ASGITransport` against the real database on localhost:5432. Run each with `backend/.venv/bin/python`.

---

### UAT-API-001: ExerciseRead schema has correct fields and movement_patterns is list[str]

- **Endpoint**: N/A (import test)
- **Description**: Verify `ExerciseRead` is importable and `movement_patterns` is typed as `list[str]`, not `dict`.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import typing, uuid
from app.schemas.exercise import ExerciseRead
hints = typing.get_type_hints(ExerciseRead)
assert hints['movement_patterns'] == list[str], f'Expected list[str], got {hints[\"movement_patterns\"]}'
assert hints['id'] == uuid.UUID
assert hints['name'] == str
assert hints['category'] == str
assert hints['muscle_groups'] == list[str]
assert hints['equipment_required'] == list[str]
assert hints['is_reps'] == bool
assert hints['is_duration'] == bool
assert hints['supports_weight'] == bool
assert hints['is_bilateral'] == bool
assert hints['priority_tier'] == int
print('OK: ExerciseRead fields verified, movement_patterns is list[str]')
"
  ```
- **Expected Result**: Prints `OK: ExerciseRead fields verified, movement_patterns is list[str]` with no assertion errors.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-002: list_exercises service is importable and accepts correct params

- **Endpoint**: N/A (import test)
- **Description**: Verify `list_exercises` is importable from `app.services.exercises` and has the expected signature.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import inspect
from app.services.exercises import list_exercises
sig = inspect.signature(list_exercises)
params = list(sig.parameters.keys())
assert 'session' in params, f'missing session param'
assert 'name' in params, f'missing name param'
assert 'muscle_groups' in params, f'missing muscle_groups param'
assert 'equipment' in params, f'missing equipment param'
assert 'priority_tier' in params, f'missing priority_tier param'
print('OK: list_exercises importable with correct params:', params)
"
  ```
- **Expected Result**: Prints `OK: list_exercises importable with correct params: ['session', 'name', 'muscle_groups', 'equipment', 'priority_tier']` with no assertion errors.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-003: GET /exercises/ returns 200 with all 50 exercises

- **Endpoint**: `GET /exercises/`
- **Description**: Verify the endpoint returns HTTP 200 with exactly 50 exercises when no filters are applied.
- **Steps**:
  1. Run the command below (requires DB on localhost:5432 with seed data)
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio, os, sys
sys.path.insert(0, 'backend')
os.chdir('backend')
import httpx
from httpx import ASGITransport
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.get('/exercises/')
        assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
        data = r.json()
        assert isinstance(data, list), f'Expected list, got {type(data)}'
        assert len(data) == 50, f'Expected 50 exercises, got {len(data)}'
        ex = data[0]
        for field in ['id','name','category','muscle_groups','equipment_required','movement_patterns','is_reps','is_duration','supports_weight','is_bilateral','priority_tier']:
            assert field in ex, f'Missing field: {field}'
        assert isinstance(ex['movement_patterns'], list), f'movement_patterns should be list, got {type(ex[\"movement_patterns\"])}'
        print(f'OK: 200, {len(data)} exercises, first: {ex[\"name\"]}')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `OK: 200, 50 exercises, first: <name>` with no assertion errors.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-004: GET /exercises/?name=squat returns exercises with "squat" in name

- **Endpoint**: `GET /exercises/?name=squat`
- **Description**: Verify case-insensitive name filter returns only exercises whose name contains "squat".
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio, os, sys
sys.path.insert(0, 'backend')
os.chdir('backend')
import httpx
from httpx import ASGITransport
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.get('/exercises/', params={'name': 'squat'})
        assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
        data = r.json()
        assert len(data) > 0, 'Expected at least one squat exercise'
        for ex in data:
            assert 'squat' in ex['name'].lower(), f'Name does not contain squat: {ex[\"name\"]}'
        print(f'OK: {len(data)} squat exercises: {[e[\"name\"] for e in data]}')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `OK: N squat exercises: [...]` where all names contain "squat" (case-insensitive).
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-005: GET /exercises/?muscle_groups=chest returns exercises with chest in muscle_groups

- **Endpoint**: `GET /exercises/?muscle_groups=chest`
- **Description**: Verify muscle_groups filter returns exercises that include "chest" in their muscle_groups array.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio, os, sys
sys.path.insert(0, 'backend')
os.chdir('backend')
import httpx
from httpx import ASGITransport
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.get('/exercises/', params={'muscle_groups': 'chest'})
        assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
        data = r.json()
        assert len(data) > 0, 'Expected at least one chest exercise'
        for ex in data:
            assert 'chest' in ex['muscle_groups'], f'chest not in muscle_groups for {ex[\"name\"]}: {ex[\"muscle_groups\"]}'
        print(f'OK: {len(data)} chest exercises: {[e[\"name\"] for e in data]}')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `OK: N chest exercises: [...]` where every exercise has "chest" in its muscle_groups list.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-006: GET /exercises/?equipment=barbell returns exercises with barbell equipment

- **Endpoint**: `GET /exercises/?equipment=barbell`
- **Description**: Verify equipment filter returns only exercises that include "barbell" in equipment_required.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio, os, sys
sys.path.insert(0, 'backend')
os.chdir('backend')
import httpx
from httpx import ASGITransport
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.get('/exercises/', params={'equipment': 'barbell'})
        assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
        data = r.json()
        assert len(data) > 0, 'Expected at least one barbell exercise'
        for ex in data:
            assert 'barbell' in ex['equipment_required'], f'barbell not in equipment_required for {ex[\"name\"]}: {ex[\"equipment_required\"]}'
        print(f'OK: {len(data)} barbell exercises: {[e[\"name\"] for e in data]}')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `OK: N barbell exercises: [...]` where every exercise has "barbell" in equipment_required.
- [x] Pass <!-- 2026-06-04 -->

---

## Edge Case Tests

### UAT-EDGE-001: GET /exercises/?priority_tier=4 returns 422 validation error

- **Endpoint**: `GET /exercises/?priority_tier=4`
- **Description**: Verify that `priority_tier=4` is rejected with HTTP 422 since the allowed range is `ge=1, le=3`.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio, os, sys
sys.path.insert(0, 'backend')
os.chdir('backend')
import httpx
from httpx import ASGITransport
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.get('/exercises/', params={'priority_tier': '4'})
        assert r.status_code == 422, f'Expected 422, got {r.status_code}: {r.text}'
        body = r.json()
        assert 'detail' in body, f'Expected detail in error body: {body}'
        print(f'OK: 422 received for priority_tier=4, detail: {body[\"detail\"]}')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `OK: 422 received for priority_tier=4, detail: [...]` — FastAPI validation error because 4 exceeds `le=3`.
- [x] Pass <!-- 2026-06-04 -->
