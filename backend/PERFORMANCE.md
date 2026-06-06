# Performance Baseline

Measured on: 2026-06-04 (local dev, Docker PostgreSQL 16, 50 exercises)

## Endpoint Response Times (20 iterations each)

| Endpoint | Avg (ms) | P95 (ms) | Target |
|----------|----------|----------|--------|
| GET /exercises/ | 2.0 | 7.5 | < 50ms |
| GET /exercises/?name=squat | 1.4 | 1.9 | < 50ms |
| GET /exercises/?muscle_groups=chest | 1.6 | 2.5 | < 50ms |
| GET /workouts/ | 1.8 | 3.7 | < 100ms |

All endpoints are well within targets (20–50x headroom).

## Index Notes

- `ix_exercises_muscle_groups_gin` (GIN) — ARRAY overlap queries use bitmap scan when forced; planner chooses seq scan on 50-row table (correct optimizer behaviour)
- `ix_exercises_equipment_required_gin` (GIN) — same
- `ix_exercises_name` (B-tree) — name ILIKE queries use seq scan (ILIKE doesn't benefit from B-tree without `pg_trgm`)

## GIN Index Verification

With `SET enable_seqscan = off`:

```
Bitmap Heap Scan on exercises
  Recheck Cond: (muscle_groups && '{chest}'::character varying[])
  ->  Bitmap Index Scan on ix_exercises_muscle_groups_gin
        Index Cond: (muscle_groups && '{chest}'::character varying[])
```

The planner selects sequential scan on the 50-row dev dataset (fastest for small tables). GIN index will kick in automatically as data grows.
