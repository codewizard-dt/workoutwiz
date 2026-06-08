import uuid
from pydantic import BaseModel


class ExerciseSeedRecord(BaseModel):
    """Validates a single record from 1-multi-agent/exercises.json."""

    model_config = {"extra": "ignore"}

    id: uuid.UUID
    name: str
    category: str | None = None
    muscle_groups: list[str]
    equipment_required: list[str]
    movement_patterns: list[str]
    is_reps: bool
    is_duration: bool
    supports_weight: bool
    is_bilateral: bool
    bilateral_pair_id: uuid.UUID | None = None
    priority_tier: int
    description: str | None = None
    joints_loaded: list[str] = []
    side: str | None = None
    estimated_rep_duration: float | None = None
