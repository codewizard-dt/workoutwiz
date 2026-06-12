# 110 — PATCH /coach/draft/{id}: approve / edit / send lifecycle endpoint

> **Depends on**: [109-coach-draft-persistence](109-coach-draft-persistence.md)
> **Blocks**: [111-coach-draft-review-ui](111-coach-draft-review-ui.md)
> **Parallel-safe with**: [107-coach-page-action-items](107-coach-page-action-items.md), [108-accountability-engine-tests](108-accountability-engine-tests.md)

## Objective

Add three PATCH endpoints to `backend/app/routers/coach.py` to manage the `coach_draft` lifecycle: approve a draft, edit its body, and mark it sent. A draft that is not `approved` must be blocked from the `sent` transition.

## Approach

The endpoints reuse the `AsyncSession` dependency already wired in other routers (e.g. `routers/kg.py`). Transitions are enforced via a simple state machine: `draft → approved → sent`. Editing is only permitted when `status == draft` or `status == approved` (not after `sent`). Approving again is a no-op if already approved. These rules are enforced in the endpoint handler — no separate state machine class needed (YAGNI).

Also add `POST /coach/draft` to create a draft from a nudge (called internally by `POST /coach/nudge` after Task 110 lands). The nudge endpoint saves its draft so it can be reviewed before sending.

Reference patterns: `routers/kg.py` for `AsyncSession` + `current_active_user` usage.

## Steps

### 1. Add `AsyncSession` dependency to `routers/coach.py`  <!-- agent: general-purpose -->

Check whether `AsyncSession` and `get_async_session` are already imported. If not, use Serena `search_for_pattern` on `backend/app/routers/coach.py` for `from ..database`. Add the import:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_session
```

And import the model and schema:
```python
from ..models.coach_draft import CoachDraft, CoachDraftStatus, CoachDraftContentType
from ..schemas.coach import CoachDraftSchema
```

- [x] Imports added to `backend/app/routers/coach.py` <!-- Completed: 2026-06-11 -->

### 2. Add `POST /coach/draft` endpoint  <!-- agent: general-purpose -->

Add after `coach_nudge`:

```python
class CreateDraftRequest(BaseModel):
    member_id: str
    member_name: str
    content_type: str  # "nudge" | "recommendation"
    body: str
    grounded_on: list[str] = []

@router.post(
    "/draft",
    response_model=CoachDraftSchema,
    summary="Save an AI-generated draft for coach review",
    status_code=201,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "DB error"},
    },
)
async def create_coach_draft(
    body: CreateDraftRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> CoachDraftSchema:
    import json
    try:
        draft = CoachDraft(
            member_id=body.member_id,
            member_name=body.member_name,
            content_type=CoachDraftContentType(body.content_type),
            body=body.body,
            grounded_on=json.dumps(body.grounded_on) if body.grounded_on else None,
            status=CoachDraftStatus.draft,
            created_by=user.email,
        )
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        return _draft_to_schema(draft)
    except Exception as exc:
        await db.rollback()
        logger.exception("Error creating coach draft")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [x] `POST /coach/draft` endpoint exists and returns 201 with `CoachDraftSchema` <!-- Completed: 2026-06-11 -->

### 3. Add `PATCH /coach/draft/{draft_id}` endpoint  <!-- agent: general-purpose -->

Add after `create_coach_draft`:

```python
class PatchDraftRequest(BaseModel):
    action: str  # "approve" | "edit" | "send"
    body: str | None = None  # required when action == "edit"

@router.patch(
    "/draft/{draft_id}",
    response_model=CoachDraftSchema,
    summary="Approve, edit, or send a coach draft",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Draft not found"},
        409: {"model": ErrorResponse, "description": "Invalid status transition"},
        500: {"model": ErrorResponse, "description": "DB error"},
    },
)
async def patch_coach_draft(
    draft_id: str,
    body: PatchDraftRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> CoachDraftSchema:
    import uuid, json
    from datetime import datetime, timezone
    from sqlalchemy import select

    try:
        result = await db.execute(
            select(CoachDraft).where(CoachDraft.id == uuid.UUID(draft_id))
        )
        draft = result.scalar_one_or_none()
        if draft is None:
            raise HTTPException(status_code=404, detail="Draft not found")

        if body.action == "approve":
            if draft.status == CoachDraftStatus.sent:
                raise HTTPException(status_code=409, detail="Cannot approve a sent draft")
            draft.status = CoachDraftStatus.approved
            draft.approved_by = user.email
            draft.approved_at = datetime.now(timezone.utc)

        elif body.action == "edit":
            if draft.status == CoachDraftStatus.sent:
                raise HTTPException(status_code=409, detail="Cannot edit a sent draft")
            if not body.body:
                raise HTTPException(status_code=422, detail="body is required for edit action")
            draft.body = body.body
            # Reset to draft when edited after approval
            if draft.status == CoachDraftStatus.approved:
                draft.status = CoachDraftStatus.draft
                draft.approved_by = None
                draft.approved_at = None

        elif body.action == "send":
            if draft.status != CoachDraftStatus.approved:
                raise HTTPException(
                    status_code=409,
                    detail="Draft must be approved before it can be sent",
                )
            draft.status = CoachDraftStatus.sent
            draft.sent_at = datetime.now(timezone.utc)

        else:
            raise HTTPException(status_code=422, detail=f"Unknown action: {body.action}")

        await db.commit()
        await db.refresh(draft)
        return _draft_to_schema(draft)

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Error patching coach draft")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [x] `PATCH /coach/draft/{draft_id}` endpoint exists <!-- Completed: 2026-06-11 -->
- [x] `send` action blocked with HTTP 409 when status is not `approved` <!-- Completed: 2026-06-11 -->
- [x] `edit` action resets `approved` → `draft` to enforce re-approval <!-- Completed: 2026-06-11 -->
- [x] `approve` action blocked on `sent` drafts with HTTP 409 <!-- Completed: 2026-06-11 -->

### 4. Add `GET /coach/draft` list endpoint  <!-- agent: general-purpose -->

Add a basic list endpoint so the frontend can fetch all pending drafts:

```python
@router.get(
    "/draft",
    response_model=list[CoachDraftSchema],
    summary="List all coach drafts for the current coach",
    responses={401: {"model": ErrorResponse, "description": "Not authenticated"}},
)
async def list_coach_drafts(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    status: str | None = None,
) -> list[CoachDraftSchema]:
    from sqlalchemy import select
    try:
        q = select(CoachDraft).order_by(CoachDraft.created_at.desc())
        if status:
            q = q.where(CoachDraft.status == CoachDraftStatus(status))
        result = await db.execute(q)
        return [_draft_to_schema(d) for d in result.scalars().all()]
    except Exception as exc:
        logger.exception("Error listing coach drafts")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [x] `GET /coach/draft` endpoint exists and returns a list of drafts <!-- Completed: 2026-06-11 -->
- [x] Optional `?status=draft` query parameter filters by status <!-- Completed: 2026-06-11 -->

### 5. Add `_draft_to_schema` helper function  <!-- agent: general-purpose -->

Add a private helper near the top of the relevant section in `routers/coach.py`:

```python
def _draft_to_schema(draft: CoachDraft) -> CoachDraftSchema:
    import json
    grounded_on: list[str] = []
    if draft.grounded_on:
        try:
            grounded_on = json.loads(draft.grounded_on)
        except (ValueError, TypeError):
            grounded_on = [draft.grounded_on]
    return CoachDraftSchema(
        id=str(draft.id),
        member_id=draft.member_id,
        member_name=draft.member_name,
        content_type=draft.content_type.value,
        body=draft.body,
        grounded_on=grounded_on,
        status=draft.status.value,
        created_by=draft.created_by,
        approved_by=draft.approved_by,
        approved_at=draft.approved_at.isoformat() if draft.approved_at else None,
        sent_at=draft.sent_at.isoformat() if draft.sent_at else None,
        created_at=draft.created_at.isoformat(),
    )
```

- [x] `_draft_to_schema` helper function exists in `backend/app/routers/coach.py` <!-- Completed: 2026-06-11 -->

### 6. Wire `POST /coach/nudge` to persist a draft  <!-- agent: general-purpose -->

Update the `coach_nudge` endpoint (from Task 106) to also persist the generated message as a `CoachDraft` with status `draft`. Add a `db: AsyncSession = Depends(get_async_session)` parameter and call `create_coach_draft`-equivalent logic inline after generating the message.

Use Serena `replace_symbol_body` on `coach_nudge` to add DB persistence. The updated signature:

```python
async def coach_nudge(
    body: NudgeRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> NudgeResponse:
```

After generating `response.content`, add:
```python
import json
draft = CoachDraft(
    member_id=body.member_id,
    member_name=body.member_name,
    content_type=CoachDraftContentType.nudge,
    body=response.content,
    grounded_on=json.dumps(grounded_on),
    status=CoachDraftStatus.draft,
    created_by=user.email,
)
db.add(draft)
await db.commit()
```

And add `draft_id` to the `NudgeResponse` schema so the frontend can navigate to it:
- Add `draft_id: str | None = None` to `NudgeResponse` in `schemas/coach.py`
- Return `draft_id=str(draft.id)` in the response

- [x] `POST /coach/nudge` now persists a `CoachDraft` row with `status=draft` <!-- Completed: 2026-06-11 -->
- [x] `NudgeResponse.draft_id` field exists and is populated <!-- Completed: 2026-06-11 -->

### 7. Smoke test  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/jwt/login \
  -d "username=alex@example.com&password=password123" | jq -r .access_token)

# Create a draft
DRAFT=$(curl -s -X POST http://localhost:8000/api/coach/draft \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"member_id":"m1","member_name":"Jordan","content_type":"nudge","body":"Hey Jordan!","grounded_on":["low adherence"]}')
echo "$DRAFT" | jq .
DRAFT_ID=$(echo "$DRAFT" | jq -r .id)

# Try to send without approving (must fail with 409)
curl -s -X PATCH "http://localhost:8000/api/coach/draft/$DRAFT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"send"}' | jq .status_code

# Approve
curl -s -X PATCH "http://localhost:8000/api/coach/draft/$DRAFT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"approve"}' | jq .status

# Now send
curl -s -X PATCH "http://localhost:8000/api/coach/draft/$DRAFT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"send"}' | jq .status
```

- [DEFERRED-TO-UAT] Creating a draft returns HTTP 201 with `status: "draft"`
- [DEFERRED-TO-UAT] Sending without approval returns HTTP 409
- [DEFERRED-TO-UAT] After approval, sending returns HTTP 200 with `status: "sent"`

## Acceptance Criteria

- [x] `POST /coach/draft` creates a draft with `status: "draft"` (HTTP 201)
- [x] `PATCH /coach/draft/{id}` with `action: "send"` returns HTTP 409 when status is `draft`
- [x] `PATCH /coach/draft/{id}` with `action: "approve"` transitions status to `approved`
- [x] `PATCH /coach/draft/{id}` with `action: "send"` returns HTTP 200 with `status: "sent"` after approval
- [x] `PATCH /coach/draft/{id}` with `action: "edit"` resets `approved` → `draft`
- [x] `GET /coach/draft` returns a list of all drafts
- [x] `POST /coach/nudge` now persists a `CoachDraft` and returns `draft_id` in the response
- [DEFERRED-TO-UAT] All endpoints return HTTP 401 when called without a token

---
**UAT**: [`.docs/uat/110-coach-draft-lifecycle-endpoint.uat.md`](../uat/110-coach-draft-lifecycle-endpoint.uat.md)
