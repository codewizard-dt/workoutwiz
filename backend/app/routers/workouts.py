import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.auth import current_active_user
from app.models.user import User
from app.models.workout import Workout
from app.schemas.workout import WorkoutCreate, WorkoutMetadataUpdate, WorkoutRead
from app.schemas.errors import ErrorResponse
from app.services import workouts as workout_service

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get(
    "/",
    response_model=list[WorkoutRead],
    summary="List workouts",
    description="Return all workouts belonging to the authenticated user, ordered by started_at descending.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"description": "Validation error"},
    },
)
async def list_workouts(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
) -> list[Workout]:
    return await workout_service.get_user_workouts(session, user.id)


@router.post(
    "/",
    response_model=WorkoutRead,
    status_code=201,
    summary="Create workout",
    description="Create a new workout for the authenticated user with optional sequences and sets.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"description": "Validation error — request body failed schema validation"},
    },
)
async def create_workout(
    data: WorkoutCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
) -> Workout:
    return await workout_service.create_workout(session, user.id, data)


@router.get(
    "/{workout_id}",
    response_model=WorkoutRead,
    summary="Get workout",
    description="Return a single workout by ID. Only the owning user's workouts are accessible.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
        422: {"description": "Validation error — workout_id is not a valid UUID"},
    },
)
async def get_workout(
    workout_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
) -> Workout:
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.put(
    "/{workout_id}",
    response_model=WorkoutRead,
    summary="Update workout",
    description="Replace a workout's data (started_at, ended_at, sequences). Full replacement — partial updates not supported.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
        422: {"description": "Validation error"},
    },
)
async def update_workout(
    workout_id: uuid.UUID,
    data: WorkoutCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
) -> Workout:
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return await workout_service.update_workout(session, workout, data)


@router.patch(
    "/{workout_id}",
    response_model=WorkoutRead,
    summary="Update workout metadata",
    description=(
        "Partially update workout-level fields (enjoyment, note) without "
        "touching sequences/sets. Set primary keys are preserved, so per-set "
        "feedback survives."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
        422: {"description": "Validation error"},
    },
)
async def update_workout_metadata(
    workout_id: uuid.UUID,
    data: WorkoutMetadataUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
) -> Workout:
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return await workout_service.update_workout_metadata(session, workout, data)


@router.delete(
    "/{workout_id}",
    status_code=204,
    summary="Delete workout",
    description="Permanently delete a workout and all its sequences and sets.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
        422: {"description": "Validation error — workout_id is not a valid UUID"},
    },
)
async def delete_workout(
    workout_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
) -> None:
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    await workout_service.delete_workout(session, workout)
