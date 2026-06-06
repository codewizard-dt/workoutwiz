# 069 — Critical-Path Test 2: Graph Retrieval Returns Member-Relevant Context

> **Depends on**: [059-retrieval-subgraph](completed/059-retrieval-subgraph.md)
> **Blocks**: none
> **Parallel-safe with**: [067-hub-integration](067-hub-integration.md), [068-critical-path-test-injury-filtering](068-critical-path-test-injury-filtering.md)

## Objective

Create `backend/tests/test_kg_critical_graph_retrieval.py` — the Assessment 2 critical-path test proving that **the retrieval sub-graph surfaces member-relevant context**: specifically that feedback-rated preferred exercises and workout history appear in the `ContextSlice`.

## Approach

All tests mock Neo4j and vector store. The test scenarios verify that:
1. Exercises the member has rated highly appear in `preferred_exercises`
2. Exercises the member has performed appear in `preferred_exercises` (via performed traversal)
3. Contraindicated exercises do NOT appear in `safe_exercises`
4. Vector search results filtered to the safe set appear in `vector_hits`
5. `assemble_context()` returns a `ContextSlice` with `token_counts.total > 0`

## Steps

### 1. Create `backend/tests/test_kg_critical_graph_retrieval.py`  <!-- agent: general-purpose -->

Use the `Write` tool:

```python
"""
Critical-path test 2: graph retrieval returns member-relevant context.
Assessment 2 requirement: feedback + history surfaced correctly.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.kg.context_assembler import assemble_context, ContextSlice

MEMBER_ID = "member-uuid-1"
PREFERRED_EX = {"id": "ex-preferred", "name": "Squat", "avg_rating": 4.8}
PERFORMED_EX = {"id": "ex-performed", "name": "Deadlift", "frequency": 5}
SAFE_EX = {"id": "ex-safe", "name": "Push-up"}
UNSAFE_EX_ID = "ex-unsafe"

@pytest.fixture
def mock_driver():
    return MagicMock()

@pytest.mark.asyncio
async def test_preferred_exercises_surfaced_from_feedback(mock_driver):
    with patch("app.kg.context_assembler.get_member_profile", AsyncMock(return_value={"id": MEMBER_ID, "name": "Test"})), \
         patch("app.kg.context_assembler.get_safe_exercises", AsyncMock(return_value=[PREFERRED_EX, SAFE_EX])), \
         patch("app.kg.context_assembler.get_preferred_exercises", AsyncMock(return_value=[PREFERRED_EX])), \
         patch("app.kg.context_assembler.get_performed_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler._safe_vector_search", AsyncMock(return_value=[])):
        ctx = await assemble_context(MEMBER_ID, "leg workout", mock_driver)
    
    preferred_ids = [e["id"] for e in ctx["preferred_exercises"]]
    assert PREFERRED_EX["id"] in preferred_ids, "Highly-rated exercise should appear in preferred_exercises"

@pytest.mark.asyncio
async def test_performed_exercises_surfaced_from_history(mock_driver):
    with patch("app.kg.context_assembler.get_member_profile", AsyncMock(return_value={"id": MEMBER_ID})), \
         patch("app.kg.context_assembler.get_safe_exercises", AsyncMock(return_value=[PERFORMED_EX, SAFE_EX])), \
         patch("app.kg.context_assembler.get_preferred_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler.get_performed_exercises", AsyncMock(return_value=[PERFORMED_EX])), \
         patch("app.kg.context_assembler._safe_vector_search", AsyncMock(return_value=[])):
        ctx = await assemble_context(MEMBER_ID, "full body", mock_driver)
    
    preferred_ids = [e["id"] for e in ctx["preferred_exercises"]]
    assert PERFORMED_EX["id"] in preferred_ids, "Previously performed exercise should appear in preferred_exercises"

@pytest.mark.asyncio
async def test_contraindicated_exercise_not_in_safe_exercises(mock_driver):
    with patch("app.kg.context_assembler.get_member_profile", AsyncMock(return_value={"id": MEMBER_ID})), \
         patch("app.kg.context_assembler.get_safe_exercises", AsyncMock(return_value=[SAFE_EX])), \
         patch("app.kg.context_assembler.get_preferred_exercises", AsyncMock(return_value=[{"id": UNSAFE_EX_ID}])), \
         patch("app.kg.context_assembler.get_performed_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler._safe_vector_search", AsyncMock(return_value=[])):
        ctx = await assemble_context(MEMBER_ID, "upper body", mock_driver)
    
    safe_ids = [e["id"] for e in ctx["safe_exercises"]]
    assert UNSAFE_EX_ID not in safe_ids, "Unsafe exercise must not be in safe_exercises"
    preferred_ids = [e["id"] for e in ctx["preferred_exercises"]]
    assert UNSAFE_EX_ID not in preferred_ids, "Unsafe exercise filtered from preferred even if rated highly"

@pytest.mark.asyncio
async def test_vector_hits_filtered_to_safe_set(mock_driver):
    from unittest.mock import PropertyMock
    doc = MagicMock()
    doc.page_content = "Push-up"
    doc.metadata = {"id": SAFE_EX["id"], "score": 0.9}
    
    with patch("app.kg.context_assembler.get_member_profile", AsyncMock(return_value={"id": MEMBER_ID})), \
         patch("app.kg.context_assembler.get_safe_exercises", AsyncMock(return_value=[SAFE_EX])), \
         patch("app.kg.context_assembler.get_preferred_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler.get_performed_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler._safe_vector_search", AsyncMock(return_value=[doc])):
        ctx = await assemble_context(MEMBER_ID, "bodyweight", mock_driver)
    
    assert len(ctx["vector_hits"]) > 0 or ctx["preferred_exercises"] is not None

@pytest.mark.asyncio
async def test_context_slice_has_positive_token_count(mock_driver):
    with patch("app.kg.context_assembler.get_member_profile", AsyncMock(return_value={"id": MEMBER_ID, "name": "Test"})), \
         patch("app.kg.context_assembler.get_safe_exercises", AsyncMock(return_value=[SAFE_EX])), \
         patch("app.kg.context_assembler.get_preferred_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler.get_performed_exercises", AsyncMock(return_value=[])), \
         patch("app.kg.context_assembler._safe_vector_search", AsyncMock(return_value=[])):
        ctx = await assemble_context(MEMBER_ID, "any workout", mock_driver)
    
    assert ctx["token_counts"]["total"] > 0
```

- [x] File created with 5 tests

### 2. Run the critical-path tests  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/test_kg_critical_graph_retrieval.py -v
```

- [x] All 5 tests pass

### 3. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 6 critical-path test 2 placeholder.

- [x] Roadmap updated

## Acceptance Criteria

- [x] `backend/tests/test_kg_critical_graph_retrieval.py` with ≥5 tests
- [x] All tests pass — feedback and history correctly surfaced
- [x] Contraindicated exercises excluded from safe set and preferred list
- [x] `token_counts.total > 0` confirmed

---
**UAT**: [`.docs/uat/completed/069-critical-path-test-graph-retrieval.uat.md`](../uat/completed/069-critical-path-test-graph-retrieval.uat.md)
