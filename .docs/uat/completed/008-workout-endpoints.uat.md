# UAT: Workout CRUD Endpoints

> **Source task**: [`.docs/tasks/completed/008-workout-endpoints.md`](../../tasks/completed/008-workout-endpoints.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] PostgreSQL running on localhost:5432, database `workoutwiz` exists
- [ ] Alembic migrations applied (`cd backend && .venv/bin/alembic upgrade head`)
- [ ] Exercise seed data loaded (exercises table populated from `1-multi-agent/exercises.json`)
- [ ] `backend/.venv` exists with all dependencies installed
- [ ] Working directory for test scripts: `backend/`

---

## Import / Smoke Tests

### UAT-IMPORT-001: WorkoutCreate and WorkoutRead schemas import correctly

- **Description**: Verify the workout Pydantic schemas are importable and expose the expected classes.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.schemas.workout import WorkoutCreate, WorkoutRead; print('WorkoutCreate:', WorkoutCreate.__name__); print('WorkoutRead:', WorkoutRead.__name__)"
  ```
- **Expected Result**: Exits 0. Prints `WorkoutCreate: WorkoutCreate` and `WorkoutRead: WorkoutRead` with no import errors.
- [x] Pass <!-- 2026-06-04 -->

### UAT-IMPORT-002: Workouts service functions are importable

- **Description**: Verify all four service functions are importable from `app.services.workouts`.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.services.workouts import get_user_workouts, create_workout, update_workout, delete_workout; print('all imported')"
  ```
- **Expected Result**: Exits 0. Prints `all imported` with no import errors.
- [x] Pass <!-- 2026-06-04 -->

---

## API Tests

### UAT-API-001: POST /workouts/ without auth returns 401

- **Endpoint**: `POST /workouts/`
- **Description**: Verify that the create endpoint requires authentication.
- **Steps**:
  1. Save the script below as `./tmp/uat_008_no_auth.py`, then run it
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        r = await c.post('/workouts/', json={'started_at': '2026-01-01T10:00:00Z', 'sequences': []})
        print('status:', r.status_code)
        assert r.status_code == 401, f'expected 401, got {r.status_code}: {r.text}'
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `status: 401` then `PASS`.
- [x] Pass <!-- 2026-06-04 -->

### UAT-API-002: GET /workouts/ without auth returns 401

- **Endpoint**: `GET /workouts/`
- **Description**: Verify the list endpoint requires authentication.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        r = await c.get('/workouts/')
        print('status:', r.status_code)
        assert r.status_code == 401, f'expected 401, got {r.status_code}: {r.text}'
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `status: 401` then `PASS`.
- [x] Pass <!-- 2026-06-04 -->

### UAT-API-003: POST /workouts/ with auth creates workout and returns 201 with nested sequences/sets

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /workouts/`
- **Description**: Verify authenticated POST creates a workout with nested sequences and sets; returns 201 with full `WorkoutRead` body including nested sequences and sets.
- **Steps**:
  1. Run the script below from `backend/`. It registers a user, logs in, then POSTs a workout with one sequence and one set.
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx, uuid
from app.main import app

EMAIL = f'uat008-{uuid.uuid4().hex[:8]}@test.com'
PASSWORD = 'TestPass123!'
EXERCISE_ID = '0b3178cf-bf89-45a3-bfb0-27310ef6ef38'

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        await c.post('/auth/register', json={'email': EMAIL, 'password': PASSWORD})
        login = await c.post('/auth/jwt/login', data={'username': EMAIL, 'password': PASSWORD})
        assert login.status_code == 200, f'login failed: {login.text}'
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        payload = {
            'started_at': '2026-01-01T10:00:00Z',
            'ended_at': '2026-01-01T11:00:00Z',
            'sequences': [{
                'phase': 'main',
                'position': 0,
                'sets': [{
                    'exercise_id': EXERCISE_ID,
                    'set_type': 'STRENGTH',
                    'position': 0,
                    'reps': 10,
                    'weight_kg': 80.0
                }]
            }]
        }
        r = await c.post('/workouts/', json=payload, headers=headers)
        print('status:', r.status_code)
        assert r.status_code == 201, f'expected 201, got {r.status_code}: {r.text}'
        body = r.json()
        assert 'id' in body, 'missing id'
        assert 'user_id' in body, 'missing user_id'
        assert 'sequences' in body, 'missing sequences'
        assert len(body['sequences']) == 1, f'expected 1 sequence, got {len(body[\"sequences\"])}'
        assert len(body['sequences'][0]['sets']) == 1, 'expected 1 set'
        assert body['sequences'][0]['phase'] == 'main'
        assert body['sequences'][0]['sets'][0]['reps'] == 10
        print('workout_id:', body['id'])
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `status: 201`, `workout_id: <uuid>`, then `PASS`. Body has `id`, `user_id`, `started_at`, `ended_at`, `sequences` array with one entry containing one `sets` entry with `reps: 10`.
- [x] Pass <!-- 2026-06-04 -->

### UAT-API-004: GET /workouts/ returns only the authenticated user's workouts

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `GET /workouts/`
- **Description**: Verify the list endpoint is scoped to the authenticated user — another user's workouts are not returned.
- **Steps**:
  1. Run the script below from `backend/`. It creates two users, each posts a workout, then verifies each user only sees their own.
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx, uuid
from app.main import app

EXERCISE_ID = '0b3178cf-bf89-45a3-bfb0-27310ef6ef38'

async def register_and_login(c, email, password):
    await c.post('/auth/register', json={'email': email, 'password': password})
    login = await c.post('/auth/jwt/login', data={'username': email, 'password': password})
    assert login.status_code == 200, f'login failed: {login.text}'
    return {'Authorization': f'Bearer {login.json()[\"access_token\"]}'}

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        tag = uuid.uuid4().hex[:8]
        h1 = await register_and_login(c, f'user1-{tag}@test.com', 'TestPass123!')
        h2 = await register_and_login(c, f'user2-{tag}@test.com', 'TestPass123!')
        payload = {'started_at': '2026-01-01T09:00:00Z', 'sequences': []}
        r1 = await c.post('/workouts/', json=payload, headers=h1)
        r2 = await c.post('/workouts/', json=payload, headers=h2)
        assert r1.status_code == 201
        assert r2.status_code == 201
        wid1 = r1.json()['id']
        wid2 = r2.json()['id']
        list1 = await c.get('/workouts/', headers=h1)
        list2 = await c.get('/workouts/', headers=h2)
        assert list1.status_code == 200
        assert list2.status_code == 200
        ids1 = [w['id'] for w in list1.json()]
        ids2 = [w['id'] for w in list2.json()]
        assert wid1 in ids1, 'user1 workout missing from user1 list'
        assert wid2 not in ids1, 'user2 workout leaked into user1 list'
        assert wid2 in ids2, 'user2 workout missing from user2 list'
        assert wid1 not in ids2, 'user1 workout leaked into user2 list'
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `PASS`. Each user's list contains only their own workout ID.
- [x] Pass <!-- 2026-06-04 -->

### UAT-API-005: GET /workouts/{id} for another user's workout returns 404

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `GET /workouts/{workout_id}`
- **Description**: Verify that fetching a workout belonging to a different user returns 404 (no information leak).
- **Steps**:
  1. Run the script below from `backend/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx, uuid
from app.main import app

async def register_and_login(c, email, password):
    await c.post('/auth/register', json={'email': email, 'password': password})
    login = await c.post('/auth/jwt/login', data={'username': email, 'password': password})
    return {'Authorization': f'Bearer {login.json()[\"access_token\"]}'}

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        tag = uuid.uuid4().hex[:8]
        h1 = await register_and_login(c, f'owner-{tag}@test.com', 'TestPass123!')
        h2 = await register_and_login(c, f'other-{tag}@test.com', 'TestPass123!')
        r = await c.post('/workouts/', json={'started_at': '2026-01-01T09:00:00Z', 'sequences': []}, headers=h1)
        assert r.status_code == 201
        wid = r.json()['id']
        fetch = await c.get(f'/workouts/{wid}', headers=h2)
        print('status:', fetch.status_code)
        assert fetch.status_code == 404, f'expected 404, got {fetch.status_code}: {fetch.text}'
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `status: 404` then `PASS`.
- [x] Pass <!-- 2026-06-04 -->

### UAT-API-006: PUT /workouts/{id} replaces sequences and returns 200

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PUT /workouts/{workout_id}`
- **Description**: Verify that PUT replaces the full workout (sequences and sets atomically) and returns 200 with updated `WorkoutRead`.
- **Steps**:
  1. Run the script below from `backend/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx, uuid
from app.main import app

EXERCISE_ID = '0b3178cf-bf89-45a3-bfb0-27310ef6ef38'

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        tag = uuid.uuid4().hex[:8]
        await c.post('/auth/register', json={'email': f'uat008put-{tag}@test.com', 'password': 'TestPass123!'})
        login = await c.post('/auth/jwt/login', data={'username': f'uat008put-{tag}@test.com', 'password': 'TestPass123!'})
        headers = {'Authorization': f'Bearer {login.json()[\"access_token\"]}'}
        create_payload = {
            'started_at': '2026-01-01T10:00:00Z',
            'sequences': [{'phase': 'warmup', 'position': 0, 'sets': []}]
        }
        r = await c.post('/workouts/', json=create_payload, headers=headers)
        assert r.status_code == 201
        wid = r.json()['id']
        assert len(r.json()['sequences']) == 1
        assert r.json()['sequences'][0]['phase'] == 'warmup'
        update_payload = {
            'started_at': '2026-01-01T10:00:00Z',
            'ended_at': '2026-01-01T11:30:00Z',
            'sequences': [
                {'phase': 'main', 'position': 0, 'sets': [{'exercise_id': EXERCISE_ID, 'set_type': 'STRENGTH', 'position': 0, 'reps': 5, 'weight_kg': 100.0}]},
                {'phase': 'cooldown', 'position': 1, 'sets': []}
            ]
        }
        r2 = await c.put(f'/workouts/{wid}', json=update_payload, headers=headers)
        print('status:', r2.status_code)
        assert r2.status_code == 200, f'expected 200, got {r2.status_code}: {r2.text}'
        body = r2.json()
        phases = [s['phase'] for s in body['sequences']]
        assert 'warmup' not in phases, 'old warmup sequence not replaced'
        assert 'main' in phases, 'new main sequence missing'
        assert 'cooldown' in phases, 'new cooldown sequence missing'
        assert body['ended_at'] is not None
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `status: 200` then `PASS`. Response body has `sequences` containing `main` and `cooldown` phases but not the original `warmup`.
- [x] Pass <!-- 2026-06-04 -->

### UAT-API-007: DELETE /workouts/{id} returns 204

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `DELETE /workouts/{workout_id}`
- **Description**: Verify that DELETE returns 204 and the workout is no longer accessible.
- **Steps**:
  1. Run the script below from `backend/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio, httpx, uuid
from app.main import app

async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
        tag = uuid.uuid4().hex[:8]
        await c.post('/auth/register', json={'email': f'uat008del-{tag}@test.com', 'password': 'TestPass123!'})
        login = await c.post('/auth/jwt/login', data={'username': f'uat008del-{tag}@test.com', 'password': 'TestPass123!'})
        headers = {'Authorization': f'Bearer {login.json()[\"access_token\"]}'}
        r = await c.post('/workouts/', json={'started_at': '2026-01-01T10:00:00Z', 'sequences': []}, headers=headers)
        assert r.status_code == 201
        wid = r.json()['id']
        delete_r = await c.delete(f'/workouts/{wid}', headers=headers)
        print('status:', delete_r.status_code)
        assert delete_r.status_code == 204, f'expected 204, got {delete_r.status_code}: {delete_r.text}'
        get_r = await c.get(f'/workouts/{wid}', headers=headers)
        assert get_r.status_code == 404, f'expected 404 after delete, got {get_r.status_code}'
        print('PASS')

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0. Prints `status: 204` then `PASS`. Subsequent GET returns 404.
- [x] Pass <!-- 2026-06-04 -->
