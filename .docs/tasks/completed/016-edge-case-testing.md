# 016 — Edge Case Testing (Missing Data, Invalid IDs, Auth Token Expiry)

> **Depends on**: [014-port-react-components](014-port-react-components.md)
> **Blocks**: none
> **Parallel-safe with**: [015-e2e-tests](015-e2e-tests.md), [017-performance-baseline](017-performance-baseline.md), [018-production-readme](018-production-readme.md)

## Objective

Extend the pytest integration test suite with edge case scenarios that verify the backend handles invalid inputs, missing resources, expired tokens, and concurrent requests without panicking.

## Approach

- Add a new `backend/tests/test_edge_cases.py` file
- All tests use the existing conftest.py fixtures (real DB, httpx client)
- Cover 4 categories: missing data, invalid IDs, auth edge cases, concurrent requests

## Steps

### 1. Missing data and invalid input tests  <!-- agent: general-purpose -->

Add to `backend/tests/test_edge_cases.py`:

```python
import pytest
import uuid
from httpx import AsyncClient

# Missing required fields
async def test_create_workout_missing_started_at(client: AsyncClient, ...):
    # POST /workouts/ with empty body → 422

# Invalid UUID in path
async def test_get_workout_invalid_uuid(client: AsyncClient, ...):
    # GET /workouts/not-a-uuid → 422

# Valid UUID but not found
async def test_get_workout_nonexistent_id(client: AsyncClient, ...):
    # GET /workouts/<valid-uuid-not-in-db> → 404

# Invalid priority_tier value
async def test_exercises_invalid_priority_tier(client: AsyncClient):
    # GET /exercises/?priority_tier=99 → 422

# Invalid set_type value
async def test_create_workout_invalid_set_type(client: AsyncClient, ...):
    # POST /workouts/ with set_type="INVALID" → 422
```

- [x] 5 missing-data/invalid-input tests added <!-- Completed: 2026-06-04 -->

---

### 2. Auth edge case tests  <!-- agent: general-purpose -->

Add to `backend/tests/test_edge_cases.py`:

```python
# Malformed bearer token
async def test_malformed_token(client: AsyncClient):
    # GET /auth/me with Authorization: Bearer garbage → 401

# Expired token (use a pre-generated expired JWT)
async def test_expired_token(client: AsyncClient):
    # Create a token with lifetime_seconds=1, wait, then use it → 401
    # Use JWTStrategy directly to generate an expired token

# Wrong credentials
async def test_login_wrong_password(client: AsyncClient):
    # Register user, try login with wrong password → 400

# Accessing another user's workout
async def test_cross_user_workout_access(client: AsyncClient):
    # User A creates workout; User B tries GET /workouts/<A's id> → 404
```

- [x] 4 auth edge case tests added <!-- Completed: 2026-06-04 -->

---

### 3. Concurrent request tests  <!-- agent: general-purpose -->

Add to `backend/tests/test_edge_cases.py`:

```python
import asyncio

# Concurrent workout creation
async def test_concurrent_workout_creation(client: AsyncClient, ...):
    # Create 5 workouts concurrently with asyncio.gather
    # All should succeed and be distinct (no ID collision)

# Concurrent exercise queries
async def test_concurrent_exercise_queries(client: AsyncClient):
    # 10 concurrent GET /exercises/ → all return 200 with 50 results
```

- [x] 2 concurrent request tests added using `asyncio.gather` <!-- Completed: 2026-06-04 -->

---

### 4. Run extended test suite  <!-- agent: general-purpose -->

From `backend/`:
```bash
.venv/bin/pytest tests/ -v --tb=short
```

Original 19 tests + 11 new edge case tests = at least 30 tests passing.

- [x] `pytest tests/ -v` exits with code 0 <!-- Completed: 2026-06-04 -->
- [x] At least 30 tests passing total <!-- Completed: 2026-06-04 -->

## Acceptance Criteria

- [x] `backend/tests/test_edge_cases.py` created with 11 new tests <!-- Completed: 2026-06-04 -->
- [x] Missing data → 422 Unprocessable Entity <!-- Completed: 2026-06-04 -->
- [x] Invalid UUIDs in path → 422 <!-- Completed: 2026-06-04 -->
- [x] Valid-but-missing UUID → 404 <!-- Completed: 2026-06-04 -->
- [x] Malformed/expired JWT → 401 <!-- Completed: 2026-06-04 -->
- [x] Cross-user access → 404 (no information leak) <!-- Completed: 2026-06-04 -->
- [x] 5 concurrent workout creates succeed without ID collisions <!-- Completed: 2026-06-04 -->
- [x] All tests pass with `pytest tests/ -v` <!-- Completed: 2026-06-04 -->

---
**UAT**: [`.docs/uat/016-edge-case-testing.uat.md`](../uat/016-edge-case-testing.uat.md)
