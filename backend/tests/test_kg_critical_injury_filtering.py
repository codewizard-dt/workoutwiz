"""
Critical-path test 1: injury filtering correctness.
Assessment 2 requirement: contraindicated exercises never appear in output.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.kg.generation_graph import build_generation_graph, WorkoutRecommendation, RecommendedExercise
from app.kg.context_assembler import ContextSlice, SectionTokenCounts

SAFE_EXERCISES = [
    {"id": "ex-safe-1", "name": "Push-up"},
    {"id": "ex-safe-2", "name": "Plank"},
    {"id": "ex-safe-3", "name": "Glute Bridge"},
]

def _make_context(contraindicated_ids=None, safe=None) -> ContextSlice:
    return ContextSlice(
        member_profile={"id": "m1", "name": "Test Member", "goals": [], "fitness_level": "beginner"},
        safe_exercises=safe or SAFE_EXERCISES,
        preferred_exercises=[],
        vector_hits=[],
        token_counts=SectionTokenCounts(member_profile=10, safe_exercises=50, preferred_exercises=0, vector_hits=0, total=60),
        contraindicated_ids=contraindicated_ids or set(),
    )

def _make_recommendation(exercise_ids: list[str]) -> WorkoutRecommendation:
    return WorkoutRecommendation(
        exercises=[
            RecommendedExercise(exercise_id=eid, name=eid, sets=3, reps=10, reasoning="test")
            for eid in exercise_ids
        ],
        overall_reasoning="test",
        member_id="m1",
    )

@pytest.mark.asyncio
@pytest.mark.parametrize("contraindicated,llm_picks,expected_safe,expected_skipped", [
    ({"ex-bad-1"}, ["ex-safe-1", "ex-bad-1"], ["ex-safe-1"], ["ex-bad-1"]),
    ({"ex-bad-1", "ex-bad-2"}, ["ex-safe-1", "ex-bad-1", "ex-bad-2"], ["ex-safe-1"], ["ex-bad-1", "ex-bad-2"]),
    (set(), ["ex-safe-1", "ex-safe-2"], ["ex-safe-1", "ex-safe-2"], []),
    ({"ex-safe-1", "ex-safe-2", "ex-safe-3"}, ["ex-safe-1"], [], ["ex-safe-1"]),
    ({"ex-preferred"}, ["ex-preferred", "ex-safe-1"], ["ex-safe-1"], ["ex-preferred"]),
])
async def test_contraindicated_exercises_never_in_output(
    contraindicated, llm_picks, expected_safe, expected_skipped
):
    context = _make_context(contraindicated_ids=contraindicated)
    mock_llm_output = _make_recommendation(llm_picks)

    with patch("app.kg.generation_graph.ChatAnthropic") as mock_chat:
        mock_instance = MagicMock()
        mock_instance.with_structured_output.return_value.ainvoke = AsyncMock(return_value=mock_llm_output)
        mock_chat.return_value = mock_instance

        graph = build_generation_graph()
        result = await graph.ainvoke({
            "member_id": "m1",
            "query": "build a workout",
            "context": context,
        })

    rec = result["recommendation"]
    actual_ids = [e.exercise_id for e in rec.exercises]

    # CRITICAL: no contraindicated exercise in output
    for bad_id in contraindicated:
        assert bad_id not in actual_ids, f"Contraindicated exercise {bad_id} found in output!"

    # Skipped exercises recorded
    for skipped_id in expected_skipped:
        assert skipped_id in rec.skipped_exercise_ids
