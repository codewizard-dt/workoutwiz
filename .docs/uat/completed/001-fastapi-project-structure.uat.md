# UAT: FastAPI Project Structure

> **Source task**: [`.docs/tasks/completed/001-fastapi-project-structure.md`](../tasks/completed/001-fastapi-project-structure.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] `backend/` directory exists in the project root
- [ ] Python 3.11+ is available (`python3 --version`)
- [ ] Dependencies installed: run `pip install -e ".[dev]"` from `backend/`
- [ ] A running FastAPI server for HTTP tests: `uvicorn app.main:app --host 127.0.0.1 --port 8000` from `backend/` (no database required)

---

## API Tests

### UAT-API-001: GET /healthz returns 200 with correct body
- **Endpoint**: `GET /healthz`
- **Description**: Verify the health-check route is registered, reachable, and returns the exact required shape
- **Steps**:
  1. Ensure the uvicorn server is running (see Prerequisites)
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X GET 'http://127.0.0.1:8000/healthz'
  ```
- **Expected Result**: `200 OK` with body `{"status":"ok"}`
- [x] Pass <!-- 2026-06-04 -->

---

## Edge Case Tests

### UAT-EDGE-001: App module imports without a running database
- **Scenario**: All application modules (`app.main`, `app.config`, `app.database`) must be importable without a live PostgreSQL connection — the engine is created lazily, so startup should not fail if the DB is unreachable
- **Steps**:
  1. Ensure no database is running (or that `DATABASE_URL` points to a non-existent host)
  2. Run the python command below from `backend/`
- **Command**:
  ```bash
  python -c 'from app.main import app; print("import ok")'
  ```
- **Expected Result**: Prints `import ok` with exit code 0; no `ImportError`, `OperationalError`, or other exception
- [x] Pass <!-- 2026-06-04 -->

---

## Integration Tests

### UAT-INT-001: All required Python files exist and are syntactically valid
- **Components**: `backend/` directory tree — all Python source files scaffolded by this task
- **Flow**: Verify file presence and syntax validity for every file listed in the task acceptance criteria
- **Steps**:
  1. From `backend/`, run the syntax-check command below
- **Command**:
  ```bash
  python -m py_compile app/__init__.py app/config.py app/database.py app/main.py app/models/__init__.py app/schemas/__init__.py app/routers/__init__.py migrations/__init__.py migrations/env.py && echo "all syntax ok"
  ```
- **Expected Result**: Prints `all syntax ok` with exit code 0; no `SyntaxError` output
- [x] Pass <!-- 2026-06-04 -->

### UAT-INT-002: alembic.ini has script_location = migrations
- **Components**: `backend/alembic.ini` — Alembic configuration consumed by `migrations/env.py`
- **Flow**: Verify the Alembic config file correctly points migration scripts to the `migrations/` directory
- **Steps**:
  1. From `backend/`, run the python command below
- **Command**:
  ```bash
  python -c 'import configparser; c=configparser.ConfigParser(); c.read("alembic.ini"); v=c["alembic"]["script_location"]; print(v); assert v=="migrations", f"expected migrations, got {v}"'
  ```
- **Expected Result**: Prints `migrations` with exit code 0; no `AssertionError`
- [x] Pass <!-- 2026-06-04 -->

### UAT-INT-003: pyproject.toml declares all required dependencies
- **Components**: `backend/pyproject.toml` — dependency manifest read by pip
- **Flow**: Verify every dependency listed in the task spec is present in pyproject.toml with a minimum-version pin
- **Steps**:
  1. From `backend/`, run the python command below
- **Command**:
  ```bash
  python -c "import tomllib; d=tomllib.loads(open('pyproject.toml').read()); deps=d['project']['dependencies']; names=[s.split('>=')[0].split('[')[0] for s in deps]; required=['fastapi','uvicorn','sqlalchemy','asyncpg','alembic','fastapi-users','pydantic-settings','python-multipart']; missing=[r for r in required if r not in names]; print('present:', names); assert not missing, f'missing: {missing}'"
  ```
- **Expected Result**: Prints the list of present package names with exit code 0; no `AssertionError`; all eight required packages are present
- [x] Pass <!-- 2026-06-04 -->

### UAT-INT-004: Settings class reads DATABASE_URL from environment
- **Components**: `backend/app/config.py` — `Settings` / `pydantic-settings`
- **Flow**: Verify the `Settings` class honours an env-var override (not just the `.env` file default)
- **Steps**:
  1. From `backend/`, run the python command below
- **Command**:
  ```bash
  python -c 'import os; os.environ["DATABASE_URL"]="postgresql+asyncpg://test:test@testhost:5432/testdb"; from app import config; s=config.Settings(); print(s.database_url); assert "testhost" in s.database_url'
  ```
- **Expected Result**: Prints a URL containing `testhost` with exit code 0; no `AssertionError`
- [x] Pass <!-- 2026-06-04 -->

### UAT-INT-005: database.py exports required symbols
- **Components**: `backend/app/database.py` — engine, session factory, Base, dependency
- **Flow**: Verify all four symbols required by downstream tasks are exported from the module
- **Steps**:
  1. From `backend/`, run the python command below
- **Command**:
  ```bash
  python -c 'from app.database import engine, AsyncSessionLocal, Base, get_async_session; from sqlalchemy.orm import DeclarativeBase; assert issubclass(Base, DeclarativeBase); print("database exports ok")'
  ```
- **Expected Result**: Prints `database exports ok` with exit code 0; no `ImportError` or `AssertionError`; `Base` is confirmed to be a `DeclarativeBase` subclass
- [x] Pass <!-- 2026-06-04 -->
