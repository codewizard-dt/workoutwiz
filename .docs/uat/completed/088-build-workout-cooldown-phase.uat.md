# UAT: Build Workout Cooldown Phase

> **Source task**: [`.docs/tasks/completed/088-build-workout-cooldown-phase.md`](../tasks/completed/088-build-workout-cooldown-phase.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] Backend virtualenv exists at `backend/.venv/`
- [ ] `exercises.json` dataset is present at `.docs/guides/1-multi-agent/exercises.json` (50 exercises including regen/mobility-tagged entries)
- [ ] The exercise cache is seeded (either via `load_exercises()` or by the test fixtures — the pytest suite manages this internally)
- [ ] `.env` file is present and loadable for the critical/integration tests that hit the real dataset

---

## Unit Tests (pytest)

### UAT-UNIT-001: build_workout_tool returns non-empty cooldown when recovery exercises exist in cache

- **Test file**: `backend/tests/test_agents_generator.py`
- **Test function**: `test_build_workout_tool_emits_non_empty_cooldown`
- **Description**: Verifies that when the exercise cache contains at least one exercise with a `movement_patterns` value matching `"regen"`, `"mobility - static"`, or `"mobility - dynamic"`, `build_workout_tool` populates `phases.cooldown` with a non-empty list.
- **Steps**:
  1. From the `backend/` directory, load the env and run the specific test:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_generator.py::test_build_workout_tool_emits_non_empty_cooldown -v
  ```
- **Expected Result**: `1 passed` — the test asserts that `phases.cooldown` is non-empty, every cooldown entry `id` is in the stubbed cache, no cooldown `id` appears in `warmup` or `main`, and every entry contains keys `id`, `name`, `sets`, `reps`, `duration_s`, `rest_s`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-UNIT-002: Cooldown entry dict shape is correct — low-intensity overrides applied

- **Test file**: `backend/tests/test_agents_generator.py`
- **Test function**: `test_build_workout_tool_emits_non_empty_cooldown` (shape assertions within)
- **Description**: Verifies that each cooldown dict carries exactly the six keys produced by `exercise_to_dict` with `override_sets=1` and `override_rest=30`. For a regen exercise (`is_duration=True`, `is_reps=False`): `sets=1`, `reps=None`, `duration_s=30`, `rest_s=30`.
- **Steps**:
  1. Same run as UAT-UNIT-001; the shape assertions are part of the same test function.
  2. Confirm the test output shows no `AssertionError` for key presence or value expectations.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_generator.py::test_build_workout_tool_emits_non_empty_cooldown -v -s
  ```
- **Expected Result**: `1 passed`. Cooldown entries contain `{"id": <str>, "name": <str>, "sets": 1, "reps": null, "duration_s": 30, "rest_s": 30}` (null/None for reps, integer 30 for duration_s and rest_s).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-UNIT-003: Cooldown IDs do not overlap warmup or main

- **Test file**: `backend/tests/test_agents_generator.py`
- **Test function**: `test_build_workout_tool_emits_non_empty_cooldown`
- **Description**: Verifies the exclusion logic — `_select_cooldown_exercises` receives `exclude_ids = {str(e.id) for e in warmup + main}` and therefore no cooldown entry appears in either the warmup or main phase.
- **Steps**:
  1. Same test run as UAT-UNIT-001; the no-overlap assertions are in the same test function.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_generator.py::test_build_workout_tool_emits_non_empty_cooldown -v
  ```
- **Expected Result**: `1 passed` — no assertion fires for `"cooldown id ... also in warmup"` or `"cooldown id ... also in main"`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-UNIT-004: Cooldown is empty (not an error) when cache has no recovery-tagged exercises

- **Test file**: `backend/tests/test_agents_generator.py`
- **Test function**: `test_build_workout_tool_empty_cooldown_when_no_recovery_exercises`
- **Description**: Verifies the graceful no-op path: when the cache contains only strength exercises (no `"regen"` / `"mobility"` movement patterns), `build_workout_tool` returns `phases.cooldown == []` without raising any exception.
- **Steps**:
  1. Run the test:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_generator.py::test_build_workout_tool_empty_cooldown_when_no_recovery_exercises -v
  ```
- **Expected Result**: `1 passed` — `workout["phases"]["cooldown"]` equals `[]` and no exception was raised.
- [x] Pass <!-- 2026-06-07 -->

---

## Integration Tests (pytest — real dataset)

### UAT-INT-001: Cooldown IDs are all valid dataset exercise IDs (critical grounding)

- **Test file**: `backend/tests/test_agents_critical_generator.py`
- **Test function**: `test_all_workout_exercise_ids_exist_in_dataset`
- **Description**: End-to-end grounding check using the real `exercises.json` dataset (50 exercises). `build_workout_tool` is called with 5 real exercise IDs; the resulting `warmup + main + cooldown` are flattened and every `id` must exist in `_VALID_IDS` (the set of all IDs from `exercises.json`). This is the critical assertion that cooldown never emits invented IDs.
- **Steps**:
  1. Run the critical generator test suite:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_critical_generator.py -v
  ```
- **Expected Result**: All tests in `test_agents_critical_generator.py` pass, including `test_all_workout_exercise_ids_exist_in_dataset`. No cooldown entry produces an ID absent from `exercises.json`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-INT-002: Full test_agents_generator.py suite passes (no regressions)

- **Test file**: `backend/tests/test_agents_generator.py`
- **Description**: Run the complete generator test module to confirm the new cooldown tests are additive and no existing tests regress.
- **Steps**:
  1. Run all generator unit tests:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_generator.py -v
  ```
- **Expected Result**: All tests pass. The output includes `test_build_workout_tool_emits_non_empty_cooldown PASSED` and `test_build_workout_tool_empty_cooldown_when_no_recovery_exercises PASSED` alongside the pre-existing tests.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-INT-003: Both test files pass together (full suite run)

- **Test files**: `backend/tests/test_agents_generator.py` + `backend/tests/test_agents_critical_generator.py`
- **Description**: Run both files together as specified in the task's Step 4 verification command. This confirms the new cooldown tests and the critical grounding assertions all co-exist without interference.
- **Steps**:
  1. Run the combined suite:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -m pytest tests/test_agents_generator.py tests/test_agents_critical_generator.py -q
  ```
- **Expected Result**: All tests pass with `0 errors, 0 failures`. The `-q` output ends with a summary line like `N passed in Xs`.
- [x] Pass <!-- 2026-06-07 -->

---

## Edge Case Tests

### UAT-EDGE-001: _select_cooldown_exercises pattern matching is substring-based

- **Description**: Verifies that the `_COOLDOWN_PATTERNS = ["regen", "mobility - static", "mobility - dynamic"]` filtering uses substring matching (via `_matches_movement_patterns_local`), so an exercise with `movement_patterns=["mobility - static stretch"]` would still qualify as a cooldown candidate.
- **Scenario**: A cache entry whose `movement_patterns` value contains `"mobility - static"` as a substring (not an exact match) is correctly selected as a cooldown candidate and not rejected.
- **Steps**:
  1. This is verified by the substring-match implementation in `_matches_movement_patterns_local`. Confirm by adding a one-off assertion inline to UAT-UNIT-001's test setup OR by running the test module with `-s` to observe no exclusion.
  2. As a targeted check, inspect the `_matches_movement_patterns_local` function body to confirm `any(p in searchable for p in patterns_lower)`:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -c "from app.agents.workout_generator import _matches_movement_patterns_local; from unittest.mock import MagicMock; e=MagicMock(); e.movement_patterns=['mobility - static stretch']; print(_matches_movement_patterns_local(e, ['mobility - static']))"
  ```
- **Expected Result**: Prints `True` — substring matching is confirmed.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-EDGE-002: Cooldown count is capped at 2 exercises

- **Description**: Verifies that `_select_cooldown_exercises` returns at most `count=2` exercises even when 3+ recovery-tagged exercises exist in the cache.
- **Scenario**: Cache has 3 regen exercises; cooldown should include exactly 2 (the two with lowest `priority_tier`).
- **Steps**:
  1. Run a focused Python snippet that populates the cache with 3 regen exercises and calls `_select_cooldown_exercises`:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -c "
import uuid; from unittest.mock import MagicMock; from app.agents import exercises as ex_module; from app.agents.workout_generator import _select_cooldown_exercises
def mk(n, pt): e=MagicMock(); e.id=uuid.uuid4(); e.movement_patterns=['regen']; e.priority_tier=pt; e.name=n; return e
ex_module._cache=[mk('R1',1),mk('R2',2),mk('R3',3)]; result=_select_cooldown_exercises(exclude_ids=set()); ex_module._cache=[]; print(len(result), [x.name for x in result])
"
  ```
- **Expected Result**: Prints `2 ['R1', 'R2']` — exactly 2 exercises, prioritised by lowest `priority_tier` (tier 1 and 2, not tier 3).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-EDGE-003: Cooldown excludes exercises already in warmup/main

- **Description**: Verifies that if a regen-tagged exercise ID happens to already appear in warmup or main, it is excluded from cooldown.
- **Scenario**: A single regen exercise is both in `exercise_ids` (so it lands in warmup/main) and in the cache — the cooldown must be empty because the only candidate is excluded.
- **Steps**:
  1. Run a focused Python snippet:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source .env && set +a && .venv/bin/python -c "
import uuid; from unittest.mock import MagicMock; from app.agents import exercises as ex_module; from app.agents.workout_generator import build_workout_tool
uid='cccccccc-0000-0000-0000-000000000001'; e=MagicMock(); e.id=uuid.UUID(uid); e.name='Stretch'; e.movement_patterns=['regen']; e.is_reps=False; e.is_duration=True; e.supports_weight=False; e.priority_tier=2
ex_module._cache=[e]
result=build_workout_tool.invoke({'goal':'cooldown only','exercise_ids':[uid],'sets':3,'rest_seconds':90})
ex_module._cache=[]
print('cooldown:', result['phases']['cooldown'])
"
  ```
- **Expected Result**: Prints `cooldown: []` — the only regen exercise was used in main (since `len(valid) < 3`, warmup is empty and main contains the single exercise), so `exclude_ids` includes it and cooldown is empty.
- [x] Pass <!-- 2026-06-07 -->

---
**UAT**: [`.docs/uat/088-build-workout-cooldown-phase.uat.md`](../uat/088-build-workout-cooldown-phase.uat.md)
