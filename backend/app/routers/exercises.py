from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models.exercise import Exercise
from app.schemas.exercise import ExerciseRead
from app.services.exercises import list_exercises

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[ExerciseRead])
async def get_exercises(
    name: str | None = Query(None, description="Case-insensitive name search"),
    muscle_groups: list[str] | None = Query(None, description="Filter by muscle group (any match)"),
    equipment: list[str] | None = Query(None, description="Filter by equipment (any match)"),
    priority_tier: int | None = Query(None, ge=1, le=3, description="Filter by priority tier (1=highest)"),
    session: AsyncSession = Depends(get_async_session),
) -> list[Exercise]:
    return await list_exercises(session, name=name, muscle_groups=muscle_groups, equipment=equipment, priority_tier=priority_tier)
