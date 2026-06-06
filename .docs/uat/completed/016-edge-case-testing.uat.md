# UAT: Edge Case Testing (Missing Data, Invalid IDs, Auth Token Expiry)

> **Source task**: [`.docs/tasks/016-edge-case-testing.md`](../tasks/016-edge-case-testing.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] PostgreSQL running on localhost:5432; databases `workoutwiz` and `workoutwiz_test` exist
- [ ] Alembic migrations applied (`cd backend && .venv/bin/alembic upgrade head`)
- [ ] `backend/.venv` exists with all dependencies installed (including `pytest`, `pytest-asyncio`, `httpx`)
- [ ] Working directory for all commands below: `backend/` (i.e. `/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend`)

---

## File Existence Tests

### UAT-FILE-001: test_edge_cases.py exists

Verify the new test file was created at the required path.

**Command**:
```bash
python -c "import pathlib; p = pathlib.Path('tests/test_edge_cases.py'); assert p.exists(), 'FAIL: file missing'; print('PASS: tests/test_edge_cases.py exists')"
```

**Expected**: `PASS: tests/test_edge_cases.py exists`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-002: test_edge_cases.py contains exactly 11 test functions

Verify all 11 required tests are present by name.

**Command**:
```bash
python -c "
import ast, pathlib
src = pathlib.Path('tests/test_edge_cases.py').read_text()
tree = ast.parse(src)
tests = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')]
required = [
    'test_create_workout_missing_started_at',
    'test_get_workout_invalid_uuid',
    'test_get_workout_nonexistent_id',
    'test_exercises_invalid_priority_tier',
    'test_create_workout_invalid_set_type',
    'test_malformed_token',
    'test_expired_token',
    'test_login_wrong_password',
    'test_cross_user_workout_access',
    'test_concurrent_workout_creation',
    'test_concurrent_exercise_queries',
]
missing = [t for t in required if t not in tests]
assert not missing, f'FAIL: missing tests: {missing}'
print(f'PASS: all 11 required test functions found ({len(tests)} total)')
"
```

**Expected**: `PASS: all 11 required test functions found (11 total)`

- [x] Pass <!-- 2026-06-04 -->

---

## Full Test Suite

### UAT-SUITE-001: pytest tests/ -v exits code 0 with at least 30 tests passing

Run the full test suite (original 19 + 11 new edge case tests). This is the primary acceptance gate.

**Command**:
```bash
.venv/bin/pytest tests/ -v --tb=short
```

**Expected**:
- Exit code 0
- Output line matching `30 passed` (or more)
- All 11 new edge case tests appear and show `PASSED`:
  - `tests/test_edge_cases.py::test_create_workout_missing_started_at`
  - `tests/test_edge_cases.py::test_get_workout_invalid_uuid`
  - `tests/test_edge_cases.py::test_get_workout_nonexistent_id`
  - `tests/test_edge_cases.py::test_exercises_invalid_priority_tier`
  - `tests/test_edge_cases.py::test_create_workout_invalid_set_type`
  - `tests/test_edge_cases.py::test_malformed_token`
  - `tests/test_edge_cases.py::test_expired_token`
  - `tests/test_edge_cases.py::test_login_wrong_password`
  - `tests/test_edge_cases.py::test_cross_user_workout_access`
  - `tests/test_edge_cases.py::test_concurrent_workout_creation`
  - `tests/test_edge_cases.py::test_concurrent_exercise_queries`

- [x] Pass <!-- 2026-06-04 -->

---

## Edge Case Tests (Behavior Verification)

### UAT-EDGE-001: Missing required field → 422

Verify that `POST /workouts/` with an empty body returns 422 Unprocessable Entity (missing `started_at`).

**Scenario**: Send a POST to create a workout without the required `started_at` field.

**Verified by**: `test_create_workout_missing_started_at` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-002: Invalid UUID in path → 422

Verify that `GET /workouts/not-a-uuid` returns 422 Unprocessable Entity (FastAPI path validation rejects non-UUID string).

**Scenario**: Supply a non-UUID string as a path parameter where a UUID is required.

**Verified by**: `test_get_workout_invalid_uuid` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-003: Valid UUID but not found → 404

Verify that `GET /workouts/<valid-uuid-not-in-db>` returns 404 Not Found.

**Scenario**: Supply a syntactically valid UUID that does not correspond to any workout in the database.

**Verified by**: `test_get_workout_nonexistent_id` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-004: Invalid priority_tier query parameter → 422

Verify that `GET /exercises/?priority_tier=99` returns 422 Unprocessable Entity.

**Scenario**: Supply an out-of-range `priority_tier` value (valid range is 1–3; 99 is invalid).

**Verified by**: `test_exercises_invalid_priority_tier` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-005: Invalid set_type value → 422

Verify that creating a workout with `set_type="INVALID"` returns 422 Unprocessable Entity.

**Scenario**: Supply an invalid enum value for `set_type` (valid values: `STRENGTH`, `CARDIO`).

**Verified by**: `test_create_workout_invalid_set_type` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-006: Malformed bearer token → 401

Verify that `GET /auth/me` with `Authorization: Bearer garbage` returns 401 Unauthorized.

**Scenario**: Send a request with a syntactically invalid JWT token string.

**Verified by**: `test_malformed_token` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-007: Expired JWT token → 401

Verify that using an expired JWT token returns 401 Unauthorized.

**Scenario**: A token generated with `lifetime_seconds=1` is used after it has expired.

**Verified by**: `test_expired_token` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-008: Wrong login password → 400

Verify that logging in with an incorrect password returns 400 Bad Request.

**Scenario**: A registered user attempts login with the wrong password.

**Verified by**: `test_login_wrong_password` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-009: Cross-user workout access → 404 (no information leak)

Verify that User B cannot access User A's workout; the endpoint returns 404 (not 403) to avoid leaking resource existence.

**Scenario**: User A creates a workout; User B authenticates and attempts `GET /workouts/<user-A-workout-id>`.

**Verified by**: `test_cross_user_workout_access` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-010: Concurrent workout creation — no ID collisions

Verify that 5 concurrent `POST /workouts/` requests all succeed and produce distinct UUIDs.

**Scenario**: Use `asyncio.gather` to fire 5 simultaneous workout creation requests with the same authenticated user.

**Verified by**: `test_concurrent_workout_creation` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-011: Concurrent exercise queries — all succeed

Verify that 10 concurrent `GET /exercises/` requests all return 200 with all 50 exercises.

**Scenario**: Use `asyncio.gather` to fire 10 simultaneous read requests against the exercise listing endpoint.

**Verified by**: `test_concurrent_exercise_queries` in `tests/test_edge_cases.py`

- [x] Pass <!-- 2026-06-04 -->

---

## Coverage Summary

| Category | Test Functions | Acceptance Criteria |
|---|---|---|
| Missing data / invalid input | 5 | 422 on missing field, invalid UUID path, invalid priority_tier, invalid set_type; 404 on missing UUID |
| Auth edge cases | 4 | 401 on malformed token, 401 on expired token, 400 on wrong password, 404 on cross-user access |
| Concurrent requests | 2 | 5 concurrent creates succeed with distinct IDs; 10 concurrent reads all return 200 + 50 results |
| **Total** | **11** | All must pass (`pytest tests/ -v` exit code 0, ≥ 30 tests passing) |
