# UAT: Critical-Path Test 1 — Injury Filtering Correctness

> **Source task**: [`.docs/tasks/completed/068-critical-path-test-injury-filtering.md`](../tasks/completed/068-critical-path-test-injury-filtering.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] `backend/` virtualenv is active (or `cd backend && source .venv/bin/activate`)
- [ ] `backend/tests/test_kg_critical_injury_filtering.py` exists

---

## Unit Test Suite

### UAT-UNIT-001: All 5 Parameterized Cases Pass

- **Description**: Run the full parameterized test suite and confirm every case exits green — contraindicated exercises are never present in generation output and always appear in `skipped_exercise_ids`.
- **Steps**:
  1. From the repo root, run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_kg_critical_injury_filtering.py -v
  ```
- **Expected Result**: `5 passed` with no failures. Output should list all 5 parameterized variants each marked `PASSED`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Single Contraindicated Exercise Removed

- **Scenario**: LLM returns one safe exercise and one contraindicated exercise (`ex-bad-1`); only the safe exercise survives.
- **Steps**:
  1. Run the targeted parametrize case below (matches case index 0)
- **Command**:
  ```bash
  cd backend && python -m pytest "tests/test_kg_critical_injury_filtering.py::test_contraindicated_exercises_never_in_output[contraindicated0-llm_picks0-expected_safe0-expected_skipped0]" -v
  ```
- **Expected Result**: `1 passed`. `ex-bad-1` absent from `rec.exercises`; `ex-bad-1` present in `rec.skipped_exercise_ids`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Multiple Contraindicated Exercises All Removed

- **Scenario**: LLM returns one safe and two contraindicated (`ex-bad-1`, `ex-bad-2`); both contraindicated are stripped.
- **Steps**:
  1. Run the targeted parametrize case below (matches case index 1)
- **Command**:
  ```bash
  cd backend && python -m pytest "tests/test_kg_critical_injury_filtering.py::test_contraindicated_exercises_never_in_output[contraindicated1-llm_picks1-expected_safe1-expected_skipped1]" -v
  ```
- **Expected Result**: `1 passed`. Both `ex-bad-1` and `ex-bad-2` absent from output exercises; both in `skipped_exercise_ids`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: No Contraindicated Exercises — Recommendation Unchanged

- **Scenario**: Empty contraindicated set; all LLM picks pass through unmodified.
- **Steps**:
  1. Run the targeted parametrize case below (matches case index 2)
- **Command**:
  ```bash
  cd backend && python -m pytest "tests/test_kg_critical_injury_filtering.py::test_contraindicated_exercises_never_in_output[contraindicated2-llm_picks2-expected_safe2-expected_skipped2]" -v
  ```
- **Expected Result**: `1 passed`. Both `ex-safe-1` and `ex-safe-2` present in output; `skipped_exercise_ids` is empty.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-004: All Exercises Contraindicated — Fallback Triggered

- **Scenario**: Every exercise the LLM picks is contraindicated; safety gate filters all of them and triggers fallback, producing empty or fallback exercises list.
- **Steps**:
  1. Run the targeted parametrize case below (matches case index 3)
- **Command**:
  ```bash
  cd backend && python -m pytest "tests/test_kg_critical_injury_filtering.py::test_contraindicated_exercises_never_in_output[contraindicated3-llm_picks3-expected_safe3-expected_skipped3]" -v
  ```
- **Expected Result**: `1 passed`. No contraindicated IDs (`ex-safe-1`, `ex-safe-2`, `ex-safe-3`) appear in output exercises; `ex-safe-1` is in `skipped_exercise_ids`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-005: Contraindicated Exercise in Preferred List Still Removed

- **Scenario**: An exercise that was preferred by the member (`ex-preferred`) is also contraindicated; it must still be stripped by the safety gate.
- **Steps**:
  1. Run the targeted parametrize case below (matches case index 4)
- **Command**:
  ```bash
  cd backend && python -m pytest "tests/test_kg_critical_injury_filtering.py::test_contraindicated_exercises_never_in_output[contraindicated4-llm_picks4-expected_safe4-expected_skipped4]" -v
  ```
- **Expected Result**: `1 passed`. `ex-preferred` absent from output exercises; `ex-preferred` present in `skipped_exercise_ids`; `ex-safe-1` present in output exercises.
- [x] Pass <!-- 2026-06-06 -->
