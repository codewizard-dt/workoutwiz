# 064 — Feedback Write-Back: Persist Post-Workout Ratings to Graph

> **Depends on**: [053-feedback-ingestion-neo4j](completed/053-feedback-ingestion-neo4j.md)
> **Blocks**: [065-kg-fastapi-router](065-kg-fastapi-router.md)
> **Parallel-safe with**: [060-generation-agent-subgraph](060-generation-agent-subgraph.md)

## Objective

Expose the existing `FeedbackEvent` Neo4j ingestion as a service function callable from the FastAPI layer, and add a Pydantic schema for feedback submission. No new API router in this task — that's TASK-065.

## Approach

The `ingest_feedback.py` module in `backend/app/knowledge_graph/` already has the ingestion logic. This task:
1. Adds a `FeedbackWriteService` class (or standalone async function) in `backend/app/kg/feedback_service.py` that wraps the ingestion call.
2. Defines `FeedbackPayload` Pydantic schema in `backend/app/schemas/kg.py`.
3. Writes a unit test.

**`FeedbackPayload` schema:**
```python
class FeedbackPayload(BaseModel):
    member_id: str
    exercise_id: str
    rating: int = Field(ge=1, le=5)
    text: str | None = None
    workout_session_id: str | None = None
    context_type: str = "post_workout"
```

**`write_feedback(payload: FeedbackPayload, driver: AsyncDriver) -> str`**: calls the existing ingestion function, returns the created `FeedbackEvent` node's `id`.

## Steps

### 1. Inspect existing feedback ingestion  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/knowledge_graph/ingest_feedback.py`. Note the function signature(s) for creating `FeedbackEvent` nodes and their parameters.

- [ ] Existing feedback ingestion function signature confirmed

### 2. Create `backend/app/schemas/kg.py`  <!-- agent: general-purpose -->

Use the `Write` tool to create with:
- `FeedbackPayload` Pydantic model (fields above)
- `KGRecommendRequest` model: `{ member_id: str, query: str }`
- `KGExplainRequest` model: `{ member_id: str, exercise_id: str }`

- [ ] `backend/app/schemas/kg.py` created with all 3 schema classes

### 3. Create `backend/app/kg/feedback_service.py`  <!-- agent: general-purpose -->

```python
"""Feedback write-back service — wraps Neo4j FeedbackEvent ingestion."""
import uuid
import logging
from neo4j import AsyncDriver
from app.schemas.kg import FeedbackPayload
from app.knowledge_graph.ingest_feedback import ingest_feedback_event  # adjust name to actual function

logger = logging.getLogger(__name__)

async def write_feedback(payload: FeedbackPayload, driver: AsyncDriver) -> str:
    """Persist a feedback event to Neo4j. Returns the created node's id."""
    feedback_id = str(uuid.uuid4())
    await ingest_feedback_event(
        feedback_id=feedback_id,
        member_id=payload.member_id,
        exercise_id=payload.exercise_id,
        rating=payload.rating,
        text=payload.text,
        workout_session_id=payload.workout_session_id,
        context_type=payload.context_type,
        driver=driver,
    )
    logger.info("Feedback %s written for member %s, exercise %s", feedback_id, payload.member_id, payload.exercise_id)
    return feedback_id
```

Adjust the import and call signature to match the actual ingest function found in Step 1.

- [ ] `backend/app/kg/feedback_service.py` created with `write_feedback()` async function

### 4. Write unit test `backend/tests/kg/test_feedback_service.py`  <!-- agent: general-purpose -->

Tests:
- `test_write_feedback_calls_ingestion`: mock the ingest function, call `write_feedback()`, assert ingest was called with correct args and a UUID is returned.
- `test_feedback_payload_validates_rating_range`: assert `FeedbackPayload(rating=0, ...)` raises `ValidationError`; rating=5 is valid.

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_feedback_service.py -v
```

- [ ] Tests pass

### 5. Update roadmap  <!-- agent: general-purpose -->

Edit roadmap to replace inline Phase 5 feedback write-back placeholder with `[TASK-064: Feedback write-back...](../tasks/064-feedback-writeback.md)`.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `backend/app/schemas/kg.py` with `FeedbackPayload`, `KGRecommendRequest`, `KGExplainRequest`
- [ ] `backend/app/kg/feedback_service.py` with `write_feedback(payload, driver) -> str`
- [ ] `write_feedback` calls the existing Neo4j ingestion — no duplicate logic
- [ ] `FeedbackPayload.rating` validated 1–5 via `Field(ge=1, le=5)`
- [ ] Tests pass

---
**UAT**: [`.docs/uat/064-feedback-writeback.uat.md`](../uat/064-feedback-writeback.uat.md)
