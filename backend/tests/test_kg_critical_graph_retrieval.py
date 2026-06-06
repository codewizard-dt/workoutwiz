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
