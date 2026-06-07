# 088 — Populate Cooldown Phase in build_workout Tool

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [086-readme-kg-production-eval](086-readme-kg-production-eval.md), [087-fix-stale-intent-values-test](087-fix-stale-intent-values-test.md)

## Objective

Make `build_workout_tool` in `backend/app/agents/workout_generator.py` emit a non-empty `cooldown` phase of low-intensity stretch/mobility movements drawn from the exercise dataset, so generated workouts satisfy the Assessment 1 & 2 requirement of warmup/main/cooldown phases each with sets/reps/rest.

## Approach

Select cooldown candidates from the in-memory exercise cache by matching the dataset's recovery signal — `movement_patterns` values containing `"regen"`, `"mobility - static"`, or `"mobility - dynamic"` (these entries are `is_duration: true`, `is_reps: false`, `priority_tier: 2`) — preferring lower `priority_tier`, then append a small slice (2-3) of these as the `cooldown` list using the existing per-exercise dict shape. Cooldown exercises are chosen independently of the LLM-provided `exercise_ids` but MUST be real dataset IDs (so the critical-path "only real IDs" assertions still hold), and any already present in warmup/main are skipped to avoid duplication.

## Prerequisites

- [ ] Read `backend/app/agents/workout_generator.py` — confirm current `build_workout_tool` body (lines ~82-119): `warmup = valid[:2]`, `main = valid[2:]`, `cooldown: list[dict[str, Any]] = []` (always empty), and the inner `exercise_to_dict(e)` helper producing `{id, name, sets, reps, duration_s, rest_s}`.
- [ ] Read `backend/app/agents/exercises.py` — note `get_all_exercises()` (returns `list(_cache)`), `search_exercises(...)` (already substring-matches via `_matches_movement_patterns`, sorts by `priority_tier` ascending), and that `search_exercises` is imported into `workout_generator.py` as `_search_exercises`.
- [ ] Confirm the cooldown data signal in `.docs/guides/1-multi-agent/exercises.json`: 6 entries have `movement_patterns` containing `"regen"` (e.g. "Ground Upper Trap Stretch" `0a9d8d01-a52d-453e-92bc-dd9238e9a930`, "World's Greatest Stretch" `0a4d99cf-5075-468e-9551-b9f8efa267f1`, "Walking Toe Touches" `1423ff58-68de-47da-8884-cb6f438f5774`); these are `is_duration: true`, `is_reps: false`.

---

## Steps

### 1. Add a cooldown-candidate selector  <!-- agent: general-purpose -->

- [ ] In `backend/app/agents/workout_generator.py`, add a small module-level helper (e.g. `_select_cooldown_exercises(exclude_ids: set[str], count: int = 2) -> list`) that returns dataset exercises suitable for a cooldown.
  - Source candidates from the existing cache helpers — call `_search_exercises(movement_patterns=["regen", "mobility"], max_results=...)` (it already substring-matches `movement_patterns` and sorts by `priority_tier` ascending) and/or filter `get_all_exercises()` for movement_patterns containing `"regen"`, `"mobility - static"`, or `"mobility - dynamic"`.
  - Exclude any exercise whose `str(e.id)` is in `exclude_ids` (the IDs already placed in warmup/main) so cooldown does not duplicate earlier phases.
  - Prefer lower `priority_tier` (the search helper already sorts this way); return at most `count` exercises. If no recovery-tagged exercises exist in the cache, return `[]` (graceful no-op, never raise).

### 2. Populate the cooldown list in build_workout_tool  <!-- agent: general-purpose -->

- [ ] In `build_workout_tool`, replace the `cooldown: list[dict[str, Any]] = []` placeholder so cooldown is built from `_select_cooldown_exercises(...)`.
  - Pass `exclude_ids = {str(e.id) for e in warmup + main}` so the cooldown picks distinct exercises.
  - Render each selected cooldown exercise through the existing `exercise_to_dict(...)` helper so the dict shape (`id`, `name`, `sets`, `reps`, `duration_s`, `rest_s`) stays consistent with warmup/main; cooldown entries should be low intensity — keep `sets` modest (e.g. `1`) and `rest_s` short (e.g. `30`) rather than the strength `sets`/`rest_seconds` defaults. Because cooldown stretches are `is_duration: true`/`is_reps: false`, `exercise_to_dict` already yields `duration_s` set and `reps: None`.
  - Build the cooldown dicts BEFORE the `return {...}` and assign into `phases["cooldown"]`; leave `warmup`/`main` selection and `total_exercises`/`invalid_ids_skipped` behavior unchanged.
  - Acceptance note: cooldown IDs must all exist in the dataset (they come from the cache, so this holds), and must not overlap warmup/main IDs.

### 3. Tests  <!-- agent: general-purpose -->

- [ ] Add a test to `backend/tests/test_agents_generator.py` asserting `build_workout_tool` returns a NON-EMPTY `cooldown` phase for a normal request.
  - The existing autouse `populate_exercise_cache` fixture stubs `_cache` with a SINGLE MagicMock that has no recovery movement_patterns, so it cannot exercise cooldown — give the new test its own cache. Either extend/override the fixture or set `app.agents.exercises._cache` inside the test to several MagicMock exercises that include at least one with `movement_patterns = ["regen"]` (or `["mobility - static"]`), `is_duration = True`, `is_reps = False`, plus a couple of normal `is_reps = True` strength exercises for warmup/main; restore `_cache = []` afterward (mirror the existing fixture teardown).
  - Assert: `result["phases"]["cooldown"]` is non-empty; every cooldown entry has an `id` present in the stubbed cache; and no cooldown `id` also appears in `warmup`/`main`.
- [ ] Confirm `backend/tests/test_agents_critical_generator.py` still passes — its `_all_phase_exercises(...)` already flattens `cooldown`, and its assertions require every phase exercise ID to be in `_VALID_IDS` (the real dataset), which the cache-sourced cooldown satisfies.

### 4. Verification  <!-- agent: general-purpose -->

- [ ] Run the relevant pytest with the backend venv and confirm pass: `set -a && source .env && set +a` then `backend/.venv/bin/python -m pytest backend/tests/test_agents_generator.py backend/tests/test_agents_critical_generator.py -q` (run from the `backend/` directory).

## Acceptance Criteria

- [ ] `build_workout_tool` returns `phases.cooldown` as a NON-EMPTY list for a normal request that yields a populated warmup/main.
- [ ] Every cooldown entry references a valid dataset exercise ID (sourced from the cache / `exercises.json`); no invented IDs.
- [ ] Cooldown entries use the same dict shape as warmup/main (`id`, `name`, `sets`, `reps`, `duration_s`, `rest_s`) and are low-intensity (modest `sets`, short `rest_s`), with no ID overlapping warmup or main.
- [ ] When the cache contains no recovery/mobility-tagged exercises, `build_workout_tool` returns an empty `cooldown` without raising.
- [ ] New test in `test_agents_generator.py` asserts a non-empty cooldown; `test_agents_generator.py` and `test_agents_critical_generator.py` both pass.

---
**UAT**: [`.docs/uat/088-build-workout-cooldown-phase.uat.md`](../uat/088-build-workout-cooldown-phase.uat.md)
