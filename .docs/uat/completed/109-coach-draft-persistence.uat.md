# UAT: Coach Draft Persistence

> **Source task**: [`.docs/tasks/109-coach-draft-persistence.md`](../tasks/109-coach-draft-persistence.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Docker Compose stack is running (`docker compose up -d`)
- [ ] `db` service is healthy (`docker compose ps db` shows `healthy`)
- [ ] Migration `d1e2f3a4b5c6` has been applied (`make migrate` or `docker compose exec backend alembic upgrade head`)
- [ ] Python venv is available at `backend/.venv/`

---

## API Tests

_No HTTP endpoints are introduced by TASK-109. The persistence layer only (model, migration, schema) is tested below via database introspection and Python import checks._

---

## Edge Case Tests

### UAT-EDGE-001: Alembic head is `d1e2f3a4b5c6`
- **Scenario**: The migration ran successfully and Alembic reports the new revision as current head
- **Steps**:
  1. Run the command below against the running backend container
- **Command**:
  ```bash
  docker compose exec backend alembic -c /app/alembic.ini current 2>&1
  ```
- **Expected Result**: Output contains `d1e2f3a4b5c6 (head)` — confirming the `add_coach_drafts_table` migration is applied
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-002: `coach_drafts` table exists with all required columns
- **Scenario**: PostgreSQL table was created with all 14 columns defined in the task
- **Steps**:
  1. Run the psql command below against the local DB port (5433)
- **Command**:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "\d coach_drafts"
  ```
- **Expected Result**: Output lists all 14 columns: `id`, `member_id`, `member_name`, `content_type`, `body`, `grounded_on`, `status`, `created_by`, `approved_by`, `approved_at`, `sent_at`, `created_at`, `updated_at`. Column types match: `id` is `uuid`, `body`/`grounded_on` are `text`, `status` and `content_type` are enum types, datetime columns include timezone info.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-003: `coachdraftstatus` ENUM has exactly three values
- **Scenario**: The PostgreSQL ENUM type for status contains only `draft`, `approved`, `sent`
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "SELECT enum_range(NULL::coachdraftstatus);"
  ```
- **Expected Result**: Output shows `{draft,approved,sent}` — exactly three values in that order
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-004: `coachdraftcontenttype` ENUM has exactly two values
- **Scenario**: The PostgreSQL ENUM type for content_type contains only `nudge`, `recommendation`
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "SELECT enum_range(NULL::coachdraftcontenttype);"
  ```
- **Expected Result**: Output shows `{nudge,recommendation}` — exactly two values
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-005: Indexes on `member_id` and `status` exist
- **Scenario**: The migration created the two performance indexes defined in the task
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'coach_drafts' ORDER BY indexname;"
  ```
- **Expected Result**: Output includes rows for `ix_coach_drafts_member_id` (on column `member_id`) and `ix_coach_drafts_status` (on column `status`), plus the primary key index
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-006: `status` column defaults to `draft`
- **Scenario**: New rows inserted without a status value get `draft` as the server default
- **Steps**:
  1. Insert a minimal row omitting the status column
  2. Query the row back
- **Command**:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "INSERT INTO coach_drafts (id, member_id, member_name, content_type, body) VALUES (gen_random_uuid(), 'uat-member-001', 'UAT Member', 'nudge', 'Test body') RETURNING id, status;"
  ```
- **Expected Result**: The returned row shows `status = draft` — confirming the server default is applied
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-007: Python `CoachDraft` model importable from `backend.app.models`
- **Scenario**: `CoachDraft`, `CoachDraftStatus`, and `CoachDraftContentType` are all accessible from the package `__init__`
- **Steps**:
  1. Run the Python one-liner below using the project venv
- **Command**:
  ```bash
  backend/.venv/bin/python -c "from app.models import CoachDraft, CoachDraftStatus, CoachDraftContentType; print('CoachDraft OK'); print('statuses:', [e.value for e in CoachDraftStatus]); print('content_types:', [e.value for e in CoachDraftContentType])" 2>&1
  ```
- **Expected Result**: Prints:
  ```
  CoachDraft OK
  statuses: ['draft', 'approved', 'sent']
  content_types: ['nudge', 'recommendation']
  ```
  No import errors or tracebacks
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-008: `CoachDraftSchema` importable and validates `from_attributes`
- **Scenario**: The Pydantic schema is accessible from `backend.app.schemas.coach` and has `from_attributes = True`
- **Steps**:
  1. Run the Python one-liner below using the project venv
- **Command**:
  ```bash
  backend/.venv/bin/python -c "from app.schemas.coach import CoachDraftSchema; m = CoachDraftSchema.model_config; print('from_attributes:', m.get('from_attributes')); import inspect; fields = list(CoachDraftSchema.model_fields.keys()); print('fields:', fields)" 2>&1
  ```
- **Expected Result**: Prints `from_attributes: True` and `fields:` lists all 13 schema fields: `id`, `member_id`, `member_name`, `content_type`, `body`, `grounded_on`, `status`, `created_by`, `approved_by`, `approved_at`, `sent_at`, `created_at` (note: `updated_at` is not in the Pydantic schema per the task spec). No import errors.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-009: Migration downgrade removes table and ENUMs
- **Scenario**: Running `alembic downgrade -1` cleanly removes the `coach_drafts` table and both ENUM types
- **Steps**:
  1. Run the downgrade via the backend container
  2. Verify the table is gone
  3. Re-apply the migration to restore the state
- **Command**:
  ```bash
  docker compose exec backend alembic -c /app/alembic.ini downgrade -1 2>&1
  ```
  Then verify:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "SELECT to_regclass('public.coach_drafts');"
  ```
  Then restore:
  ```bash
  docker compose exec backend alembic -c /app/alembic.ini upgrade head 2>&1
  ```
- **Expected Result**: After downgrade, `SELECT to_regclass(...)` returns `NULL` (table does not exist). After `upgrade head`, Alembic reports `d1e2f3a4b5c6 (head)` again. No errors during either migration step.
- [x] Pass <!-- 2026-06-11 -->

---

## Integration Tests

### UAT-INT-001: Full round-trip — insert, query, and validate a `coach_drafts` row
- **Components**: PostgreSQL `coach_drafts` table, `coachdraftstatus` ENUM, `coachdraftcontenttype` ENUM
- **Flow**: Insert a row with all non-nullable fields set, then read it back and confirm every column value round-trips correctly
- **Steps**:
  1. Insert a full row
  2. Query it back by the returned `id`
- **Command**:
  ```bash
  docker compose exec db psql -U postgres -d workoutwiz -c "WITH ins AS (INSERT INTO coach_drafts (id, member_id, member_name, content_type, body, grounded_on, status, created_by) VALUES (gen_random_uuid(), 'int-member-001', 'Integration Member', 'recommendation', 'Increase your squat frequency to 3x/week.', '[\"workout_123\",\"workout_456\"]', 'draft', 'coach@example.com') RETURNING *) SELECT id, member_id, content_type, status, created_by, approved_by, approved_at, sent_at FROM ins;" 2>&1
  ```
- **Expected Result**: Row returned with:
  - `member_id = int-member-001`
  - `content_type = recommendation`
  - `status = draft`
  - `created_by = coach@example.com`
  - `approved_by = NULL`
  - `approved_at = NULL`
  - `sent_at = NULL`
  No errors; `id` is a valid UUID; `created_at` and `updated_at` are populated by server defaults
- [x] Pass <!-- 2026-06-11 -->
