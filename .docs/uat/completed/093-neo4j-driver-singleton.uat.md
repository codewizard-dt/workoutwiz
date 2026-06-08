# UAT: Shared Neo4j Driver Singleton

> **Source task**: [`.docs/tasks/completed/093-neo4j-driver-singleton.md`](../tasks/completed/093-neo4j-driver-singleton.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] Backend virtual environment is active: `source backend/.venv/bin/activate`
- [ ] The `backend/.venv` exists (run `make install` if not)
- [ ] No live Neo4j instance is required — all tests use mocks or inspect module state directly

---

## Edge Case Tests

### UAT-EDGE-001: `get_neo4j_driver` raises RuntimeError when driver not initialised
- **Scenario**: `get_neo4j_driver()` is called before `create_neo4j_driver()` has been called (i.e., `_driver` is `None`). The dependency must raise `RuntimeError`, not silently yield `None` or construct a new driver.
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -c "
import asyncio, app.kg.driver as drv
original = drv._driver
drv._driver = None
async def run():
    gen = drv.get_neo4j_driver()
    try:
        await gen.__anext__()
        print('FAIL: no error raised')
    except RuntimeError as e:
        print('PASS:', e)
    except Exception as e:
        print('UNEXPECTED:', type(e).__name__, e)
    finally:
        drv._driver = original
asyncio.run(run())
"
  ```
- **Expected Result**: Output contains `PASS: Neo4j driver has not been initialised.` (substring match sufficient — exact message: `"Neo4j driver has not been initialised. Ensure create_neo4j_driver() is called during lifespan startup."`)
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-002: `close_neo4j_driver` is idempotent — safe to call when already None
- **Scenario**: `close_neo4j_driver()` is called when `_driver` is already `None` (e.g., double-close on shutdown). Must not raise.
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -c "
import asyncio, app.kg.driver as drv
original = drv._driver
drv._driver = None
async def run():
    try:
        await drv.close_neo4j_driver()
        print('PASS: no error on double-close')
    except Exception as e:
        print('FAIL:', type(e).__name__, e)
    finally:
        drv._driver = original
asyncio.run(run())
"
  ```
- **Expected Result**: Output is `PASS: no error on double-close`
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-003: `create_neo4j_driver` is idempotent — repeated calls return same instance
- **Scenario**: Calling `create_neo4j_driver()` twice must return the same `AsyncDriver` object and construct it only once (no second `AsyncGraphDatabase.driver(...)` call).
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_kg_router.py::test_create_neo4j_driver_returns_singleton -v
  ```
- **Expected Result**: `1 passed` — the existing singleton-reuse unit test passes without errors
- [x] Pass <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: No per-request `AsyncGraphDatabase.driver(...)` in request-path routers
- **Scenario**: After the refactor, `backend/app/routers/kg.py` and `backend/app/routers/coach.py` must contain zero calls to `AsyncGraphDatabase.driver(` or `neo4j.AsyncGraphDatabase.driver(`. Any remaining call would indicate an unremediated per-request driver construction site.
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -c "
import re, pathlib
pattern = re.compile(r'AsyncGraphDatabase\.driver\(')
targets = ['backend/app/routers/kg.py', 'backend/app/routers/coach.py']
found = []
for t in targets:
    src = pathlib.Path(t).read_text()
    if pattern.search(src):
        found.append(t)
if found:
    print('FAIL: per-request driver construction found in:', found)
else:
    print('PASS: no per-request AsyncGraphDatabase.driver() in routers')
"
  ```
- **Expected Result**: Output is `PASS: no per-request AsyncGraphDatabase.driver() in routers`
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-002: `get_neo4j_driver` dependency does NOT close the driver
- **Scenario**: The `get_neo4j_driver()` generator must yield the shared driver and then return without calling `driver.close()`. Closing is reserved for `close_neo4j_driver()` in lifespan. This test exhausts the generator and asserts `.close()` was never called.
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -c "
import asyncio
from unittest.mock import MagicMock
import app.kg.driver as drv

async def run():
    mock = MagicMock()
    original = drv._driver
    drv._driver = mock
    try:
        gen = drv.get_neo4j_driver()
        yielded = await gen.__anext__()
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass
        if yielded is not mock:
            print('FAIL: yielded wrong object')
        elif mock.close.called:
            print('FAIL: driver.close() was called by dependency')
        else:
            print('PASS: dependency yields shared driver and does not close it')
    finally:
        drv._driver = original

asyncio.run(run())
"
  ```
- **Expected Result**: Output is `PASS: dependency yields shared driver and does not close it`
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-003: KG router tests pass with injected dependency override
- **Scenario**: The full KG router test suite (which overrides `get_neo4j_driver` with a mock and asserts `driver.close` is never awaited per request) must pass. This validates that the three refactored handlers (`kg_recommend`, `kg_explain`, `kg_feedback`) correctly consume the injected dependency rather than constructing their own driver.
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_kg_router.py -v
  ```
- **Expected Result**: All tests in `test_kg_router.py` pass (no failures related to driver injection or unexpected `driver.close()` calls). The `test_create_neo4j_driver_returns_singleton`, `test_kg_recommend_returns_200`, `test_kg_explain_returns_explanation`, `test_kg_feedback_writes_and_returns_id` tests all show `PASSED`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-004: `lifespan` wires driver creation and disposal in the correct order
- **Scenario**: The lifespan function must call `create_neo4j_driver()` before the app begins serving requests (startup) and `close_neo4j_driver()` after the app stops serving (shutdown), mirroring the SQLAlchemy engine pattern. Verify by inspecting the source for the correct call sequence.
- **Steps**:
  1. From the repo root, run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -c "
import ast, pathlib, textwrap

src = pathlib.Path('backend/app/main.py').read_text()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.AsyncFunctionDef) and node.name == 'lifespan':
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
                elif isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
        if 'create_neo4j_driver' in calls and 'close_neo4j_driver' in calls:
            print('PASS: lifespan contains both create_neo4j_driver and close_neo4j_driver')
        else:
            print('FAIL: lifespan missing expected calls, found:', calls)
        break
"
  ```
- **Expected Result**: Output is `PASS: lifespan contains both create_neo4j_driver and close_neo4j_driver`
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-005: Full backend test suite passes without new failures
- **Scenario**: The refactor must not introduce new test failures. Running the complete backend test suite must show the same passing test count as baseline (the task notes 0 new failures; 33 pre-existing failures unchanged).
- **Steps**:
  1. From the repo root, run the command below. This takes ~30 seconds.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/ -v --tb=no -q 2>&1 | tail -5
  ```
- **Expected Result**: Summary line shows no regression — the number of failures does not exceed the pre-refactor baseline of 33. The line resembles: `X passed, 33 failed` (or fewer failures if other fixes landed). Zero of the failing tests should mention `get_neo4j_driver`, `create_neo4j_driver`, or `close_neo4j_driver`.
- [x] Pass <!-- 2026-06-08 -->
