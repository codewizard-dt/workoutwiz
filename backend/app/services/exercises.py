from collections import Counter
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



async def get_exercise_facets(
    session: AsyncSession,
) -> dict[str, list[tuple[str, int]]]:
    """Return distinct filterable values across the catalog, each with a count.

    Computed in one scan over the (small) exercise table. Each facet list is
    sorted by descending count, then alphabetically, so the most common values
    surface first in the UI.
    """
    stmt = select(
        Exercise.muscle_groups,
        Exercise.equipment_required,
        Exercise.movement_patterns,
        Exercise.category,
    )
    rows = (await session.execute(stmt)).all()

    muscle: Counter[str] = Counter()
    equipment: Counter[str] = Counter()
    patterns: Counter[str] = Counter()
    categories: Counter[str] = Counter()

    for muscle_groups, equipment_required, movement_patterns, category in rows:
        muscle.update(muscle_groups or [])
        equipment.update(equipment_required or [])
        patterns.update(movement_patterns or [])
        if category:
            categories[category] += 1

    def _sorted(counter: Counter[str]) -> list[tuple[str, int]]:
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))

    return {
        "muscle_groups": _sorted(muscle),
        "equipment": _sorted(equipment),
        "movement_patterns": _sorted(patterns),
        "categories": _sorted(categories),
    }
