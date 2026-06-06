# UAT: Install Core Dependencies and Environment Config

> **Source task**: [`.docs/tasks/020-install-core-dependencies.md`](../tasks/020-install-core-dependencies.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Task 019 (python-package-setup) is complete — `.venv` exists at `1-multi-agent/.venv/`
- [ ] Working directory is the repo root (`workoutwiz/`)
- [ ] `.env` file does NOT exist at `1-multi-agent/.env` (to avoid polluting import test with pre-set vars)

---

## Edge Case Tests

### UAT-EDGE-001: All core imports succeed inside the venv
- **Scenario**: All declared runtime dependencies install cleanly and are importable
- **Steps**:
  1. Run the command below from the repo root (activates venv inline via `bash -c`)
- **Command**:
  ```bash
  bash -c 'cd 1-multi-agent && source .venv/bin/activate && python -c "import langgraph; import langchain; import langchain_anthropic; import anthropic; import pydantic; import rapidfuzz; import fastapi; import uvicorn; print(\"All imports OK\")"'
  ```
- **Expected Result**: Exits 0 and prints `All imports OK` with no import errors or tracebacks
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: fastapi and uvicorn importable (runtime server deps)
- **Scenario**: FastAPI and Uvicorn are declared in `pyproject.toml` and must be importable
- **Steps**:
  1. Run the command below — checks the two server-layer deps separately to surface any version conflict
- **Command**:
  ```bash
  bash -c 'cd 1-multi-agent && source .venv/bin/activate && python -c "import fastapi; import uvicorn; print(fastapi.__version__, uvicorn.__version__)"'
  ```
- **Expected Result**: Exits 0 and prints two version strings (e.g. `0.115.x 0.32.x`) — no ImportError
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: `.env.example` exists with required keys
- **Scenario**: Assessors and operators need `.env.example` to know which secrets to supply; all required vars must be documented
- **Steps**:
  1. Read `1-multi-agent/.env.example` — confirm all five expected keys are present
- **Command**:
  ```bash
  python -c "
content = open('1-multi-agent/.env.example').read()
required = ['ANTHROPIC_API_KEY', 'COACH_MODEL', 'ROUTER_MODEL', 'GENERATOR_MODEL', 'LOGGER_MODEL']
missing = [k for k in required if k not in content]
print('Missing:', missing) if missing else print('All required keys present')
"
  ```
- **Expected Result**: Prints `All required keys present` — no missing keys
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: `.env.example` documents default model values
- **Scenario**: All four model vars must have documented defaults so the system can run out of the box with no customisation
- **Steps**:
  1. Read `1-multi-agent/.env.example` and confirm each model var has an assigned value (not blank)
- **Command**:
  ```bash
  python -c "
import re
content = open('1-multi-agent/.env.example').read()
models = ['COACH_MODEL', 'ROUTER_MODEL', 'GENERATOR_MODEL', 'LOGGER_MODEL']
for m in models:
    match = re.search(rf'^{m}=(.+)$', content, re.MULTILINE)
    if not match or not match.group(1).strip():
        print(f'MISSING or BLANK: {m}')
    else:
        print(f'OK: {m}={match.group(1).strip()}')
"
  ```
- **Expected Result**: Prints four `OK: <VAR>=<value>` lines — no MISSING or BLANK lines
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-003: `src/workout_wiz/__init__.py` calls `load_dotenv()`
- **Scenario**: The package init must call `load_dotenv()` so `.env` is loaded automatically at import time
- **Steps**:
  1. Inspect the package init for the `load_dotenv` call
- **Command**:
  ```bash
  python -c "
content = open('1-multi-agent/src/workout_wiz/__init__.py').read()
assert 'load_dotenv' in content, 'load_dotenv NOT found in __init__.py'
print('load_dotenv call present')
"
  ```
- **Expected Result**: Prints `load_dotenv call present` — no AssertionError
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-004: `.env` is gitignored; `.env.example` is not
- **Scenario**: Real secrets (`.env`) must never be committed; the template (`.env.example`) must be tracked
- **Steps**:
  1. Read the root `.gitignore` and verify `.env` is excluded while `.env.example` is explicitly allowed
- **Command**:
  ```bash
  python -c "
content = open('.gitignore').read()
lines = content.splitlines()
env_ignored = any(l.strip() in ('.env', '.env.*') for l in lines)
example_excepted = any(l.strip() == '!.env.example' for l in lines)
print('env_ignored:', env_ignored)
print('example_excepted:', example_excepted)
assert env_ignored, '.env is NOT in .gitignore'
assert example_excepted, '!.env.example negation NOT in .gitignore'
print('gitignore rules correct')
"
  ```
- **Expected Result**: Prints `env_ignored: True`, `example_excepted: True`, then `gitignore rules correct` — no AssertionError
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-005: `load_dotenv()` actually loads vars from a `.env` file
- **Scenario**: Verify the end-to-end dotenv integration — writing a temp `.env` and importing the package should expose the var
- **Steps**:
  1. Create a temporary `.env` in `1-multi-agent/` with a test var, import the package, verify the var is present, then delete the temp file
- **Command**:
  ```bash
  bash -c 'cd 1-multi-agent && echo "UAT_TEST_VAR=hello_uat" > .env && source .venv/bin/activate && python -c "import workout_wiz; import os; v=os.getenv(\"UAT_TEST_VAR\"); print(\"VAR:\", v); assert v==\"hello_uat\", f\"Expected hello_uat got {v}\"" && rm .env'
  ```
- **Expected Result**: Prints `VAR: hello_uat` and exits 0. The `.env` file is removed by the cleanup in the command.
- [x] Pass <!-- 2026-06-05 -->
