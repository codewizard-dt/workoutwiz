# UAT: Exercise Data Loader

> **Source task**: [`.docs/tasks/022-exercise-data-loader.md`](../tasks/022-exercise-data-loader.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Working directory is `1-multi-agent/` (all shell commands below are relative to it)
- [ ] Python virtual environment exists at `1-multi-agent/.venv/`
- [ ] `exercises.json` is present in `1-multi-agent/` (50 exercises)
- [ ] `src/workout_wiz/models.py` and `src/workout_wiz/exercises.py` are implemented

---

## Shell Script Tests

These tests invoke the module directly via Python and assert on produced output. No server is required.

### UAT-SHELL-001: Smoke test — loader returns 50 exercises

- **Description**: Verify `get_all_exercises()` loads exactly 50 exercises from `exercises.json` at runtime via a one-liner import.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import get_all_exercises; exs = get_all_exercises(); print(f'Loaded {len(exs)} exercises')"
  ```
- **Expected Result**: Output is exactly `Loaded 50 exercises`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-002: Exercise model fields — all required fields present on loaded objects

- **Description**: Verify `Exercise` Pydantic model has all required fields (`id`, `name`, `muscle_groups`, `movement_patterns`, `equipment_required`, `is_reps`, `is_duration`, `supports_weight`, `priority_tier`, `is_bilateral`, `bilateral_pair_id`) and that `extra="ignore"` silently drops unexpected JSON keys.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import get_all_exercises; e = get_all_exercises()[0]; print(e.id, e.name, e.priority_tier, e.is_reps, e.is_duration, e.supports_weight, e.is_bilateral, e.bilateral_pair_id)"
  ```
- **Expected Result**: Prints a UUID, a name string, an integer tier, three booleans, and either a UUID or `None` — no `ValidationError` is raised. Example: `0b3178cf-bf89-45a3-bfb0-27310ef6ef38 Barbell Decline Bench Press 2 True True True False None`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-003: `get_exercise_by_id` — found

- **Description**: Verify `get_exercise_by_id` returns the correct exercise when given a known UUID.
- **Steps**:
  1. Run the command below (uses the first exercise's known UUID from the dataset).
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import get_exercise_by_id; e = get_exercise_by_id('0b3178cf-bf89-45a3-bfb0-27310ef6ef38'); print(e.name)"
  ```
- **Expected Result**: Output is `Barbell Decline Bench Press`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-004: `get_exercise_by_id` — not found returns None

- **Description**: Verify `get_exercise_by_id` returns `None` for an unknown UUID without raising an exception.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import get_exercise_by_id; result = get_exercise_by_id('00000000-0000-0000-0000-000000000000'); print(result)"
  ```
- **Expected Result**: Output is `None`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-005: `search_exercises` — filter by muscle group (chest)

- **Description**: Verify `search_exercises(muscle_groups=["chest"])` returns only exercises whose `muscle_groups` list contains "chest" (case-insensitive substring match). Dataset has 5 chest exercises.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(muscle_groups=['chest']); print(len(results)); print(all('chest' in ' '.join(e.muscle_groups).lower() for e in results))"
  ```
- **Expected Result**: First line is `5` (or `10` if dataset grows beyond default max, but currently ≤ 5). Second line is `True`. Both conditions must hold — no non-chest exercise appears.
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-006: `search_exercises` — filter by equipment (dumbbell)

- **Description**: Verify `search_exercises(equipment=["dumbbell"])` returns only exercises whose `equipment_required` list contains "dumbbell" (case-insensitive substring). Dataset has 9 such exercises.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(equipment=['dumbbell']); print(len(results)); print(all('dumbbell' in ' '.join(e.equipment_required).lower() for e in results))"
  ```
- **Expected Result**: First line is `9`. Second line is `True`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-007: `search_exercises` — filter by movement pattern (vertical)

- **Description**: Verify `search_exercises(movement_patterns=["vertical"])` returns only exercises whose `movement_patterns` list contains "vertical" (case-insensitive substring). Dataset has 5 such exercises.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(movement_patterns=['vertical']); print(len(results)); print(all('vertical' in ' '.join(e.movement_patterns).lower() for e in results))"
  ```
- **Expected Result**: First line is `5`. Second line is `True`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-008: `search_exercises` — combined filter (chest + barbell)

- **Description**: Verify that combining `muscle_groups` and `equipment` filters applies both (logical AND). Dataset has exactly 1 exercise that is both chest and barbell.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(muscle_groups=['chest'], equipment=['barbell']); print(len(results)); print(results[0].name)"
  ```
- **Expected Result**: First line is `1`. Second line is `Barbell Decline Bench Press`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-009: `search_exercises` — max_results cap

- **Description**: Verify `search_exercises(max_results=3)` returns no more than 3 results regardless of how many exercises match.
- **Steps**:
  1. Run the command below (no filter, all 50 exercises match, capped at 3).
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(max_results=3); print(len(results))"
  ```
- **Expected Result**: Output is `3`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-010: `search_exercises` — results sorted by priority_tier ascending

- **Description**: Verify returned results are sorted by `priority_tier` ascending (tier 1 = highest priority first). All current exercises are tier 2, so the list must be non-descending (i.e., sorted ascending), which must hold even if tiers were mixed.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(); tiers = [e.priority_tier for e in results]; print(tiers == sorted(tiers))"
  ```
- **Expected Result**: Output is `True`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-011: `search_exercises` — empty filter returns all exercises (up to max_results default)

- **Description**: Verify calling `search_exercises()` with no filters returns up to 10 exercises (the default `max_results`).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(); print(len(results))"
  ```
- **Expected Result**: Output is `10`
- [x] Pass <!-- 2026-06-05 -->

### UAT-SHELL-012: `_load_exercises` is cached — identical object returned on second call

- **Description**: Verify the `lru_cache` on `_load_exercises` means repeated calls return the same list object (not re-parsed from disk).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import get_all_exercises; a = get_all_exercises(); b = get_all_exercises(); print(a is b)"
  ```
- **Expected Result**: Output is `True` (same object in memory — not a re-read)
- [x] Pass <!-- 2026-06-05 -->

---

## Unit Test Suite

### UAT-TEST-001: All 6 pytest tests pass

- **Description**: Verify all six unit tests in `tests/test_exercises.py` pass without error. Tests cover: 50-exercise count, get-by-id found, get-by-id not-found, search by muscle group, max_results, and priority sort.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_exercises.py -v
  ```
- **Expected Result**: All 6 tests pass — output ends with `6 passed`. No errors or failures.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: `search_exercises` — no matches returns empty list

- **Description**: Verify that a search with a filter that matches no exercises returns an empty list rather than raising an exception.
- **Steps**:
  1. Run the command below using a nonsense muscle group name that matches no exercise.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; results = search_exercises(muscle_groups=['zzz_nonexistent_muscle']); print(type(results).__name__, len(results))"
  ```
- **Expected Result**: Output is `list 0`
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: `get_exercise_by_id` — case-sensitive UUID (exact match required)

- **Description**: Verify that `get_exercise_by_id` requires exact UUID string match. An uppercase version of a known UUID should return `None`.
- **Steps**:
  1. Run the command below (uses uppercase version of a known UUID).
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import get_exercise_by_id; result = get_exercise_by_id('0B3178CF-BF89-45A3-BFB0-27310EF6EF38'); print(result)"
  ```
- **Expected Result**: Output is `None` (UUIDs in the dataset are lowercase; the match is string-exact, not case-folded)
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: `search_exercises` — case-insensitive matching (uppercase input)

- **Description**: Verify that `search_exercises` normalises filter values to lowercase before matching, so "CHEST" finds the same exercises as "chest".
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.exercises import search_exercises; a = search_exercises(muscle_groups=['chest']); b = search_exercises(muscle_groups=['CHEST']); print(len(a), len(b), len(a) == len(b))"
  ```
- **Expected Result**: Both counts are equal and non-zero, e.g. `5 5 True`
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: `Exercise` model — extra JSON fields silently ignored

- **Description**: Verify the `extra="ignore"` config means fields present in the JSON but not declared in the model (e.g., `joints_loaded`, `side`, `estimated_rep_duration`) do not cause a `ValidationError`.
- **Steps**:
  1. Run the command below. The exercise JSON includes `joints_loaded`, `side`, and `estimated_rep_duration` — none of which are in the model.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.models import Exercise; e = Exercise.model_validate({'id':'abc','name':'X','muscle_groups':[],'movement_patterns':[],'equipment_required':[],'is_reps':True,'is_duration':False,'supports_weight':False,'priority_tier':1,'is_bilateral':False,'extra_unknown_field':'should_be_ignored'}); print('ok', hasattr(e, 'extra_unknown_field'))"
  ```
- **Expected Result**: Output is `ok False` — the model validates without error and the extra field is not accessible as an attribute.
- [x] Pass <!-- 2026-06-05 -->
