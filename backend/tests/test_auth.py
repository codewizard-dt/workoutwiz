import pytest
from httpx import AsyncClient


async def register_and_login(client: AsyncClient, email: str, password: str) -> str:
    """Register a user and return a JWT access token."""
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"email": "register_ok@example.com", "password": "S3cur3Pass!"},
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["email"] == "register_ok@example.com"
    assert "id" in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "S3cur3Pass!"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    email, password = "login_ok@example.com", "S3cur3Pass!"
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    email = "wrong_pw@example.com"
    await client.post("/auth/register", json={"email": email, "password": "correct!"})
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": "wrong!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    email, password = "get_me@example.com", "S3cur3Pass!"
    token = await register_and_login(client, email, password)
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == email
    assert "id" in body


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
