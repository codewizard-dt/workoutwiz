import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.auth import current_active_user
from app.models.user import User
from app.schemas.workout import WorkoutCreate, WorkoutRead
from app.services import workouts as workout_service

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=list[WorkoutRead])
async def list_workouts(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    return await workout_service.get_user_workouts(session, user.id)


@router.post("/", response_model=WorkoutRead, status_code=201)
async def create_workout(
    data: WorkoutCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    return await workout_service.create_workout(session, user.id, data)


@router.get("/{workout_id}", response_model=WorkoutRead)
async def get_workout(
    workout_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.put("/{workout_id}", response_model=WorkoutRead)
async def update_workout(
    workout_id: uuid.UUID,
    data: WorkoutCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return await workout_service.update_workout(session, workout, data)


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    workout = await workout_service.get_workout(session, workout_id, user.id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    await workout_service.delete_workout(session, workout)
