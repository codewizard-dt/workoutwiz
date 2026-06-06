# UAT: Feedback Write-Back — Persist Post-Workout Ratings to Graph

> **Source task**: [`.docs/tasks/064-feedback-writeback.md`](../tasks/064-feedback-writeback.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Python environment activated (e.g. `source .venv/bin/activate` inside `backend/`)
- [ ] `.env` present and loadable (used by `set -a && source .env && set +a`)
- [ ] Neo4j not required — all tests mock the driver
- [ ] `backend/app/schemas/kg.py` exists with `FeedbackPayload`, `KGRecommendRequest`, `KGExplainRequest`
- [ ] `backend/app/kg/feedback_service.py` exists with `write_feedback(payload, driver) -> str`
- [ ] `backend/tests/kg/test_feedback_service.py` exists

---

## Unit Tests

These tests exercise the service function and schema directly via `pytest` — no running server or Neo4j instance required.

### UAT-UNIT-001: Full pytest suite for feedback service

- **Description**: Run all five unit tests in `test_feedback_service.py` to verify `write_feedback` calls the Neo4j session correctly, returns a valid UUID, and returns unique IDs across calls.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py -v
  ```
- **Expected Result**: All 5 tests collected and pass (`PASSED`). Output includes:
  - `test_write_feedback_calls_ingestion PASSED`
  - `test_write_feedback_writes_correct_cypher_queries PASSED`
  - `test_write_feedback_returns_unique_ids PASSED`
  - `test_feedback_payload_validates_rating_range PASSED`
  - `test_feedback_payload_optional_fields PASSED`
  - No warnings about missing neo4j driver or missing env vars
- [ ] Pass

### UAT-UNIT-002: `write_feedback` executes a Neo4j write transaction

- **Description**: Verify that `write_feedback` calls `session.execute_write` exactly once, confirming the Cypher write path is invoked (not a dry-run).
- **Steps**:
  1. Run the targeted test below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py::test_write_feedback_calls_ingestion -v
  ```
- **Expected Result**: `test_write_feedback_calls_ingestion PASSED` — `execute_write` was called once and the return value is a valid UUID string.
- [ ] Pass

### UAT-UNIT-003: `write_feedback` returns distinct UUIDs on each invocation

- **Description**: Two separate calls to `write_feedback` with the same payload must return different IDs, proving each call creates a new node rather than upserting.
- **Steps**:
  1. Run the targeted test below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py::test_write_feedback_returns_unique_ids -v
  ```
- **Expected Result**: `test_write_feedback_returns_unique_ids PASSED` — `id1 != id2`.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: `FeedbackPayload.rating` rejects values outside 1–5

- **Description**: The `rating` field uses `Field(ge=1, le=5)`. Values of 0 and 6 must raise `pydantic.ValidationError`; boundary values 1 and 5 must be accepted.
- **Steps**:
  1. Run the targeted test below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py::test_feedback_payload_validates_rating_range -v
  ```
- **Expected Result**: `test_feedback_payload_validates_rating_range PASSED`. Specifically:
  - `FeedbackPayload(member_id="m1", exercise_id="e1", rating=0)` raises `ValidationError`
  - `FeedbackPayload(member_id="m1", exercise_id="e1", rating=6)` raises `ValidationError`
  - `FeedbackPayload(member_id="m1", exercise_id="e1", rating=1).rating == 1`
  - `FeedbackPayload(member_id="m1", exercise_id="e1", rating=5).rating == 5`
- [ ] Pass

### UAT-EDGE-002: `FeedbackPayload` optional fields default correctly

- **Description**: `text`, `workout_session_id` are optional (default `None`) and `context_type` defaults to `"post_workout"` when not supplied.
- **Steps**:
  1. Run the targeted test below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py::test_feedback_payload_optional_fields -v
  ```
- **Expected Result**: `test_feedback_payload_optional_fields PASSED`. Payload constructed with only `member_id`, `exercise_id`, `rating=3` has:
  - `payload.text is None`
  - `payload.workout_session_id is None`
  - `payload.context_type == "post_workout"`
- [ ] Pass

---

## Integration Tests

### UAT-INT-001: Schema file exports all three required models

- **Description**: `backend/app/schemas/kg.py` must export `FeedbackPayload`, `KGRecommendRequest`, and `KGExplainRequest`. This verifies the full acceptance criterion "three schema classes present" without requiring a running server.
- **Steps**:
  1. Run the command below; it imports the three classes and prints their names
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.schemas.kg import FeedbackPayload, KGRecommendRequest, KGExplainRequest; print(FeedbackPayload.__name__, KGRecommendRequest.__name__, KGExplainRequest.__name__)"
  ```
- **Expected Result**: Exits with code 0 and prints `FeedbackPayload KGRecommendRequest KGExplainRequest` (no import errors).
- [ ] Pass

### UAT-INT-002: `write_feedback` importable from service module

- **Description**: `backend/app/kg/feedback_service.py` must expose `write_feedback` as a callable, confirming the service layer is wired correctly and all its internal imports resolve.
- **Steps**:
  1. Run the command below; it imports `write_feedback` and prints its qualified name
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.feedback_service import write_feedback; import inspect; print(inspect.iscoroutinefunction(write_feedback))"
  ```
- **Expected Result**: Exits with code 0 and prints `True` (confirming `write_feedback` is an async function).
- [ ] Pass

### UAT-INT-003: No duplicate Cypher logic — service delegates to `ingest_feedback` module constants

- **Description**: `write_feedback` must reuse the Cypher query constants (`_MERGE_FEEDBACK_EVENT`, `_EDGE_EXERCISE_ABOUT`, `_EDGE_MEMBER_RATED`) from `ingest_feedback.py` rather than defining its own. This verifies the "no duplicate logic" acceptance criterion.
- **Steps**:
  1. Run the targeted Cypher-query test below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py::test_write_feedback_writes_correct_cypher_queries -v
  ```
- **Expected Result**: `test_write_feedback_writes_correct_cypher_queries PASSED` — the mock confirms that the three Cypher constants from `ingest_feedback.py` were passed to `_run_write_tx`.
- [ ] Pass
