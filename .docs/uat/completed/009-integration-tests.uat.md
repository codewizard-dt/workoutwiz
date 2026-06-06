# UAT: Integration Tests for All Routes

> **Source task**: [`.docs/tasks/009-integration-tests.md`](../tasks/009-integration-tests.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] PostgreSQL running on localhost:5432; databases `workoutwiz` and `workoutwiz_test` exist
- [ ] Alembic migrations applied to dev DB (`cd backend && .venv/bin/alembic upgrade head`)
- [ ] `backend/.venv` exists with all dependencies installed (including `pytest`, `pytest-asyncio`, `httpx`)
- [ ] Working directory for test commands: `backend/`

---

## File Existence Tests

### UAT-FILE-001: conftest.py exists with session-scoped migration fixture

**Command**:
```bash
cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && \
  backend/.venv/bin/python -c "
import ast, pathlib
src = pathlib.Path('tests/conftest.py').read_text()
tree = ast.parse(src)
fixtures = [n.name for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]
assert 'apply_migrations' in fixtures, 'apply_migrations fixture missing'
# Verify session scope
for n in ast.walk(tree):
    if isinstance(n, ast.AsyncFunctionDef) and n.name == 'apply_migrations':
        for dec in n.decorator_list:
            dec_str = ast.unparse(dec)
            if 'session' in dec_str:
                print('PASS: apply_migrations has session scope')
                break
"
```

**Expected**: Prints `PASS: apply_migrations has session scope`

- [x] PASS

---

### UAT-FILE-002: test_auth.py, test_exercises.py, and test_workouts.py all exist

**Command**:
```bash
cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && \
  backend/.venv/bin/python -c "
import pathlib
for f in ['tests/test_auth.py', 'tests/test_exercises.py', 'tests/test_workouts.py']:
    assert pathlib.Path(f).exists(), f'{f} missing'
    print(f'PASS: {f} exists')
"
```

**Expected**: Three `PASS` lines, one per file.

- [x] PASS

---

### UAT-FILE-003: register_and_login helper is defined in test_auth.py

**Command**:
```bash
cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && \
  backend/.venv/bin/python -c "
import ast, pathlib
src = pathlib.Path('tests/test_auth.py').read_text()
tree = ast.parse(src)
names = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
assert 'register_and_login' in names, 'register_and_login not found'
print('PASS: register_and_login helper defined')
"
```

**Expected**: `PASS: register_and_login helper defined`

- [ ] PASS

---

## Full Test Suite

### UAT-SUITE-001: pytest tests/ -v exits code 0 with at least 19 tests passing

This is the primary acceptance test. Run from `backend/` using the venv pytest.

**Command**:
```bash
cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && \
  .venv/bin/pytest tests/ -v --tb=short
```

**Expected**:
- Exit code 0
- Output line matching `19 passed` (or more)
- All of the following test names appear and show `PASSED`:
  - `tests/test_auth.py::test_register_success`
  - `tests/test_auth.py::test_register_duplicate_email`
  - `tests/test_auth.py::test_login_success`
  - `tests/test_auth.py::test_login_wrong_password`
  - `tests/test_auth.py::test_get_me_authenticated`
  - `tests/test_auth.py::test_get_me_unauthenticated`
  - `tests/test_exercises.py::test_list_all_exercises`
  - `tests/test_exercises.py::test_filter_by_name`
  - `tests/test_exercises.py::test_filter_by_muscle_group`
  - `tests/test_exercises.py::test_filter_by_equipment`
  - `tests/test_exercises.py::test_filter_by_priority_tier`
  - `tests/test_exercises.py::test_invalid_priority_tier`
  - `tests/test_workouts.py::test_list_workouts_unauthenticated`
  - `tests/test_workouts.py::test_create_workout`
  - `tests/test_workouts.py::test_list_workouts_isolation`
  - `tests/test_workouts.py::test_get_workout`
  - `tests/test_workouts.py::test_get_other_users_workout_returns_404`
  - `tests/test_workouts.py::test_update_workout`
  - `tests/test_workouts.py::test_delete_workout`

- [x] PASS

---

## Coverage Summary

| Area | Tests | Criteria |
|------|-------|----------|
| Auth | 6 | register ok/dup, login ok/wrong-pw, /me authed/unauthed |
| Exercises | 6 | list all, filter name/muscle/equipment/tier, invalid tier 422 |
| Workouts | 7 | unauth 401, create, isolation, get, cross-user 404, update, delete |
| **Total** | **19** | All must pass |
