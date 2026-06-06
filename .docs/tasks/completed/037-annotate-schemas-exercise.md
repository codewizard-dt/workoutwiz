# 037 — Annotate schemas/exercise.py with OpenAPI Field metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md)

## Objective

Add `Field(description=..., example=...)` annotations to every field in `ExerciseRead` (and any filter-param schemas) in `backend/app/schemas/exercise.py` so the Swagger UI at `/docs` shows rich per-field documentation without any manual route-level schema overrides.

## Approach

Use Pydantic v2 `Field(description=..., example=...)` on every field of `ExerciseRead`. The `ExerciseRead` class is the sole exercise schema — there are no separate filter schemas in `schemas/exercise.py`; exercise filters are inline query params on the router. Enrich all fields with human-readable descriptions and representative example values matching the exercises.json dataset.

## Steps

### 1. Annotate ExerciseRead fields  <!-- agent: general-purpose -->

Edit `backend/app/schemas/exercise.py`:

- Import `Field` from `pydantic` alongside the existing `BaseModel` import.
- Annotate every field in `ExerciseRead` with `Field(description=..., example=...)`:

  | Field | Description | Example |
  |-------|-------------|---------|
  | `id` | Unique exercise identifier (UUID) | `"a1b2c3d4-..."` |
  | `name` | Human-readable exercise name | `"Barbell Back Squat"` |
  | `category` | Broad exercise category (e.g. Strength, Cardio) | `"Strength"` |
  | `muscle_groups` | Primary and secondary muscles targeted | `["Quadriceps", "Glutes"]` |
  | `equipment_required` | Equipment needed to perform the exercise | `["Barbell", "Squat Rack"]` |
  | `movement_patterns` | Fundamental movement patterns | `["Squat", "Bilateral"]` |
  | `is_reps` | Whether the exercise is tracked by repetition count | `true` |
  | `is_duration` | Whether the exercise is tracked by time duration | `false` |
  | `supports_weight` | Whether weight can be added to this exercise | `true` |
  | `is_bilateral` | Whether the exercise works both sides simultaneously | `true` |
  | `bilateral_pair_id` | UUID of the paired unilateral variant, if any | `null` |
  | `priority_tier` | Programming priority (1 = highest quality) | `1` |
  | `description` | Optional longer description of the exercise | `"A compound lower-body movement..."` |

- Keep `model_config = {"from_attributes": True}` unchanged.

- [x] `Field` is imported from `pydantic`
- [x] All 13 fields have `description=` set
- [x] All 13 fields have `example=` set with a realistic value
- [x] `model_config` is unchanged
- [x] File is valid Python (no syntax errors)

## Acceptance Criteria

- [x] `backend/app/schemas/exercise.py` imports `Field` from `pydantic`
- [x] Every field in `ExerciseRead` uses `Field(description=..., example=...)`
- [x] Running `python -c "from app.schemas.exercise import ExerciseRead; print(ExerciseRead.model_json_schema())"` from `backend/` prints a JSON schema where every property has a `description` key
- [x] No existing tests are broken (the schema change is backwards-compatible — `Field` metadata is additive)

---
**UAT**: [`.docs/uat/037-annotate-schemas-exercise.uat.md`](../uat/037-annotate-schemas-exercise.uat.md)
