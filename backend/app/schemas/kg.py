"""Pydantic schemas for Knowledge Graph API operations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FeedbackPayload(BaseModel):
    """Payload for submitting post-workout exercise feedback."""

    member_id: str = Field(description="UUID of the member submitting feedback")
    exercise_id: str = Field(description="UUID of the exercise being rated")
    rating: int = Field(ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    text: str | None = Field(default=None, description="Optional free-text feedback")
    workout_session_id: str | None = Field(
        default=None,
        description="UUID of the associated workout session, if any",
    )
    context_type: str = Field(
        default="post_workout",
        description="Context in which the feedback was given (e.g. 'post_workout')",
    )


class KGRecommendRequest(BaseModel):
    """Request body for exercise recommendation queries against the knowledge graph."""

    member_id: str = Field(description="UUID of the member to generate recommendations for")
    query: str = Field(description="Natural-language query describing desired workout or exercise type")


class KGExplainRequest(BaseModel):
    """Request body for explaining why an exercise was recommended."""

    member_id: str = Field(description="UUID of the member")
    exercise_id: str = Field(description="UUID of the exercise to explain")
