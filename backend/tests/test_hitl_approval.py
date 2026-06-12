import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_draft_cannot_be_sent_without_approval(client: AsyncClient):
    # Register + login
    email = "hitl_test1@example.com"
    password = "TestPass123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_resp = await client.post("/auth/jwt/login", data={"username": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a draft
    create_resp = await client.post(
        "/coach/draft",
        json={"member_id": "test-m1", "member_name": "Test", "content_type": "nudge", "body": "Hey there!", "grounded_on": []},
        headers=headers,
    )
    assert create_resp.status_code == 201
    draft_id = create_resp.json()["id"]

    # Attempt to send without approving — must be 409
    send_resp = await client.patch(
        f"/coach/draft/{draft_id}",
        json={"action": "send"},
        headers=headers,
    )
    assert send_resp.status_code == 409, f"Expected 409 but got {send_resp.status_code}: {send_resp.text}"

    # Approve
    approve_resp = await client.patch(
        f"/coach/draft/{draft_id}",
        json={"action": "approve"},
        headers=headers,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # Now send — must succeed
    send_after_approve = await client.patch(
        f"/coach/draft/{draft_id}",
        json={"action": "send"},
        headers=headers,
    )
    assert send_after_approve.status_code == 200
    assert send_after_approve.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_edit_after_approval_resets_to_draft(client: AsyncClient):
    # Register + login
    email = "hitl_test2@example.com"
    password = "TestPass123!"
    await client.post("/auth/register", json={"email": email, "password": password})
    login_resp = await client.post("/auth/jwt/login", data={"username": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/coach/draft",
        json={"member_id": "test-m2", "member_name": "Test2", "content_type": "nudge", "body": "Original message", "grounded_on": []},
        headers=headers,
    )
    assert create_resp.status_code == 201
    draft_id = create_resp.json()["id"]

    await client.patch(f"/coach/draft/{draft_id}", json={"action": "approve"}, headers=headers)

    # Edit after approval
    edit_resp = await client.patch(
        f"/coach/draft/{draft_id}",
        json={"action": "edit", "body": "Updated message"},
        headers=headers,
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["status"] == "draft", "Edit after approval must reset to draft"

    # Sending after edit (without re-approval) must be blocked
    send_resp = await client.patch(f"/coach/draft/{draft_id}", json={"action": "send"}, headers=headers)
    assert send_resp.status_code == 409
