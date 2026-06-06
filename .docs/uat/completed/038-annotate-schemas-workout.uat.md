# UAT: Annotate Workout Schemas with OpenAPI Field Metadata

> **Source task**: [`.docs/tasks/038-annotate-schemas-workout.md`](../tasks/038-annotate-schemas-workout.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend dependencies installed (`pip install -e .` or `poetry install` from `backend/`)
- [ ] Backend server running on `http://localhost:8000` (`uvicorn app.main:app --reload` from `backend/`)
- [ ] A valid JWT bearer token stored in `$UAT_AUTH_TOKEN` (obtain via `POST /auth/jwt/login`)
- [ ] Database is up and migrations have been applied

---

## API Tests

### UAT-API-001: WorkoutRead JSON schema has `description` on every property (recursive)

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `WorkoutRead.model_json_schema()` includes a `description` key for every property recursively across all six schema classes. This is the primary acceptance criterion from the task.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "import json; from app.schemas.workout import WorkoutRead; s = WorkoutRead.model_json_schema(); all_defs = {**s.get('properties', {}), **{k: v for d in s.get('\$defs', {}).values() for k, v in d.get('properties', {}).items()}}; missing = [k for k, v in all_defs.items() if 'description' not in v]; print('Missing descriptions:', missing or 'NONE'); print('Top-level props:', list(s.get('properties', {}).keys()))"
  ```
- **Expected Result**: Output contains `Missing descriptions: NONE`. Top-level props includes `id`, `user_id`, `started_at`, `ended_at`, `sequences`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: All six schema classes import cleanly and have `Field` annotations

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `Field` is imported from `pydantic` in `schemas/workout.py` and that all six classes load without `ImportError` or `SyntaxError`.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.workout import WorkoutSetCreate, WorkoutSequenceCreate, WorkoutCreate, WorkoutSetRead, WorkoutSequenceRead, WorkoutRead; counts = {c.__name__: len(c.model_fields) for c in [WorkoutSetCreate, WorkoutSequenceCreate, WorkoutCreate, WorkoutSetRead, WorkoutSequenceRead, WorkoutRead]}; print(counts)"
  ```
- **Expected Result**: Output is a dict with all six class names and their field counts: `WorkoutSetCreate` has 9, `WorkoutSequenceCreate` has 3, `WorkoutCreate` has 3, `WorkoutSetRead` has 11 (9 inherited + 2 new), `WorkoutSequenceRead` has 5, `WorkoutRead` has 5. No exceptions raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: WorkoutSetCreate defaults are preserved

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that annotating fields with `Field(default=..., description=..., examples=[...])` preserved the existing defaults: `position=0`, `reps=None`, `weight_kg=None`, `duration_s=None`, `speed=None`, `distance=None`, `calories=None`.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.workout import WorkoutSetCreate; import uuid; s = WorkoutSetCreate(exercise_id=uuid.uuid4(), set_type='STRENGTH'); print('position:', s.position, '| reps:', s.reps, '| weight_kg:', s.weight_kg, '| duration_s:', s.duration_s, '| speed:', s.speed, '| distance:', s.distance, '| calories:', s.calories)"
  ```
- **Expected Result**: Output is `position: 0 | reps: None | weight_kg: None | duration_s: None | speed: None | distance: None | calories: None`. No `ValidationError` is raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: WorkoutSequenceCreate defaults are preserved

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `position=0` and `sets=[]` defaults survive the annotation change.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.workout import WorkoutSequenceCreate; s = WorkoutSequenceCreate(phase='main'); print('position:', s.position, '| sets:', s.sets)"
  ```
- **Expected Result**: Output is `position: 0 | sets: []`. No `ValidationError` is raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-005: POST /workouts returns 201 with WorkoutRead-shaped body

- **Endpoint**: `POST /workouts`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the create workout endpoint still returns a correctly structured `WorkoutRead` response after the schema annotation change — the change is additive and must not break serialization.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/workouts/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"started_at":"2026-06-05T09:00:00Z","ended_at":null,"sequences":[]}' | jq '{id, user_id, started_at, ended_at, sequences_count: (.sequences | length)}'
  ```
- **Expected Result**: `201 Created`. Response body contains `id` (UUID string), `user_id` (UUID string), `started_at` (`"2026-06-05T09:00:00Z"` or equivalent ISO 8601), `ended_at` (`null`), `sequences_count` (`0`).
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: POST /workouts with nested sequences and sets returns full WorkoutRead

- **Endpoint**: `POST /workouts`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that a workout with a sequence and set round-trips correctly through the annotated schemas — serialization of nested `WorkoutSequenceRead` and `WorkoutSetRead` objects works.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Obtain a valid exercise UUID from `GET /exercises` and substitute it for `<exercise-uuid>` below
  3. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/workouts/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"started_at":"2026-06-05T09:00:00Z","ended_at":"2026-06-05T10:00:00Z","sequences":[{"phase":"main","position":0,"sets":[{"exercise_id":"<exercise-uuid>","set_type":"STRENGTH","position":0,"reps":10,"weight_kg":100.0}]}]}' | jq '{id, seq_count: (.sequences | length), set_count: (.sequences[0].sets | length), set_keys: (.sequences[0].sets[0] | keys)}'
  ```
- **Expected Result**: `201 Created`. `seq_count` is `1`, `set_count` is `1`, `set_keys` includes `id`, `sequence_id`, `exercise_id`, `set_type`, `position`, `reps`, `weight_kg`, `duration_s`, `speed`, `distance`, `calories`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-007: GET /workouts returns list with annotated WorkoutRead objects

- **Endpoint**: `GET /workouts`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the list endpoint returns the correctly shaped `WorkoutRead` objects after schema annotation (data exists from UAT-API-005).
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/workouts/' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{count: length, first_keys: (.[0] | keys)}'
  ```
- **Expected Result**: `200 OK`. `count` is at least 1. `first_keys` includes `id`, `user_id`, `started_at`, `ended_at`, `sequences`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-008: OpenAPI `/openapi.json` includes descriptions in all workout component schemas

- **Endpoint**: `GET /openapi.json`
- **Description**: Verify the live OpenAPI spec includes `description` fields for properties on all workout schema components (`WorkoutRead`, `WorkoutSequenceRead`, `WorkoutSetRead`, `WorkoutCreate`, `WorkoutSequenceCreate`, `WorkoutSetCreate`). This confirms Swagger UI will display annotations end-to-end.
- **Steps**:
  1. Ensure the backend server is running
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '[.components.schemas | to_entries[] | select(.key | test("Workout")) | {schema: .key, missing_desc: [.value.properties // {} | to_entries[] | select(.value | has("description") | not) | .key]}] | map(select(.missing_desc | length > 0))'
  ```
- **Expected Result**: `200 OK`. The jq output is `[]` (empty array) — every property on every workout-related component schema has a `description` field.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: WorkoutCreate with only `started_at` is valid (all other fields optional)

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `ended_at` and `sequences` default correctly when omitted — `ended_at=None`, `sequences=[]`.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.workout import WorkoutCreate; from datetime import datetime, timezone; w = WorkoutCreate(started_at=datetime(2026, 6, 5, 9, 0, tzinfo=timezone.utc)); print('ended_at:', w.ended_at, '| sequences:', w.sequences)"
  ```
- **Expected Result**: Output is `ended_at: None | sequences: []`. No `ValidationError` is raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: model_config `from_attributes=True` is preserved on all Read classes

- **Endpoint**: N/A (Python import verification)
- **Description**: The `model_config = {"from_attributes": True}` setting on `WorkoutRead`, `WorkoutSequenceRead`, and `WorkoutSetRead` must survive annotation changes. Without it, ORM objects cannot be serialized.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.workout import WorkoutSetRead, WorkoutSequenceRead, WorkoutRead; results = {c.__name__: c.model_config.get('from_attributes') for c in [WorkoutSetRead, WorkoutSequenceRead, WorkoutRead]}; print(results); assert all(results.values()), 'FAIL: from_attributes missing on one or more Read classes'"
  ```
- **Expected Result**: Output is `{'WorkoutSetRead': True, 'WorkoutSequenceRead': True, 'WorkoutRead': True}` with no `AssertionError`.
- [x] Pass <!-- 2026-06-06 -->
