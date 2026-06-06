# UAT: Exercise Seed Data

> **Source task**: [`.docs/tasks/completed/005-exercise-seed-data.md`](../tasks/completed/005-exercise-seed-data.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] `backend/.venv` exists (Python virtualenv installed)
- [ ] PostgreSQL is running and `workoutwiz` database exists with migrations applied
- [ ] `backend/.env` exists (or `settings.database_url` defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/workoutwiz`)
- [ ] Working directory is `backend/` for all script commands

---

## Static / Import Tests

### UAT-STATIC-001: ExerciseSeedRecord schema file exists
- **Description**: Verify `backend/app/schemas/exercise_seed.py` exists on disk.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "import pathlib; p = pathlib.Path('backend/app/schemas/exercise_seed.py'); print('EXISTS' if p.exists() else 'MISSING')"
  ```
- **Expected Result**: Prints `EXISTS`
- [x] Pass <!-- 2026-06-04 -->

### UAT-STATIC-002: ExerciseSeedRecord is importable
- **Description**: Verify `ExerciseSeedRecord` can be imported from `app.schemas.exercise_seed` without errors.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); from app.schemas.exercise_seed import ExerciseSeedRecord; print('OK:', ExerciseSeedRecord.__name__)"
  ```
- **Expected Result**: Prints `OK: ExerciseSeedRecord`
- [x] Pass <!-- 2026-06-04 -->

### UAT-STATIC-003: ExerciseSeedRecord has all required fields
- **Description**: Verify `ExerciseSeedRecord` declares the full set of required fields: `id`, `name`, `muscle_groups`, `equipment_required`, `movement_patterns`, `is_reps`, `is_duration`, `supports_weight`, `is_bilateral`, `bilateral_pair_id`, `priority_tier`, `description`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); from app.schemas.exercise_seed import ExerciseSeedRecord; fields = set(ExerciseSeedRecord.model_fields.keys()); required = {'id','name','muscle_groups','equipment_required','movement_patterns','is_reps','is_duration','supports_weight','is_bilateral','bilateral_pair_id','priority_tier','description'}; missing = required - fields; print('MISSING:', missing) if missing else print('ALL FIELDS PRESENT')"
  ```
- **Expected Result**: Prints `ALL FIELDS PRESENT`
- [x] Pass <!-- 2026-06-04 -->

### UAT-STATIC-004: seed_exercises.py file exists and is syntactically valid
- **Description**: Verify `backend/scripts/seed_exercises.py` exists and parses without `SyntaxError`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "import ast, pathlib; src = pathlib.Path('backend/scripts/seed_exercises.py').read_text(); ast.parse(src); print('SYNTAX OK')"
  ```
- **Expected Result**: Prints `SYNTAX OK`
- [x] Pass <!-- 2026-06-04 -->

### UAT-STATIC-005: EXERCISES_JSON resolves relative to project root (not hardcoded)
- **Description**: Verify the `EXERCISES_JSON` constant in `seed_exercises.py` is derived via `Path(__file__)` traversal, not a hardcoded absolute path, and that it resolves to the actual `1-multi-agent/exercises.json` file.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); from pathlib import Path; script = Path('backend/scripts/seed_exercises.py').resolve(); resolved = script.parent.parent.parent / '1-multi-agent' / 'exercises.json'; print('RESOLVES TO:', resolved); print('EXISTS:', resolved.exists())"
  ```
- **Expected Result**: Prints a path ending in `1-multi-agent/exercises.json` and `EXISTS: True`
- [x] Pass <!-- 2026-06-04 -->

---

## Validation Tests

### UAT-VAL-001: All 50 exercises.json records validate against ExerciseSeedRecord
- **Description**: Verify every record in `1-multi-agent/exercises.json` passes Pydantic validation via `ExerciseSeedRecord` (no `ValidationError` raised).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "import sys, json; sys.path.insert(0, 'backend'); from app.schemas.exercise_seed import ExerciseSeedRecord; data = json.load(open('1-multi-agent/exercises.json')); records = [ExerciseSeedRecord(**e) for e in data]; print(f'Validated {len(records)} records')"
  ```
- **Expected Result**: Prints `Validated 50 records`
- [x] Pass <!-- 2026-06-04 -->

---

## Integration Tests (Live DB)

### UAT-INT-001: Database contains exactly 50 exercises after seed
- **Description**: Verify `SELECT COUNT(*) FROM exercises` returns 50, confirming the seed script ran successfully against the live database.
- **Steps**:
  1. Ensure DB is running and migrations have been applied
  2. Run the command below from the repo root
- **Command**:
  ```bash
  /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/.venv/bin/python -c "
import asyncio, sys
sys.path.insert(0, 'backend')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
async def check():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        count = (await session.execute(text('SELECT COUNT(*) FROM exercises'))).scalar()
        print(f'exercises count: {count}')
        assert count == 50, f'Expected 50, got {count}'
        print('PASS')
    await engine.dispose()
asyncio.run(check())
"
  ```
- **Expected Result**: Prints `exercises count: 50` then `PASS`
- [x] Pass <!-- 2026-06-04 -->

### UAT-INT-002: Idempotency — re-running seed script skips if rows exist
- **Description**: Verify running `seed_exercises.py` a second time (when 50 rows already exist) prints the skip message and does not raise an error or duplicate rows.
- **Steps**:
  1. Ensure DB already has 50 exercises (UAT-INT-001 must pass first)
  2. Run the seed script again
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && .venv/bin/python scripts/seed_exercises.py
  ```
- **Expected Result**: Prints `Validated 50 exercises.` followed by `Exercises table already has 50 rows. Skipping seed.` No error output. Count remains 50.
- [x] Pass <!-- 2026-06-04 -->

---

*Note*: No API or UI tests are included — TASK-005 introduces only a Pydantic schema and a standalone seed script with no HTTP endpoints or frontend components.
