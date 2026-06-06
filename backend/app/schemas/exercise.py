import uuid
from pydantic import BaseModel


class ExerciseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    category: str
    muscle_groups: list[str]
    equipment_required: list[str]
    movement_patterns: list[str]
    is_reps: bool
    is_duration: bool
    supports_weight: bool
    is_bilateral: bool
    bilateral_pair_id: uuid.UUID | None
    priority_tier: int
    description: str | None
