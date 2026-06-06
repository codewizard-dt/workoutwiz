# UAT: Annotate ExerciseRead Schema with OpenAPI Field Metadata

> **Source task**: [`.docs/tasks/037-annotate-schemas-exercise.md`](../tasks/037-annotate-schemas-exercise.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend dependencies installed (`pip install -e .` or `poetry install` from `backend/`)
- [ ] Backend server running on `http://localhost:8000` (`uvicorn app.main:app --reload` from `backend/`)
- [ ] Database is up and exercises seed migration has been applied

---

## API Tests

### UAT-API-001: Schema JSON schema has `description` on every property

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `ExerciseRead.model_json_schema()` includes a `description` key for every one of the 13 annotated properties. This is the primary acceptance criterion from the task.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "import json; from app.schemas.exercise import ExerciseRead; s = ExerciseRead.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'description' not in v]; print('Missing descriptions:', missing or 'NONE — all fields annotated'); print('Property count:', len(props))"
  ```
- **Expected Result**: Output contains `Missing descriptions: NONE — all fields annotated` and `Property count: 13`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: ExerciseRead imports `Field` from pydantic

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `Field` is imported from `pydantic` in `schemas/exercise.py` and that the import itself is valid (no syntax errors).
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.exercise import ExerciseRead; import pydantic; f = ExerciseRead.model_fields; print('Field count:', len(f)); print('All have metadata:', all(hasattr(v, 'description') for v in f.values()))"
  ```
- **Expected Result**: Output contains `Field count: 13` and `All have metadata: True`. No `ImportError` or `SyntaxError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: ExerciseRead JSON schema has `examples` on every property

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that every property in the JSON schema produced by `ExerciseRead.model_json_schema()` has an `examples` key (Pydantic v2 uses `examples` list, not singular `example`).
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "import json; from app.schemas.exercise import ExerciseRead; s = ExerciseRead.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'examples' not in v]; print('Missing examples:', missing or 'NONE — all fields have examples')"
  ```
- **Expected Result**: Output contains `Missing examples: NONE — all fields have examples`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: GET /exercises returns 200 with valid ExerciseRead-shaped objects

- **Endpoint**: `GET /exercises`
- **Description**: Verify the exercises list endpoint still works correctly after the schema annotation change — the change is additive and must not break the existing response shape.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises' | jq '{count: length, first: .[0] | {id, name, category, muscle_groups, equipment_required, movement_patterns, is_reps, is_duration, supports_weight, is_bilateral, bilateral_pair_id, priority_tier, description}}'
  ```
- **Expected Result**: `200 OK` (implicit — jq output is valid). The `first` object contains all 13 fields: `id` (UUID string), `name` (string), `category` (string), `muscle_groups` (array), `equipment_required` (array), `movement_patterns` (array), `is_reps` (bool), `is_duration` (bool), `supports_weight` (bool), `is_bilateral` (bool), `bilateral_pair_id` (UUID string or null), `priority_tier` (integer), `description` (string or null). `count` is greater than 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-005: GET /exercises?name= filters by name (case-insensitive)

- **Endpoint**: `GET /exercises?name=squat`
- **Description**: Verify the name filter still functions correctly after the schema change (regression guard).
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises?name=squat' | jq '[.[].name]'
  ```
- **Expected Result**: `200 OK`. Response is a JSON array of exercise objects where each `name` value contains "squat" (case-insensitive). Array is non-empty.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: GET /exercises?priority_tier=2 returns only tier-2 exercises

- **Endpoint**: `GET /exercises?priority_tier=2`
- **Description**: Verify priority_tier filter works correctly after schema change (regression guard). Note: all seeded exercises have priority_tier=2, so this is the verifiable case.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises/?priority_tier=2' | jq '[.[].priority_tier] | unique'
  ```
- **Expected Result**: `200 OK`. Response array contains only objects with `priority_tier` equal to `2`. The jq output is `[2]`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: ExerciseRead `model_config` is unchanged

- **Scenario**: The `model_config = {"from_attributes": True}` setting must survive the annotation changes. If it were removed, ORM objects could not be serialized.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.exercise import ExerciseRead; cfg = ExerciseRead.model_config; print('from_attributes:', cfg.get('from_attributes')); assert cfg.get('from_attributes') is True, 'FAIL: from_attributes missing or False'"
  ```
- **Expected Result**: Output contains `from_attributes: True` with no `AssertionError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: OpenAPI `/openapi.json` includes descriptions in exercise schema

- **Endpoint**: `GET /openapi.json`
- **Description**: Verify the live OpenAPI spec (served by FastAPI) includes `description` fields for exercise properties. This confirms end-to-end that Swagger UI will show rich annotations.
- **Steps**:
  1. Ensure the backend server is running
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.components.schemas.ExerciseRead.properties | to_entries | map({key: .key, has_description: (.value | has("description"))}) | map(select(.has_description == false))'
  ```
- **Expected Result**: `200 OK`. The jq output is `[]` (empty array) — meaning every property in the `ExerciseRead` component schema has a `description` field.
- [x] Pass <!-- 2026-06-06 -->
