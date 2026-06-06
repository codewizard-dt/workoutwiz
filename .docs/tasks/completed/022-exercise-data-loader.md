# 022 — Exercise Data Loader

> **Depends on**: [019-python-package-setup](019-python-package-setup.md)
> **Blocks**: none
> **Parallel-safe with**: [020-install-core-dependencies](020-install-core-dependencies.md), [021-shared-state-and-route-schema](021-shared-state-and-route-schema.md)

## Objective

Implement the exercise data loader that reads `exercises.json` into memory once at startup and exposes typed accessors used by the Workout Generator and Workout Logger sub-agents. This is the sole data source for all exercise lookups — no database, no external API.

## Approach

The loader is a module-level singleton in `src/workout_wiz/exercises.py`. It reads `1-multi-agent/exercises.json` relative to the package root at import time using `importlib.resources` (Python 3.9+ standard). The public API is three functions: `get_all_exercises()`, `get_exercise_by_id(uuid)`, and `search_exercises(muscle_groups, equipment, movement_patterns)` — the last one is what the `search_exercises` LangGraph tool will call.

Key fields from the JSON schema (from CLAUDE.md):
- `id` (UUID), `name`, `muscle_groups` (list), `movement_patterns` (list), `equipment_required` (list)
- `is_reps`, `is_duration`, `supports_weight` (booleans — tracking field validation)
- `priority_tier` (int 1–3), `is_bilateral`, `bilateral_pair_id`

## Steps

### 1. Create Exercise Pydantic model  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/models.py` with the Exercise model:

```python
from pydantic import BaseModel


class Exercise(BaseModel):
    id: str
    name: str
    muscle_groups: list[str]
    movement_patterns: list[str]
    equipment_required: list[str]
    is_reps: bool
    is_duration: bool
    supports_weight: bool
    priority_tier: int
    is_bilateral: bool
    bilateral_pair_id: str | None = None

    # Allow extra fields from the JSON without validation errors
    model_config = {"extra": "ignore"}
```

- [ ] `src/workout_wiz/models.py` exists with `Exercise` Pydantic model
- [ ] All fields from the JSON schema are present
- [ ] `extra = "ignore"` so unexpected JSON keys don't raise errors

### 2. Create the data loader module  <!-- agent: general-purpose -->

Create `1-multi-agent/src/workout_wiz/exercises.py`:

```python
import json
from pathlib import Path
from functools import lru_cache

from workout_wiz.models import Exercise

# Resolve path to exercises.json — it sits two levels above this file's package root
_EXERCISES_PATH = Path(__file__).parent.parent.parent.parent / "exercises.json"


@lru_cache(maxsize=1)
def _load_exercises() -> list[Exercise]:
    with open(_EXERCISES_PATH) as f:
        raw = json.load(f)
    return [Exercise.model_validate(item) for item in raw]


def get_all_exercises() -> list[Exercise]:
    return _load_exercises()


def get_exercise_by_id(exercise_id: str) -> Exercise | None:
    return next((e for e in _load_exercises() if e.id == exercise_id), None)


def search_exercises(
    muscle_groups: list[str] | None = None,
    equipment: list[str] | None = None,
    movement_patterns: list[str] | None = None,
    max_results: int = 10,
) -> list[Exercise]:
    """Filter exercises by any combination of muscle groups, equipment, or movement patterns.

    Matching is case-insensitive substring. Returns up to max_results exercises,
    sorted by priority_tier ascending (tier 1 = highest priority first).
    """
    results = _load_exercises()

    if muscle_groups:
        mg_lower = [m.lower() for m in muscle_groups]
        results = [
            e for e in results
            if any(m.lower() in " ".join(e.muscle_groups).lower() for m in mg_lower)
        ]

    if equipment:
        eq_lower = [eq.lower() for eq in equipment]
        results = [
            e for e in results
            if any(eq.lower() in " ".join(e.equipment_required).lower() for eq in eq_lower)
        ]

    if movement_patterns:
        mp_lower = [m.lower() for m in movement_patterns]
        results = [
            e for e in results
            if any(m.lower() in " ".join(e.movement_patterns).lower() for m in mp_lower)
        ]

    results.sort(key=lambda e: e.priority_tier)
    return results[:max_results]
```

Note: The path resolution `Path(__file__).parent.parent.parent.parent / "exercises.json"` resolves from `src/workout_wiz/exercises.py` → `src/workout_wiz/` → `src/` → `1-multi-agent/` → `exercises.json`. Verify this is correct relative to the actual file location.

- [ ] `src/workout_wiz/exercises.py` exists
- [ ] `_load_exercises()` is cached with `lru_cache`
- [ ] `search_exercises()` filters by all three dimensions with case-insensitive matching
- [ ] Results sorted by `priority_tier` ascending

### 3. Write tests  <!-- agent: general-purpose -->

Create `1-multi-agent/tests/test_exercises.py`:

```python
from workout_wiz.exercises import get_all_exercises, get_exercise_by_id, search_exercises


def test_loads_50_exercises():
    exercises = get_all_exercises()
    assert len(exercises) == 50


def test_get_by_id_found():
    exercises = get_all_exercises()
    first = exercises[0]
    found = get_exercise_by_id(first.id)
    assert found is not None
    assert found.id == first.id


def test_get_by_id_not_found():
    assert get_exercise_by_id("00000000-0000-0000-0000-000000000000") is None


def test_search_by_muscle_group():
    results = search_exercises(muscle_groups=["chest"])
    assert len(results) > 0
    assert all("chest" in " ".join(e.muscle_groups).lower() for e in results)


def test_search_max_results():
    results = search_exercises(max_results=3)
    assert len(results) <= 3


def test_search_priority_sort():
    results = search_exercises()
    tiers = [e.priority_tier for e in results]
    assert tiers == sorted(tiers)
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_exercises.py -v`

- [ ] All 6 tests pass

### 4. Verify path resolution  <!-- agent: general-purpose -->

After writing the module, run a quick smoke test to confirm the path resolves correctly:

```bash
cd 1-multi-agent
source .venv/bin/activate
python -c "from workout_wiz.exercises import get_all_exercises; exs = get_all_exercises(); print(f'Loaded {len(exs)} exercises')"
```

- [ ] Output is "Loaded 50 exercises"

## Acceptance Criteria

- [ ] `src/workout_wiz/models.py` contains `Exercise` Pydantic model with all required fields
- [ ] `src/workout_wiz/exercises.py` loads `exercises.json` once (cached) and exposes `get_all_exercises`, `get_exercise_by_id`, `search_exercises`
- [ ] `search_exercises()` filters correctly by muscle group, equipment, and movement pattern
- [ ] All 6 tests in `tests/test_exercises.py` pass
- [ ] "Loaded 50 exercises" confirmed at runtime

---
**UAT**: [`.docs/uat/022-exercise-data-loader.uat.md`](../uat/022-exercise-data-loader.uat.md)
