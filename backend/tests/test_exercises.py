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



@pytest.mark.asyncio
async def test_exercise_read_includes_metadata_fields(client: AsyncClient):
    resp = await client.get("/exercises/")
    assert resp.status_code == 200
    ex = resp.json()[0]
    for field in ("joints_loaded", "side", "estimated_rep_duration"):
        assert field in ex
    assert isinstance(ex["joints_loaded"], list)


@pytest.mark.asyncio
async def test_facets_shape_and_ordering(client: AsyncClient):
    resp = await client.get("/exercises/facets")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("muscle_groups", "equipment", "movement_patterns", "categories"):
        assert key in data
        assert isinstance(data[key], list)
        for entry in data[key]:
            assert set(entry.keys()) == {"value", "count"}
            assert entry["count"] >= 1
    # muscle_groups facet is non-empty for the seeded catalog and sorted by count desc
    assert len(data["muscle_groups"]) > 0
    counts = [entry["count"] for entry in data["muscle_groups"]]
    assert counts == sorted(counts, reverse=True)
