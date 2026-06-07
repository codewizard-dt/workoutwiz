"""Pydantic schemas for Knowledge Graph API operations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FeedbackPayload(BaseModel):
    """Payload for submitting post-workout feedback.

    Supports three context types:
      - exercise: feedback on a single exercise (exercise_id required)
      - workout:  feedback on an entire workout session (workout_id required)
      - set:      feedback on a specific set (workout_set_id + exercise_id required)
    """

    member_id: str = Field(description="UUID of the member submitting feedback")
    exercise_id: str | None = Field(
        default=None,
        description="UUID of the exercise being rated (required for exercise/set contexts)",
    )
    rating: int = Field(ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    text: str | None = Field(default=None, description="Optional free-text feedback")
    workout_id: str | None = Field(
        default=None,
        description="UUID of the associated workout (required for workout context)",
    )
    workout_set_id: str | None = Field(
        default=None,
        description="UUID of the specific set (required for set context)",
    )
    context_type: str = Field(
        default="exercise",
        description="Context type: 'exercise', 'workout', or 'set'",
    )


class KGRecommendRequest(BaseModel):
    """Request body for exercise recommendation queries against the knowledge graph."""

    member_id: str = Field(description="UUID of the member to generate recommendations for")
    query: str = Field(description="Natural-language query describing desired workout or exercise type")


class KGExplainRequest(BaseModel):
    """Request body for explaining why an exercise was recommended."""

    member_id: str = Field(description="UUID of the member")
    exercise_id: str = Field(description="UUID of the exercise to explain")
