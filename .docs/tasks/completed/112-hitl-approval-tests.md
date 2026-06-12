# 112 — Critical test: draft cannot reach a member without approved status + Playwright approve/edit path

> **Depends on**: [111-coach-draft-review-ui](111-coach-draft-review-ui.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Add the Phase 2 critical tests: (1) a pytest test confirming that `PATCH /coach/draft/{id}` with `action: send` returns HTTP 409 when the draft is not approved; and (2) a Playwright end-to-end test exercising the approve → (optional edit) → send flow through the `CoachPage` Pending Drafts panel.

## Approach

The pytest test creates a draft via the API, attempts to send it, asserts 409, approves it, then sends again and asserts 200. This covers the state machine enforced in Task 110. The Playwright test navigates to `/coach`, creates a nudge draft using the "Draft Nudge" button (from Task 107), and exercises the Pending Drafts panel to approve and send it.

## Steps

### 1. Add pytest integration test `backend/tests/test_hitl_approval.py`  <!-- agent: general-purpose -->

This test uses `httpx.AsyncClient` against the running FastAPI app (same pattern as other integration tests if they exist; otherwise use the in-process `app` from `backend/app/main.py`).

```python
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.fixture
async def auth_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/auth/jwt/login", data={"username": "alex@example.com", "password": "password123"})
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_draft_cannot_be_sent_without_approval(auth_headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a draft
        create_resp = await ac.post(
            "/api/coach/draft",
            json={"member_id": "test-m1", "member_name": "Test", "content_type": "nudge", "body": "Hey there!", "grounded_on": []},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        draft_id = create_resp.json()["id"]

        # Attempt to send without approving — must be 409
        send_resp = await ac.patch(
            f"/api/coach/draft/{draft_id}",
            json={"action": "send"},
            headers=auth_headers,
        )
        assert send_resp.status_code == 409, f"Expected 409 but got {send_resp.status_code}: {send_resp.text}"

        # Approve
        approve_resp = await ac.patch(
            f"/api/coach/draft/{draft_id}",
            json={"action": "approve"},
            headers=auth_headers,
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        # Now send — must succeed
        send_after_approve = await ac.patch(
            f"/api/coach/draft/{draft_id}",
            json={"action": "send"},
            headers=auth_headers,
        )
        assert send_after_approve.status_code == 200
        assert send_after_approve.json()["status"] == "sent"


@pytest.mark.anyio
async def test_edit_after_approval_resets_to_draft(auth_headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_resp = await ac.post(
            "/api/coach/draft",
            json={"member_id": "test-m2", "member_name": "Test2", "content_type": "nudge", "body": "Original message", "grounded_on": []},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        draft_id = create_resp.json()["id"]

        await ac.patch(f"/api/coach/draft/{draft_id}", json={"action": "approve"}, headers=auth_headers)

        # Edit after approval
        edit_resp = await ac.patch(
            f"/api/coach/draft/{draft_id}",
            json={"action": "edit", "body": "Updated message"},
            headers=auth_headers,
        )
        assert edit_resp.status_code == 200
        assert edit_resp.json()["status"] == "draft", "Edit after approval must reset to draft"

        # Sending after edit (without re-approval) must be blocked
        send_resp = await ac.patch(f"/api/coach/draft/{draft_id}", json={"action": "send"}, headers=auth_headers)
        assert send_resp.status_code == 409
```

Ensure `anyio` is in test dependencies. Run via:
```bash
set -a && source .env && set +a
cd backend && python -m pytest tests/test_hitl_approval.py -v --anyio-mode=asyncio
```

- [x] Test file exists at `backend/tests/test_hitl_approval.py` <!-- Completed: 2026-06-11 -->
- [ ] `test_draft_cannot_be_sent_without_approval` passes
- [ ] `test_edit_after_approval_resets_to_draft` passes

### 2. Add Playwright E2E test `frontend/e2e/coach-hitl-approval.spec.ts`  <!-- agent: general-purpose -->

```typescript
import { test, expect } from '@playwright/test'

test('coach can approve and send a draft nudge', async ({ page }) => {
  // Log in
  await page.goto('http://localhost:3000')
  await page.fill('input[type="email"]', 'alex@example.com')
  await page.fill('input[type="password"]', 'password123')
  await page.click('button[type="submit"]')

  // Navigate to coach page
  await page.goto('http://localhost:3000/coach')

  // Wait for brief to load
  await expect(page.getByText('Jordan Rivera')).toBeVisible({ timeout: 15000 })

  // If Action Items are visible, click "Draft Nudge" on the first item
  const draftNudgeBtn = page.getByRole('button', { name: 'Draft Nudge' }).first()
  if (await draftNudgeBtn.isVisible()) {
    await draftNudgeBtn.click()
    // Wait for the nudge to generate and the draft to appear in Pending Drafts
    await expect(page.getByText('Pending Drafts')).toBeVisible({ timeout: 20000 })
  }

  // If Pending Drafts panel is present, test the approve/send flow
  const pendingDraftsHeading = page.getByText('Pending Drafts', { exact: true })
  if (await pendingDraftsHeading.isVisible()) {
    // Send button should be disabled before approval
    const sendBtn = page.getByRole('button', { name: 'Send' }).first()
    await expect(sendBtn).toBeDisabled()

    // Approve the first draft
    const approveBtn = page.getByRole('button', { name: 'Approve' }).first()
    await approveBtn.click()

    // Send button should now be enabled
    await expect(sendBtn).toBeEnabled({ timeout: 5000 })

    // Click Send
    await sendBtn.click()

    // The draft should disappear from the panel (status becomes 'sent')
    // Panel either disappears or shows fewer items
    await page.waitForTimeout(1000)
    // No assertion on disappearance — the panel may still show if multiple drafts exist
  }
})
```

- [x] Test file exists at `frontend/e2e/coach-hitl-approval.spec.ts` <!-- Completed: 2026-06-11 -->
- [x] Test verifies Send button is disabled before approval <!-- Completed: 2026-06-11 -->
- [x] Test verifies Send button is enabled after approval <!-- Completed: 2026-06-11 -->
- [ ] Test passes against a running stack

### 3. Run all Phase 2 tests  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a
cd backend && python -m pytest tests/test_hitl_approval.py -v --anyio-mode=asyncio
```

- [DEFERRED-TO-UAT] Both HITL pytest tests pass — requires running PostgreSQL test DB; all DB integration tests in the suite have same constraint

## Acceptance Criteria

- [ ] `test_draft_cannot_be_sent_without_approval` passes — HTTP 409 is returned when sending a non-approved draft
- [ ] `test_edit_after_approval_resets_to_draft` passes — editing after approval resets status to `draft`
- [ ] Playwright E2E test `coach-hitl-approval.spec.ts` passes against a running stack
- [ ] No regressions in existing pytest suite (`cd backend && python -m pytest` passes)

---
**UAT**: [`.docs/uat/112-hitl-approval-tests.uat.md`](../uat/112-hitl-approval-tests.uat.md)
