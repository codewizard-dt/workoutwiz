# 038 — Annotate schemas/workout.py with OpenAPI Field metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md), [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md)

## Objective

Add `Field(description=..., example=...)` to every field across all six classes in `backend/app/schemas/workout.py` (`WorkoutSetCreate`, `WorkoutSequenceCreate`, `WorkoutCreate`, `WorkoutSetRead`, `WorkoutSequenceRead`, `WorkoutRead`) so the Swagger UI shows rich per-field documentation for all workout endpoints.

## Approach

Use Pydantic v2 `Field(description=..., example=...)`. `WorkoutSetRead` inherits from `WorkoutSetCreate`, so inherited fields are annotated on the parent. All six classes need annotations — including the two new id/foreign-key fields added by the Read variants. Keep all defaults (e.g. `position: int = 0`) intact by passing them through `Field(default=0, description=...)`.

## Steps

### 1. Annotate all workout schema fields  <!-- agent: general-purpose -->

Edit `backend/app/schemas/workout.py`:

- Import `Field` from `pydantic`.
- Annotate every field in each class as described below. Where a default exists, use `Field(default=<val>, description=..., example=...)`.

**WorkoutSetCreate** (lines 6–15):

| Field | Description | Example |
|-------|-------------|---------|
| `exercise_id` | UUID of the exercise being performed | `"a1b2c3d4-..."` |
| `set_type` | Tracking type — STRENGTH (reps/weight) or CARDIO (duration/distance) | `"STRENGTH"` |
| `position` | Zero-based ordering within the sequence | `0` |
| `reps` | Number of repetitions (null for cardio sets) | `10` |
| `weight_kg` | Load in kilograms (null if bodyweight) | `100.0` |
| `duration_s` | Duration in seconds (null for strength sets) | `null` |
| `speed` | Speed in km/h (null if not tracked) | `null` |
| `distance` | Distance in km (null if not tracked) | `null` |
| `calories` | Calories burned estimate (null if not tracked) | `null` |

**WorkoutSequenceCreate** (lines 18–21):

| Field | Description | Example |
|-------|-------------|---------|
| `phase` | Workout phase — warmup, main, or cooldown | `"main"` |
| `position` | Zero-based ordering of this sequence within the workout | `0` |
| `sets` | Ordered list of sets in this sequence | `[]` |

**WorkoutCreate** (lines 24–27):

| Field | Description | Example |
|-------|-------------|---------|
| `started_at` | ISO 8601 timestamp when the workout began | `"2026-06-05T09:00:00Z"` |
| `ended_at` | ISO 8601 timestamp when the workout ended (null if in progress) | `null` |
| `sequences` | Ordered list of exercise sequences (warmup/main/cooldown) | `[]` |

**WorkoutSetRead** — only the two new fields not inherited from `WorkoutSetCreate` (lines 30–33):

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique set identifier (UUID) | `"b2c3d4e5-..."` |
| `sequence_id` | UUID of the parent sequence | `"c3d4e5f6-..."` |

**WorkoutSequenceRead** (lines 36–42):

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique sequence identifier (UUID) | `"d4e5f6a7-..."` |
| `workout_id` | UUID of the parent workout | `"e5f6a7b8-..."` |
| `phase` | Workout phase — warmup, main, or cooldown | `"main"` |
| `position` | Zero-based ordering within the workout | `0` |
| `sets` | Ordered list of sets in this sequence | `[]` |

**WorkoutRead** (lines 45–51):

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique workout identifier (UUID) | `"f6a7b8c9-..."` |
| `user_id` | UUID of the user who owns this workout | `"a7b8c9d0-..."` |
| `started_at` | ISO 8601 timestamp when the workout began | `"2026-06-05T09:00:00Z"` |
| `ended_at` | ISO 8601 timestamp when the workout ended (null if in progress) | `null` |
| `sequences` | Ordered list of exercise sequences | `[]` |

- [x] `Field` is imported from `pydantic`
- [x] All fields in `WorkoutSetCreate` have `description=` and `example=`
- [x] All fields in `WorkoutSequenceCreate` have `description=` and `example=`
- [x] All fields in `WorkoutCreate` have `description=` and `example=`
- [x] New fields in `WorkoutSetRead` have `description=` and `example=`
- [x] All fields in `WorkoutSequenceRead` have `description=` and `example=`
- [x] All fields in `WorkoutRead` have `description=` and `example=`
- [x] All existing defaults are preserved via `Field(default=..., description=..., example=...)`
- [x] File is valid Python (no syntax errors) <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/schemas/workout.py` imports `Field` from `pydantic`
- [x] Running `python -c "from app.schemas.workout import WorkoutRead; import json; s=WorkoutRead.model_json_schema(); print(json.dumps(s, indent=2))"` from `backend/` produces JSON where every property (recursive) has a `description` key
- [ ] No existing tests are broken

---
**UAT**: [`.docs/uat/038-annotate-schemas-workout.uat.md`](../uat/038-annotate-schemas-workout.uat.md)
