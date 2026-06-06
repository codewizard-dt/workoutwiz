import uuid

from pydantic import BaseModel, Field


class ExerciseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(
        description="Unique exercise identifier (UUID)",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    name: str = Field(
        description="Human-readable exercise name",
        examples=["Barbell Back Squat"],
    )
    category: str = Field(
        description="Broad exercise category (e.g. Strength, Cardio)",
        examples=["Strength"],
    )
    muscle_groups: list[str] = Field(
        description="Primary and secondary muscles targeted",
        examples=[["Quadriceps", "Glutes"]],
    )
    equipment_required: list[str] = Field(
        description="Equipment needed to perform the exercise",
        examples=[["Barbell", "Squat Rack"]],
    )
    movement_patterns: list[str] = Field(
        description="Fundamental movement patterns",
        examples=[["Squat", "Bilateral"]],
    )
    is_reps: bool = Field(
        description="Whether the exercise is tracked by repetition count",
        examples=[True],
    )
    is_duration: bool = Field(
        description="Whether the exercise is tracked by time duration",
        examples=[False],
    )
    supports_weight: bool = Field(
        description="Whether weight can be added to this exercise",
        examples=[True],
    )
    is_bilateral: bool = Field(
        description="Whether the exercise works both sides simultaneously",
        examples=[True],
    )
    bilateral_pair_id: uuid.UUID | None = Field(
        description="UUID of the paired unilateral variant, if any",
        examples=[None],
    )
    priority_tier: int = Field(
        description="Programming priority (1 = highest quality)",
        examples=[1],
    )
    description: str | None = Field(
        description="Optional longer description of the exercise",
        examples=["A compound lower-body movement targeting quadriceps and glutes."],
    )
