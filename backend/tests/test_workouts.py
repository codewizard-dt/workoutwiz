import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from tests.test_auth import register_and_login

# A known exercise ID from exercises.json (seeded each session)
EXERCISE_ID = "0b3178cf-bf89-45a3-bfb0-27310ef6ef38"

SAMPLE_WORKOUT = {
    "started_at": "2024-01-15T09:00:00Z",
    "ended_at": "2024-01-15T10:00:00Z",
    "sequences": [
        {
            "phase": "main",
            "position": 0,
            "sets": [
                {
                    "exercise_id": EXERCISE_ID,
                    "set_type": "STRENGTH",
                    "position": 0,
                    "reps": 10,
                    "weight_kg": 80.0,
                },
            ],
        }
    ],
}


@pytest.mark.asyncio
async def test_list_workouts_unauthenticated(client: AsyncClient):
    resp = await client.get("/workouts/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_workout(client: AsyncClient):
    token = await register_and_login(client, f"create_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!")
    resp = await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert len(body["sequences"]) == 1
    assert len(body["sequences"][0]["sets"]) == 1
    assert body["sequences"][0]["sets"][0]["reps"] == 10


@pytest.mark.asyncio
async def test_list_workouts_isolation(client: AsyncClient):
    """User A cannot see User B's workouts."""
    email_a = f"user_a_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"user_b_{uuid.uuid4().hex[:8]}@example.com"
    token_a = await register_and_login(client, email_a, "S3cur3Pass!")
    token_b = await register_and_login(client, email_b, "S3cur3Pass!")

    # User A creates a workout
    await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B should see zero workouts
    resp = await client.get("/workouts/", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_workout(client: AsyncClient):
    token = await register_and_login(client, f"get_wk_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!")
    create_resp = await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token}"},
    )
    workout_id = create_resp.json()["id"]

    resp = await client.get(
        f"/workouts/{workout_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == workout_id
    assert len(body["sequences"]) == 1


@pytest.mark.asyncio
async def test_get_other_users_workout_returns_404(client: AsyncClient):
    """User B cannot fetch User A's workout."""
    email_a = f"owner_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"other_{uuid.uuid4().hex[:8]}@example.com"
    token_a = await register_and_login(client, email_a, "S3cur3Pass!")
    token_b = await register_and_login(client, email_b, "S3cur3Pass!")

    create_resp = await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    workout_id = create_resp.json()["id"]

    resp = await client.get(
        f"/workouts/{workout_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_workout(client: AsyncClient):
    token = await register_and_login(client, f"upd_wk_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!")
    create_resp = await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token}"},
    )
    workout_id = create_resp.json()["id"]

    updated = {
        "started_at": "2024-02-01T08:00:00Z",
        "ended_at": "2024-02-01T09:30:00Z",
        "sequences": [
            {
                "phase": "warmup",
                "position": 0,
                "sets": [
                    {
                        "exercise_id": EXERCISE_ID,
                        "set_type": "CARDIO",
                        "position": 0,
                        "duration_s": 300,
                    }
                ],
            }
        ],
    }

    resp = await client.put(
        f"/workouts/{workout_id}",
        json=updated,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sequences"][0]["phase"] == "warmup"
    assert body["sequences"][0]["sets"][0]["duration_s"] == 300


@pytest.mark.asyncio
async def test_delete_workout(client: AsyncClient):
    token = await register_and_login(client, f"del_wk_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!")
    create_resp = await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token}"},
    )
    workout_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/workouts/{workout_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204

    get_resp = await client.get(
        f"/workouts/{workout_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404
