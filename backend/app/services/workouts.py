import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.workout import Workout, WorkoutSequence, WorkoutSet
from app.schemas.workout import WorkoutCreate


async def get_user_workouts(session: AsyncSession, user_id: uuid.UUID) -> list[Workout]:
    stmt = (
        select(Workout)
        .where(Workout.user_id == user_id)
        .options(selectinload(Workout.sequences).selectinload(WorkoutSequence.sets))
        .order_by(Workout.started_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_workout(session: AsyncSession, workout_id: uuid.UUID, user_id: uuid.UUID) -> Workout | None:
    stmt = (
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
        .options(selectinload(Workout.sequences).selectinload(WorkoutSequence.sets))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_workout(session: AsyncSession, user_id: uuid.UUID, data: WorkoutCreate) -> Workout:
    workout = Workout(user_id=user_id, started_at=data.started_at, ended_at=data.ended_at)
    session.add(workout)
    await session.flush()  # Get workout.id before inserting sequences

    for seq_data in data.sequences:
        seq = WorkoutSequence(workout_id=workout.id, phase=seq_data.phase, position=seq_data.position)
        session.add(seq)
        await session.flush()
        for set_data in seq_data.sets:
            ws = WorkoutSet(sequence_id=seq.id, **set_data.model_dump())
            session.add(ws)

    await session.commit()
    await session.refresh(workout)
    result = await get_workout(session, workout.id, user_id)
    assert result is not None
    return result


async def update_workout(session: AsyncSession, workout: Workout, data: WorkoutCreate) -> Workout:
    workout.started_at = data.started_at
    workout.ended_at = data.ended_at
    if data.enjoyment is not None:
        workout.enjoyment = data.enjoyment
    if data.note is not None:
        workout.note = data.note
    # Replace sequences (cascade delete handles sets)
    await session.execute(delete(WorkoutSequence).where(WorkoutSequence.workout_id == workout.id))
    await session.flush()
    for seq_data in data.sequences:
        seq = WorkoutSequence(workout_id=workout.id, phase=seq_data.phase, position=seq_data.position)
        session.add(seq)
        await session.flush()
        for set_data in seq_data.sets:
            ws = WorkoutSet(sequence_id=seq.id, **set_data.model_dump())
            session.add(ws)
    workout_id = workout.id
    user_id = workout.user_id
    await session.commit()
    session.expunge_all()
    result = await get_workout(session, workout_id, user_id)
    assert result is not None
    return result


async def delete_workout(session: AsyncSession, workout: Workout) -> None:
    await session.delete(workout)
    await session.commit()
