from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models.exercise import Exercise
from app.schemas.exercise import ExerciseRead, ExerciseFacets, ExerciseFacetValue
from app.services.exercises import list_exercises, get_exercise_facets
from app.schemas.errors import ErrorResponse

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get(
    "/facets",
    response_model=ExerciseFacets,
    summary="Exercise filter facets",
    description=(
        "Return distinct muscle groups, equipment, movement patterns, and "
        "categories across the catalog, each with a count, for building filter UI."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated — valid JWT Bearer token required"},
    },
)
async def get_facets(
    session: AsyncSession = Depends(get_async_session),
) -> ExerciseFacets:
    data = await get_exercise_facets(session)
    return ExerciseFacets(
        muscle_groups=[ExerciseFacetValue(value=v, count=c) for v, c in data["muscle_groups"]],
        equipment=[ExerciseFacetValue(value=v, count=c) for v, c in data["equipment"]],
        movement_patterns=[ExerciseFacetValue(value=v, count=c) for v, c in data["movement_patterns"]],
        categories=[ExerciseFacetValue(value=v, count=c) for v, c in data["categories"]],
    )


@router.get(
    "/",
    response_model=list[ExerciseRead],
    summary="List exercises",
    description=(
        "Return all exercises, optionally filtered by name, muscle group, "
        "equipment, or priority tier. Results are ordered by priority_tier ascending."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated — valid JWT Bearer token required"},
        422: {"description": "Validation error — one or more query parameters failed type or constraint checks"},
    },
)
async def get_exercises(
    name: str | None = Query(None, description="Case-insensitive name search"),
    muscle_groups: list[str] | None = Query(None, description="Filter by muscle group (any match)"),
    equipment: list[str] | None = Query(None, description="Filter by equipment (any match)"),
    priority_tier: int | None = Query(None, ge=1, le=3, description="Filter by priority tier (1=highest)"),
    session: AsyncSession = Depends(get_async_session),
) -> list[Exercise]:
    return await list_exercises(session, name=name, muscle_groups=muscle_groups, equipment=equipment, priority_tier=priority_tier)
