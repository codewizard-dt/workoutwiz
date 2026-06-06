"""Exercise data cache for LangGraph agents.

Loaded once at app startup from the PostgreSQL exercises table via
`load_exercises()`. All public functions are synchronous so they can
be called safely from within synchronous LangGraph node functions.
"""
from __future__ import annotations


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise as ExerciseModel
from app.services.exercises import list_exercises


# ---------------------------------------------------------------------------
# Module-level cache — populated by load_exercises() at startup
# ---------------------------------------------------------------------------

_cache: list[ExerciseModel] = []


async def load_exercises(session: AsyncSession) -> None:
    """Populate the in-memory exercise cache from the database.

    Call once during application lifespan startup.
    """
    global _cache
    _cache = await list_exercises(session)


# ---------------------------------------------------------------------------
# Synchronous accessors (safe to call from LangGraph node functions)
# ---------------------------------------------------------------------------

def get_all_exercises() -> list[ExerciseModel]:
    return list(_cache)


def get_exercise_by_id(exercise_id: str) -> ExerciseModel | None:
    return next((e for e in _cache if str(e.id) == exercise_id), None)


def search_exercises(
    muscle_groups: list[str] | None = None,
    equipment: list[str] | None = None,
    movement_patterns: list[str] | None = None,
    max_results: int = 10,
) -> list[ExerciseModel]:
    """Filter exercises from the cache by muscle group, equipment, or movement pattern.

    Matching is case-insensitive substring against the stored values.
    Results are sorted by priority_tier ascending (tier 1 = highest quality first).
    """
    results = list(_cache)

    if muscle_groups:
        mg_lower = [m.lower() for m in muscle_groups]
        results = [
            e for e in results
            if any(m in " ".join(e.muscle_groups).lower() for m in mg_lower)
        ]

    if equipment:
        eq_lower = [eq.lower() for eq in equipment]
        results = [
            e for e in results
            if any(eq in " ".join(e.equipment_required).lower() for eq in eq_lower)
        ]

    if movement_patterns:
        mp_lower = [m.lower() for m in movement_patterns]
        results = [
            e for e in results
            if _matches_movement_patterns(e, mp_lower)
        ]

    results.sort(key=lambda e: e.priority_tier)
    return results[:max_results]


def _matches_movement_patterns(exercise: ExerciseModel, patterns_lower: list[str]) -> bool:
    """Check if an exercise matches any of the given movement patterns.

    Handles both list[str] and dict movement_patterns formats from the DB.
    """
    mp = exercise.movement_patterns
    if isinstance(mp, dict):
        searchable = " ".join(str(v) for v in mp.values()).lower()
    elif isinstance(mp, list):
        searchable = " ".join(str(v) for v in mp).lower()
    else:
        searchable = str(mp).lower()
    return any(p in searchable for p in patterns_lower)
