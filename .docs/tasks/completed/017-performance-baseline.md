# 017 — Performance Baseline (API Response Times, Query Optimization)

> **Depends on**: [014-port-react-components](014-port-react-components.md)
> **Blocks**: none
> **Parallel-safe with**: [015-e2e-tests](015-e2e-tests.md), [016-edge-case-testing](016-edge-case-testing.md), [018-production-readme](018-production-readme.md)

## Objective

Measure API response times for all key endpoints, identify any slow queries with `EXPLAIN ANALYZE`, and add a JSONB index on `movement_patterns` if needed. Record the baseline numbers in a `backend/PERFORMANCE.md` document.

## Approach

- Use Python `timeit` / `asyncio` + httpx for response time measurement (no external tools needed)
- EXPLAIN ANALYZE via SQLAlchemy for query inspection
- Add PostgreSQL index on `exercises.name` (already present) and verify ARRAY overlap queries use GIN index
- Target baselines: `GET /exercises/` < 50ms, `GET /workouts/` < 100ms, `POST /workouts/` < 200ms

## Steps

### 1. Write performance measurement script  <!-- agent: general-purpose -->

Create `backend/scripts/perf_baseline.py`:

```python
"""
Performance baseline measurement. Run from backend/ with server running:
  .venv/bin/python scripts/perf_baseline.py
"""
import asyncio
import time
import httpx

BASE_URL = "http://localhost:8000"
ITERATIONS = 20


async def measure(client: httpx.AsyncClient, method: str, path: str, **kwargs) -> float:
    times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        response = await client.request(method, f"{BASE_URL}{path}", **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert response.status_code < 500, f"Server error on {path}: {response.text}"
    avg = sum(times) / len(times)
    p95 = sorted(times)[int(ITERATIONS * 0.95)]
    return avg, p95


async def main():
    # Register and login to get a token
    async with httpx.AsyncClient() as client:
        email = f"perf_{int(time.time())}@test.com"
        await client.post(f"{BASE_URL}/auth/register", json={"email": email, "password": "perf1234!"})
        form = {"username": email, "password": "perf1234!"}
        resp = await client.post(f"{BASE_URL}/auth/jwt/login", data=form)
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print(f"\n{'Endpoint':<40} {'Avg (ms)':>10} {'P95 (ms)':>10}")
        print("-" * 62)

        for label, method, path, kw in [
            ("GET /exercises/", "GET", "/exercises/", {}),
            ("GET /exercises/?name=squat", "GET", "/exercises/?name=squat", {}),
            ("GET /exercises/?muscle_groups=chest", "GET", "/exercises/?muscle_groups=chest", {}),
            ("GET /workouts/", "GET", "/workouts/", {"headers": headers}),
        ]:
            avg, p95 = await measure(client, method, path, **kw)
            print(f"{label:<40} {avg:>10.1f} {p95:>10.1f}")

if __name__ == "__main__":
    asyncio.run(main())
```

- [x] `backend/scripts/perf_baseline.py` created <!-- Completed: 2026-06-04 -->
- [x] Script runs without errors against a live server <!-- Completed: 2026-06-04 -->

---

### 2. Add GIN index for ARRAY overlap queries  <!-- agent: general-purpose -->

The `muscle_groups` and `equipment_required` ARRAY overlap queries benefit from a GIN index. Generate an Alembic migration:

```bash
cd backend && .venv/bin/alembic revision -m "add gin indexes for exercise arrays"
```

In the migration:
```python
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from alembic import op

def upgrade():
    op.execute("CREATE INDEX IF NOT EXISTS ix_exercises_muscle_groups_gin ON exercises USING GIN (muscle_groups)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_exercises_equipment_required_gin ON exercises USING GIN (equipment_required)")

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_exercises_muscle_groups_gin")
    op.execute("DROP INDEX IF EXISTS ix_exercises_equipment_required_gin")
```

Apply: `alembic upgrade head`

- [x] GIN index migration created in `backend/migrations/versions/` <!-- Completed: 2026-06-04 -->
- [x] `alembic upgrade head` succeeds <!-- Completed: 2026-06-04 -->
- [x] `EXPLAIN ANALYZE SELECT * FROM exercises WHERE muscle_groups && ARRAY['chest']` shows "Bitmap Index Scan" (not Seq Scan) <!-- Completed: 2026-06-04 - verified with enable_seqscan=off -->

---

### 3. Record baseline in PERFORMANCE.md  <!-- agent: general-purpose -->

Run the perf script and capture output. Create `backend/PERFORMANCE.md`:

```markdown
# Performance Baseline

Measured on: 2026-06-04 (local dev, Homebrew PostgreSQL 16, 50 exercises)

## Endpoint Response Times (20 iterations each)

| Endpoint | Avg (ms) | P95 (ms) | Target |
|----------|----------|----------|--------|
| GET /exercises/ | X.X | X.X | < 50ms |
| GET /exercises/?name=squat | X.X | X.X | < 50ms |
| GET /exercises/?muscle_groups=chest | X.X | X.X | < 50ms |
| GET /workouts/ | X.X | X.X | < 100ms |

## Index Notes

- `ix_exercises_muscle_groups_gin` (GIN) — ARRAY overlap queries use bitmap scan
- `ix_exercises_equipment_required_gin` (GIN) — same
- `ix_exercises_name` (B-tree) — name ILIKE queries use seq scan (ILIKE doesn't benefit from B-tree without `pg_trgm`)
```

Fill in actual numbers from the script output.

- [x] `backend/PERFORMANCE.md` created with measured baselines <!-- Completed: 2026-06-04 -->
- [x] All targets met (< 50ms avg for exercises, < 100ms for workouts) <!-- Completed: 2026-06-04 -->

## Acceptance Criteria

- [x] `perf_baseline.py` script runs and prints avg/P95 for all endpoints <!-- Completed: 2026-06-04 -->
- [x] GIN indexes added for `muscle_groups` and `equipment_required` <!-- Completed: 2026-06-04 -->
- [x] `EXPLAIN ANALYZE` shows index use for ARRAY overlap queries <!-- Completed: 2026-06-04 -->
- [x] `backend/PERFORMANCE.md` documents actual measured response times <!-- Completed: 2026-06-04 -->
- [x] `GET /exercises/` avg response time < 50ms <!-- Completed: 2026-06-04 - actual: 2.0ms avg -->

---
**UAT**: [`.docs/uat/017-performance-baseline.uat.md`](../uat/017-performance-baseline.uat.md)
