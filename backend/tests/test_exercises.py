import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_all_exercises(client: AsyncClient):
    resp = await client.get("/exercises/")
    assert resp.status_code == 200
    exercises = resp.json()
    assert len(exercises) == 50


@pytest.mark.asyncio
async def test_filter_by_name(client: AsyncClient):
    resp = await client.get("/exercises/?name=squat")
    assert resp.status_code == 200
    exercises = resp.json()
    assert len(exercises) > 0
    for ex in exercises:
        assert "squat" in ex["name"].lower()


@pytest.mark.asyncio
async def test_filter_by_muscle_group(client: AsyncClient):
    resp = await client.get("/exercises/?muscle_groups=quads")
    assert resp.status_code == 200
    exercises = resp.json()
    assert len(exercises) > 0
    for ex in exercises:
        assert "quads" in ex["muscle_groups"]


@pytest.mark.asyncio
async def test_filter_by_equipment(client: AsyncClient):
    resp = await client.get("/exercises/?equipment=barbell")
    assert resp.status_code == 200
    exercises = resp.json()
    assert len(exercises) > 0
    for ex in exercises:
        equipment_lower = [e.lower() for e in ex["equipment_required"]]
        assert "barbell" in equipment_lower


@pytest.mark.asyncio
async def test_filter_by_priority_tier(client: AsyncClient):
    # All 50 seeded exercises are priority_tier=2
    resp = await client.get("/exercises/?priority_tier=2")
    assert resp.status_code == 200
    exercises = resp.json()
    assert len(exercises) > 0
    for ex in exercises:
        assert ex["priority_tier"] == 2


@pytest.mark.asyncio
async def test_invalid_priority_tier(client: AsyncClient):
    resp = await client.get("/exercises/?priority_tier=4")
    assert resp.status_code == 422
