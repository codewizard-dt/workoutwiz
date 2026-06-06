# UAT: Persist audit_log entries to Postgres

> **Source task**: [`.docs/tasks/083-persist-audit-log-to-postgres.md`](../tasks/083-persist-audit-log-to-postgres.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend Postgres database is running and reachable
- [ ] `alembic upgrade head` has been applied — `audit_log` table exists
- [ ] Test dependencies installed: `cd backend && pip install -e ".[dev]"`
- [ ] `TEST_DATABASE_URL` env var resolves to a running test Postgres instance (set in `.env`)

---

## Unit / Integration Tests (pytest)

These tests exercise `persist_audit_log` and `AuditLogEntry.create` directly against the test DB via pytest-asyncio. Run them with:

```bash
cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_audit_persist.py -v
```

### UAT-TEST-001: All known fields are stored in typed columns; unknown keys go to extra JSONB

- **Description**: Verifies that a single entry with one unknown key (`exercise_count`) is persisted with all fixed fields in their typed columns and the overflow key in `extra`.
- **Steps**:
  1. Run the pytest command above
  2. Confirm `test_persist_audit_log_persists_entries` passes
- **Expected Result**: Test passes — `row.event == "router"`, `row.latency_ms == 42`, `row.tokens_in == 10`, `row.tokens_out == 5`, `row.model == "claude-3-5-haiku-20241022"`, `row.provider == "anthropic"`, `row.user_id == "u1"`, `row.extra == {"exercise_count": 3}`, `row.created_at is not None`
- [x] Pass <!-- 2026-06-06 -->

### UAT-TEST-002: Multiple entries in one call are all persisted

- **Description**: Verifies that passing multiple entries to `persist_audit_log` results in one row per entry.
- **Steps**:
  1. Run the pytest command above
  2. Confirm `test_persist_audit_log_multiple_entries` passes
- **Expected Result**: Test passes — all entries written, row count equals entry count
- [x] Pass <!-- 2026-06-06 -->

### UAT-TEST-003: No extra column set when all keys are known fields

- **Description**: Verifies `extra` is `None` when no overflow keys are present.
- **Steps**:
  1. Run the pytest command above
  2. Confirm `test_persist_audit_log_no_extra_when_all_known` passes
- **Expected Result**: Test passes — `row.extra is None`
- [x] Pass <!-- 2026-06-06 -->

### UAT-TEST-004: Empty entry list results in zero rows

- **Description**: Verifies that calling `persist_audit_log` with an empty list is a no-op.
- **Steps**:
  1. Run the pytest command above
  2. Confirm `test_persist_audit_log_empty_entries` passes
- **Expected Result**: Test passes — no rows inserted for that `session_id`
- [x] Pass <!-- 2026-06-06 -->

---

## Schema / Migration Tests

### UAT-SCHEMA-001: audit_log table exists with all required columns

- **Description**: Confirms the Alembic migration created the `audit_log` table with the correct column set, including `created_at` with a server default.
- **Steps**:
  1. Connect to the Postgres database and run:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "\d audit_log"
     ```
- **Expected Result**: Output lists all columns: `id` (uuid, PK), `session_id` (varchar, not null), `user_id` (varchar), `event` (varchar, not null), `model` (varchar), `provider` (varchar), `latency_ms` (integer), `tokens_in` (integer), `tokens_out` (integer), `route` (varchar), `confidence` (double precision), `node_name` (varchar), `source_type` (varchar), `source_id` (text), `extra` (jsonb), `created_at` (timestamptz, not null, has server default)
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCHEMA-002: Required indexes exist on session_id, user_id, and event

- **Description**: Confirms the three indexes required by the migration are present.
- **Steps**:
  1. Run:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "\di ix_audit_log_*"
     ```
- **Expected Result**: Output lists `ix_audit_log_session_id`, `ix_audit_log_user_id`, and `ix_audit_log_event`
- [x] Pass <!-- 2026-06-06 -->

---

## API Integration Tests

These tests confirm that the chat endpoint actually flushes audit entries to Postgres.

### UAT-API-001: POST /chat/ persists audit entries to Postgres after graph invocation

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /chat/`
- **Description**: Verifies that sending a chat message results in at least one `audit_log` row queryable from Postgres by the returned `session_id`.
- **Steps**:
  1. Register and log in to obtain a JWT (or use `$UAT_AUTH_TOKEN` if already set):
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && curl -sS -X POST 'http://localhost:8000/auth/register' -H 'Content-Type: application/json' -d '{"email":"uataudit001@example.com","password":"TestPass123!"}' && curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=uataudit001@example.com&password=TestPass123!' | jq '.access_token'
     ```
  2. Send a chat message (replace `<token>` with the access token from step 1):
     ```bash
     curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Give me a coaching tip for bench press"}' | jq '{session_id, route, audit_log_count: (.audit_log | length)}'
     ```
  3. Note the `session_id` from the response. Query Postgres for persisted rows:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "SELECT event, model, provider, latency_ms, created_at FROM audit_log WHERE session_id = '<session_id-from-step-2>' ORDER BY created_at;"
     ```
- **Expected Result**: Step 2 returns `200 OK` with `session_id`, `reply`, `route`, and `audit_log` array with at least one entry. Step 3 query returns at least one row with `event` set (e.g. `router`), `created_at` populated as a non-null timestamp.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

### UAT-API-002: created_at is set by the database on insert (not by the application)

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /chat/`
- **Description**: Verifies `created_at` is a real DB-generated timestamp (not null, not an application-supplied value).
- **Steps**:
  1. Using the `session_id` from UAT-API-001, run:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "SELECT created_at, (created_at IS NOT NULL) AS has_created_at FROM audit_log WHERE session_id = '<session_id-from-UAT-API-001>' LIMIT 1;"
     ```
- **Expected Result**: `has_created_at` is `t` (true); `created_at` is a valid timestamptz value
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

### UAT-API-003: In-memory audit_log in chat response matches Postgres rows

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /chat/`
- **Description**: Verifies the in-memory `audit_log` array returned in the API response has the same number of entries as the rows stored in Postgres for that session (Postgres is additive, not a replacement).
- **Steps**:
  1. Using the `session_id` from UAT-API-001, count rows in Postgres:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM audit_log WHERE session_id = '<session_id-from-UAT-API-001>';"
     ```
  2. Compare the count to the `audit_log` array length returned in step 2 of UAT-API-001.
- **Expected Result**: Postgres row count equals the `audit_log` array length from the API response (same number of entries persisted as returned in-memory)
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Unknown entry keys land in extra JSONB column, not typed columns

- **Description**: Confirms that keys not in the known-fields set are stored in `extra` and do not cause an error or silent data loss.
- **Steps**:
  1. Using the `session_id` from UAT-API-001, query `extra` for any rows that have it:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "SELECT event, extra FROM audit_log WHERE session_id = '<session_id-from-UAT-API-001>' AND extra IS NOT NULL;"
     ```
  2. Also confirm rows with only known fields have `extra IS NULL`:
     ```bash
     set -a && source /Users/davidtaylor/Repositories/gauntlet/workout-wiz/.env && set +a && psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM audit_log WHERE session_id = '<session_id-from-UAT-API-001>' AND extra IS NULL;"
     ```
- **Expected Result**: Any entry that has keys beyond the 12 known fields shows them in `extra` as a JSONB object. Entries with only known fields have `extra = NULL`.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

### UAT-EDGE-002: Graph node logic is unchanged — audit_log in state is unmodified post-persistence

- **Description**: Verifies that calling `persist_audit_log` is a pure side-effect: the in-memory `audit_log` in the chat response is identical before and after Postgres persistence.
- **Steps**:
  1. Send a chat message and note the full `audit_log` array in the response:
     ```bash
     curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Log a squat session: 3 sets of 5 reps at 100kg"}' | jq '.audit_log'
     ```
  2. Send the same message again using the same `session_id` to accumulate a second turn; confirm the `audit_log` in the response still contains exactly the entries for this invocation (not duplicated by persistence logic):
     ```bash
     curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Log a squat session: 3 sets of 5 reps at 100kg","session_id":"<session_id-from-step-1>"}' | jq '.audit_log | length'
     ```
- **Expected Result**: Each call returns an `audit_log` array that reflects only the graph state entries; the array is not inflated or mutated by the Postgres persistence call. No duplicate entries appear in the in-memory response.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->
