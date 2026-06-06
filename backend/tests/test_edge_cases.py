"""
Edge case tests: missing data, invalid IDs, auth edge cases, concurrent requests.
"""
import asyncio
import uuid

import pytest
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

# ---------------------------------------------------------------------------
# 1. Missing data / invalid input tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_workout_missing_started_at(client: AsyncClient):
    """POST /workouts/ with empty body → 422 Unprocessable Entity."""
    token = await register_and_login(
        client, f"missing_field_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!"
    )
    resp = await client.post(
        "/workouts/",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_workout_invalid_uuid(client: AsyncClient):
    """GET /workouts/not-a-uuid → 422 (path param validation)."""
    token = await register_and_login(
        client, f"inv_uuid_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!"
    )
    resp = await client.get(
        "/workouts/not-a-uuid",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_workout_nonexistent_id(client: AsyncClient):
    """GET /workouts/<valid-uuid-not-in-db> → 404."""
    token = await register_and_login(
        client, f"nonexist_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!"
    )
    nonexistent_id = str(uuid.uuid4())
    resp = await client.get(
        f"/workouts/{nonexistent_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_exercises_invalid_priority_tier(client: AsyncClient):
    """GET /exercises/?priority_tier=99 → 422 (out of allowed range 1-3)."""
    resp = await client.get("/exercises/?priority_tier=99")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_workout_invalid_set_type(client: AsyncClient):
    """POST /workouts/ with set_type='INVALID' → 422."""
    token = await register_and_login(
        client, f"inv_set_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!"
    )
    bad_workout = {
        "started_at": "2024-01-15T09:00:00Z",
        "ended_at": "2024-01-15T10:00:00Z",
        "sequences": [
            {
                "phase": "main",
                "position": 0,
                "sets": [
                    {
                        "exercise_id": EXERCISE_ID,
                        "set_type": "INVALID",
                        "position": 0,
                        "reps": 10,
                    },
                ],
            }
        ],
    }
    resp = await client.post(
        "/workouts/",
        json=bad_workout,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 2. Auth edge case tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_malformed_token(client: AsyncClient):
    """GET /auth/me with Authorization: Bearer garbage → 401."""
    resp = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer this.is.garbage"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_expired_token(client: AsyncClient):
    """An expired JWT should be rejected with 401."""
    import time
    import jwt as pyjwt

    from app.config import settings

    # Build a token that expired 60 seconds ago
    now = int(time.time())
    payload = {
        "sub": str(uuid.uuid4()),
        "aud": ["fastapi-users:auth"],
        "exp": now - 60,
        "iat": now - 120,
    }
    expired_token = pyjwt.encode(payload, settings.secret_key, algorithm="HS256")

    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Register user, try login with wrong password → 400."""
    email = f"wrong_pwd_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "S3cur3Pass!"})
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cross_user_workout_access(client: AsyncClient):
    """User B cannot access User A's workout — returns 404 (no info leak)."""
    email_a = f"owner_edge_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"other_edge_{uuid.uuid4().hex[:8]}@example.com"
    token_a = await register_and_login(client, email_a, "S3cur3Pass!")
    token_b = await register_and_login(client, email_b, "S3cur3Pass!")

    create_resp = await client.post(
        "/workouts/",
        json=SAMPLE_WORKOUT,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    workout_id = create_resp.json()["id"]

    resp = await client.get(
        f"/workouts/{workout_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 3. Concurrent request tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_workout_creation(client: AsyncClient):
    """5 concurrent workout creations all succeed with distinct IDs."""
    token = await register_and_login(
        client, f"concurrent_{uuid.uuid4().hex[:8]}@example.com", "S3cur3Pass!"
    )

    async def create_one() -> str:
        resp = await client.post(
            "/workouts/",
            json=SAMPLE_WORKOUT,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    ids = await asyncio.gather(*[create_one() for _ in range(5)])
    # All IDs must be unique — no collision
    assert len(set(ids)) == 5


@pytest.mark.asyncio
async def test_concurrent_exercise_queries(client: AsyncClient):
    """10 concurrent GET /exercises/ all return 200 with 50 results."""

    async def query_exercises() -> int:
        resp = await client.get("/exercises/")
        assert resp.status_code == 200
        return len(resp.json())

    counts = await asyncio.gather(*[query_exercises() for _ in range(10)])
    assert all(c == 50 for c in counts)
