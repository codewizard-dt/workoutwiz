# 065 — KG FastAPI Router: /kg/recommend, /kg/explain, /kg/feedback

> **Depends on**: [060-generation-agent-subgraph](completed/060-generation-agent-subgraph.md), [061-injury-safety-gate](completed/061-injury-safety-gate.md), [062-explainability-tool](completed/062-explainability-tool.md), [063-fallback-handler](completed/063-fallback-handler.md), [064-feedback-writeback](completed/064-feedback-writeback.md)
> **Blocks**: [066-tool-call-seam](066-tool-call-seam.md), [067-hub-integration](067-hub-integration.md), [070-kg-chat-dashboard](070-kg-chat-dashboard.md), [071-feedback-submission-ui](071-feedback-submission-ui.md)
> **Parallel-safe with**: [068-critical-path-test-injury-filtering](068-critical-path-test-injury-filtering.md), [069-critical-path-test-graph-retrieval](069-critical-path-test-graph-retrieval.md)

## Objective

Create `backend/app/routers/kg.py` with 3 endpoints and register it in `backend/app/main.py`:
- `POST /kg/recommend` — run the full retrieval → generation pipeline for a member
- `POST /kg/explain` — explain why a specific exercise was skipped
- `POST /kg/feedback` — write post-workout feedback to the graph

## Approach

Each endpoint:
1. Opens a Neo4j driver from settings (using `neo4j.AsyncGraphDatabase.driver(settings.neo4j_uri, ...)`)
2. Calls the appropriate service function
3. Closes the driver

**Schemas** (from `app.schemas.kg`): `KGRecommendRequest`, `KGExplainRequest`, `FeedbackPayload`.

**Response models:**
```python
class KGRecommendResponse(BaseModel):
    member_id: str
    exercises: list[RecommendedExercise]
    overall_reasoning: str
    skipped_exercise_ids: list[str]
    fallback_used: bool

class KGExplainResponse(BaseModel):
    exercise_id: str
    explanation: str

class KGFeedbackResponse(BaseModel):
    feedback_id: str
    message: str
```

**Recommend endpoint** flow:
1. Build retrieval graph, invoke with `{member_id, query}`
2. Get `ContextSlice` from retrieval result
3. Build generation graph, invoke with `{member_id, query, context}`
4. Return `KGRecommendResponse`

**Authentication**: Use the existing `current_active_user` dependency from `app.auth` (same as other routers) — but the member_id in the request body overrides the user's id if provided, or default to `str(user.id)`.

## Steps

### 1. Inspect existing routers for import/auth pattern  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/routers/exercises.py` to confirm:
- How `current_active_user` is imported and used
- How the router is declared (`APIRouter(prefix=..., tags=...)`)
- How `main.py` registers routers

- [ ] Import pattern and auth dependency confirmed

### 2. Create `backend/app/routers/kg.py`  <!-- agent: general-purpose -->

Use the `Write` tool to create with:
- `router = APIRouter(prefix="/kg", tags=["knowledge-graph"])`
- `POST /recommend` endpoint: calls retrieval + generation pipeline
- `POST /explain` endpoint: calls `explain_skipped_exercise()`
- `POST /feedback` endpoint: calls `write_feedback()`
- Response models defined in the file
- All 3 endpoints wrapped in `try/except` returning 500 on failure

- [ ] `backend/app/routers/kg.py` created with 3 endpoints

### 3. Register router in `backend/app/main.py`  <!-- agent: general-purpose -->

Use Serena `find_symbol` to locate `app.include_router()` calls in `main.py`. Add:
```python
from app.routers.kg import router as kg_router
app.include_router(kg_router)
```

- [ ] Router registered in `main.py`

### 4. Test endpoints manually (smoke test)  <!-- agent: general-purpose -->

Start the backend:
```bash
set -a && source .env && set +a && cd backend && uvicorn app.main:app --port 8001 --reload &
sleep 3
curl -s http://localhost:8001/kg/recommend || echo "NEEDS AUTH"
kill %1
```

Verify the endpoint exists (400/422/401 is fine; 404 means not registered).

- [ ] Router registered correctly (non-404 response on /kg/recommend)

### 5. Write integration test `backend/tests/test_kg_router.py`  <!-- agent: general-purpose -->

Using FastAPI's `TestClient` (sync) or `AsyncClient`:
- `test_kg_recommend_returns_200`: mock retrieval_graph and generation_graph, assert 200 + response shape
- `test_kg_explain_returns_explanation`: mock `explain_skipped_exercise`, assert 200
- `test_kg_feedback_writes_and_returns_id`: mock `write_feedback`, assert 200 + `feedback_id` in response

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/test_kg_router.py -v
```

- [ ] ≥3 router tests passing

### 6. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 6 router placeholder with `[TASK-065: KG FastAPI router...](../tasks/065-kg-fastapi-router.md)`.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `backend/app/routers/kg.py` with `POST /kg/recommend`, `POST /kg/explain`, `POST /kg/feedback`
- [ ] Router registered in `main.py` — all 3 endpoints reachable
- [ ] `POST /kg/recommend` runs retrieval → generation pipeline and returns `KGRecommendResponse`
- [ ] `POST /kg/explain` returns explanation string
- [ ] `POST /kg/feedback` persists to Neo4j and returns `feedback_id`
- [ ] ≥3 tests passing

---
**UAT**: `.docs/uat/065-kg-fastapi-router.uat.md`
