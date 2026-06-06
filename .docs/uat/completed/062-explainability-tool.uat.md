# UAT: Explainability Tool — Why Was This Exercise Skipped?

> **Source task**: [`.docs/tasks/062-explainability-tool.md`](../tasks/062-explainability-tool.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [x] Python virtualenv active (`source backend/.venv/bin/activate` or equivalent)
- [x] Working directory is project root
- [x] `backend/app/kg/explainability.py` exists
- [x] `backend/tests/kg/test_explainability.py` exists with ≥3 test functions

---

## Edge Case Tests

These tests exercise `explain_skipped_exercise()` via the pytest suite using a mocked Neo4j driver — no live database required.

### UAT-EDGE-001: Happy path — single injury contraindication

- **Scenario**: Neo4j returns a record with one matched injury; function returns the formatted sentence.
- **Steps**:
  1. Ensure prerequisites are met
  2. Run the command below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_explainability.py::test_explain_returns_injury_reason -v
  ```
- **Expected Result**: `PASSED` — output string contains the exercise name (`Barbell Squat`), the injury name (`Knee Tendinopathy`), and the word `contraindicated`.
- [x] Pass

### UAT-EDGE-002: Fallback — no record returned from Neo4j

- **Scenario**: `result.single()` returns `None` (no contraindication path exists in the graph); function returns the graceful fallback string without raising.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_explainability.py::test_explain_returns_fallback_when_no_contraindication -v
  ```
- **Expected Result**: `PASSED` — returned string contains `"insufficient context"` (case-insensitive).
- [x] Pass

### UAT-EDGE-003: Fallback — record exists but injury_names list is empty

- **Scenario**: Neo4j returns a record but `collect(i.name)` is an empty list (e.g., injury nodes exist but no names populated); function returns the graceful fallback string.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_explainability.py::test_explain_returns_fallback_when_no_injuries -v
  ```
- **Expected Result**: `PASSED` — returned string contains `"insufficient context"` (case-insensitive).
- [x] Pass

### UAT-EDGE-004: Full suite passes (≥3 tests, all green)

- **Scenario**: All unit tests for the explainability module pass together, confirming no interaction between test cases.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_explainability.py -v
  ```
- **Expected Result**: `3 passed` (or more) with exit code 0. Zero failures, zero errors.
- [x] Pass

---

## Integration Tests

### UAT-INT-001: Return format matches specification exactly

- **Scenario**: Verify the return string for a single-injury contraindication matches the exact format `"'{exercise_name}' was skipped because it is contraindicated for: {injuries}."` as required by the task spec.
- **Steps**:
  1. Run the inline Python assertion below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
import asyncio, sys
sys.path.insert(0, '.')
from unittest.mock import AsyncMock, MagicMock

def build_driver(ex_name, injuries):
    driver = MagicMock()
    record = MagicMock()
    record.__getitem__ = lambda self, k: ex_name if k == 'exercise_name' else injuries
    record.__bool__ = lambda self: True
    result = AsyncMock(); result.single = AsyncMock(return_value=record)
    session = AsyncMock(); session.run = AsyncMock(return_value=result)
    ctx = AsyncMock(); ctx.__aenter__ = AsyncMock(return_value=session); ctx.__aexit__ = AsyncMock(return_value=False)
    driver.session.return_value = ctx
    return driver

from app.kg.explainability import explain_skipped_exercise
result = asyncio.run(explain_skipped_exercise('m1', 'e1', build_driver('Squats', ['Knee Tendinopathy'])))
expected = \"'Squats' was skipped because it is contraindicated for: Knee Tendinopathy.\"
assert result == expected, f'Got: {result!r}'
print('PASS:', result)
"
  ```
- **Expected Result**: Prints `PASS: 'Squats' was skipped because it is contraindicated for: Knee Tendinopathy.` with exit code 0.
- [x] Pass

### UAT-INT-002: Multiple injuries joined with comma-space separator

- **Scenario**: When two or more injuries cause the skip, they are joined with `", "` (comma + space) in the output sentence.
- **Steps**:
  1. Run the inline Python assertion below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
import asyncio, sys
sys.path.insert(0, '.')
from unittest.mock import AsyncMock, MagicMock

def build_driver(ex_name, injuries):
    driver = MagicMock()
    record = MagicMock()
    record.__getitem__ = lambda self, k: ex_name if k == 'exercise_name' else injuries
    record.__bool__ = lambda self: True
    result = AsyncMock(); result.single = AsyncMock(return_value=record)
    session = AsyncMock(); session.run = AsyncMock(return_value=result)
    ctx = AsyncMock(); ctx.__aenter__ = AsyncMock(return_value=session); ctx.__aexit__ = AsyncMock(return_value=False)
    driver.session.return_value = ctx
    return driver

from app.kg.explainability import explain_skipped_exercise
result = asyncio.run(explain_skipped_exercise('m1', 'e1', build_driver('Leg Press', ['Knee Tendinopathy', 'Patellofemoral Syndrome'])))
assert 'Knee Tendinopathy, Patellofemoral Syndrome' in result, f'Got: {result!r}'
print('PASS:', result)
"
  ```
- **Expected Result**: Prints `PASS: 'Leg Press' was skipped because it is contraindicated for: Knee Tendinopathy, Patellofemoral Syndrome.` with exit code 0.
- [x] Pass
