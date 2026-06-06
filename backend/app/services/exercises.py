from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import array
from app.models.exercise import Exercise


async def list_exercises(
    session: AsyncSession,
    name: str | None = None,
    muscle_groups: list[str] | None = None,
    equipment: list[str] | None = None,
    priority_tier: int | None = None,
) -> list[Exercise]:
    stmt = select(Exercise)

    if name:
        stmt = stmt.where(Exercise.name.ilike(f"%{name}%"))
    if muscle_groups:
        stmt = stmt.where(Exercise.muscle_groups.overlap(array(muscle_groups)))
    if equipment:
        # equipment_required values are titlecase in the DB; normalise both sides
        # to lowercase so callers can pass "barbell" or "Barbell" interchangeably.
        equipment_list = ", ".join(f"\'{e.lower().replace(chr(39), chr(39)+chr(39))}\'" for e in equipment)
        stmt = stmt.where(
            text(
                f"ARRAY(SELECT lower(unnest(equipment_required))) && ARRAY[{equipment_list}]::text[]"
            )
        )
    if priority_tier is not None:
        stmt = stmt.where(Exercise.priority_tier == priority_tier)

    stmt = stmt.order_by(Exercise.priority_tier, Exercise.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())
