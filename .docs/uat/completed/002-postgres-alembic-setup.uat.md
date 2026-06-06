# UAT: PostgreSQL Database, Alembic Migrations, and Connection Pooling

> **Source task**: [`.docs/tasks/002-postgres-alembic-setup.md`](../tasks/002-postgres-alembic-setup.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Python 3 available on PATH (`python3 --version`)
- [ ] Working directory is the project root `/Users/davidtaylor/Repositories/gauntlet/workout-wiz` (or adjust paths accordingly)
- [ ] Docker is **not** required for static file checks (UAT-FILE-001 through UAT-FILE-005)

---

## File / Static Checks

These tests verify configuration files are present and contain the required values. No running services needed.

### UAT-FILE-001: docker-compose.yml exists with correct postgres service config
- **Description**: Verify `docker-compose.yml` exists at the project root and contains the required PostgreSQL 16 service definition with the expected environment variables, port mapping, volume, and healthcheck.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, pathlib
content = pathlib.Path('docker-compose.yml').read_text()
checks = {
    'image postgres:16-alpine': 'postgres:16-alpine' in content,
    'POSTGRES_USER=postgres': 'POSTGRES_USER: postgres' in content,
    'POSTGRES_PASSWORD=postgres': 'POSTGRES_PASSWORD: postgres' in content,
    'POSTGRES_DB=workoutwiz': 'POSTGRES_DB: workoutwiz' in content,
    'port mapping 5433:5432': '5433:5432' in content,
    'volume postgres_data': 'postgres_data' in content,
    'healthcheck pg_isready': 'pg_isready -U postgres' in content,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    print('FAIL - missing:', failed); sys.exit(1)
print('PASS - all checks present')
"
  ```
- **Expected Result**: `PASS - all checks present`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-002: database.py has required pool settings
- **Description**: Verify `backend/app/database.py` configures the SQLAlchemy async engine with `pool_size=5`, `max_overflow=10`, and `pool_pre_ping=True`.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, pathlib
content = pathlib.Path('backend/app/database.py').read_text()
checks = {
    'pool_size=5': 'pool_size=5' in content,
    'max_overflow=10': 'max_overflow=10' in content,
    'pool_pre_ping=True': 'pool_pre_ping=True' in content,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    print('FAIL - missing:', failed); sys.exit(1)
print('PASS - all pool settings present')
"
  ```
- **Expected Result**: `PASS - all pool settings present`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-003: backend/.gitignore excludes .env
- **Description**: Verify `backend/.gitignore` exists and contains a rule that excludes `.env` files so credentials are never committed.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, pathlib
p = pathlib.Path('backend/.gitignore')
if not p.exists():
    print('FAIL - backend/.gitignore does not exist'); sys.exit(1)
lines = [l.strip() for l in p.read_text().splitlines()]
if '.env' not in lines:
    print('FAIL - .env not found as a standalone line in backend/.gitignore'); sys.exit(1)
print('PASS - backend/.gitignore excludes .env')
"
  ```
- **Expected Result**: `PASS - backend/.gitignore excludes .env`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-004: migrations/versions/ directory exists with at least one migration file
- **Description**: Verify `backend/migrations/versions/` exists and contains at least one `.py` migration file, confirming the Alembic pipeline produced an initial revision.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, pathlib
versions_dir = pathlib.Path('backend/migrations/versions')
if not versions_dir.is_dir():
    print('FAIL - backend/migrations/versions/ directory does not exist'); sys.exit(1)
migration_files = [f for f in versions_dir.iterdir() if f.suffix == '.py' and f.name != '__init__.py']
if not migration_files:
    print('FAIL - no .py migration files found in backend/migrations/versions/'); sys.exit(1)
print(f'PASS - found {len(migration_files)} migration file(s):', [f.name for f in migration_files])
"
  ```
- **Expected Result**: `PASS - found 1 migration file(s): ['c18404816173_initial.py']` (or similar — at least one `.py` file)
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-005: alembic.ini has script_location = migrations
- **Description**: Verify `backend/alembic.ini` sets `script_location = migrations` so Alembic finds the correct migrations directory.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, pathlib
p = pathlib.Path('backend/alembic.ini')
if not p.exists():
    print('FAIL - backend/alembic.ini does not exist'); sys.exit(1)
content = p.read_text()
if 'script_location = migrations' not in content:
    print('FAIL - script_location = migrations not found in backend/alembic.ini'); sys.exit(1)
print('PASS - alembic.ini has script_location = migrations')
"
  ```
- **Expected Result**: `PASS - alembic.ini has script_location = migrations`
- [x] Pass <!-- 2026-06-04 -->

---

## Edge Case Tests

### UAT-EDGE-001: .env is not tracked by git
- **Description**: Confirm that `backend/.env` (if it exists) is not tracked by git, validating the `.gitignore` rule is effective.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, subprocess
result = subprocess.run(['git', 'ls-files', 'backend/.env'], capture_output=True, text=True)
if result.stdout.strip():
    print('FAIL - backend/.env is tracked by git:', result.stdout.strip()); sys.exit(1)
print('PASS - backend/.env is not tracked by git')
"
  ```
- **Expected Result**: `PASS - backend/.env is not tracked by git`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-002: Migration file is syntactically valid Python
- **Description**: Confirm the generated migration file in `backend/migrations/versions/` is valid Python (parseable without syntax errors).
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  python3 -c "
import sys, pathlib, ast
versions_dir = pathlib.Path('backend/migrations/versions')
migration_files = [f for f in versions_dir.iterdir() if f.suffix == '.py' and f.name != '__init__.py']
if not migration_files:
    print('FAIL - no migration files to validate'); sys.exit(1)
errors = []
for f in migration_files:
    try:
        ast.parse(f.read_text())
    except SyntaxError as e:
        errors.append(f'{f.name}: {e}')
if errors:
    print('FAIL - syntax errors:', errors); sys.exit(1)
print('PASS - all migration files are valid Python:', [f.name for f in migration_files])
"
  ```
- **Expected Result**: `PASS - all migration files are valid Python: ['c18404816173_initial.py']` (or similar)
- [x] Pass <!-- 2026-06-04 -->
