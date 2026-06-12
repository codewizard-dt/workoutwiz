# 106 — POST /coach/nudge: draft context-grounded nudge message for a flagged member

> **Depends on**: [105-accountability-service](105-accountability-service.md)
> **Blocks**: [107-coach-page-action-items](107-coach-page-action-items.md)
> **Parallel-safe with**: [109-coach-draft-persistence](109-coach-draft-persistence.md)

## Objective

Add `POST /coach/nudge` to `backend/app/routers/coach.py`. The endpoint accepts a flagged member's context and returns a ready-to-send draft nudge message composed by the coach LLM agent, grounded in the `ActionItem.context` produced by `accountability_service`.

## Approach

The nudge message must be grounded in actual member data (goals, injury notes, churn reasons, adherence) — not a generic "keep going!" message. The existing `coach_graph` (LangGraph) in `backend/app/agents/coach.py` already handles context-aware chat; the nudge endpoint routes through it with a purpose-built system prompt addition.

Request body: `NudgeRequest(member_id, member_name, action_item: ActionItem)`.
Response body: `NudgeResponse(draft_message: str, grounded_on: list[str])`.

The endpoint calls `rank_action_items` internally only for validation (the caller must pass a valid ActionItem), then assembles a nudge prompt and runs it through the coach LLM. Since nudges are short (1–3 sentences), use the model directly via `langchain_anthropic.ChatAnthropic` rather than the full graph — keeps latency low and avoids routing overhead.

Implementation pattern mirrors `coach_chat` in `routers/coach.py` — auth via `current_active_user`, async handler, error handling.

## Steps

### 1. Add `NudgeRequest` and `NudgeResponse` schemas to `backend/app/schemas/coach.py`  <!-- agent: general-purpose -->

Using Serena `insert_after_symbol` after `ActionItem`:

```python
class NudgeRequest(BaseModel):
    member_id: str
    member_name: str
    action_item: ActionItem

class NudgeResponse(BaseModel):
    draft_message: str
    grounded_on: list[str]
```

- [x] `NudgeRequest` and `NudgeResponse` classes exist in `backend/app/schemas/coach.py` <!-- Completed: 2026-06-11 -->

### 2. Add `POST /coach/nudge` endpoint to `backend/app/routers/coach.py`  <!-- agent: general-purpose -->

Add after the `coach_chat` function. Use Serena `insert_after_symbol` targeting `coach_chat`:

```python
@router.post(
    "/nudge",
    response_model=NudgeResponse,
    summary="Draft a nudge message for a flagged member",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"model": ErrorResponse, "description": "Invalid action item"},
        500: {"model": ErrorResponse, "description": "LLM error"},
    },
)
async def coach_nudge(
    body: NudgeRequest,
    user: User = Depends(current_active_user),
) -> NudgeResponse:
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=256)
        system = (
            "You are a fitness coach assistant. Write a warm, personal, 1-3 sentence check-in message "
            "to send to a member. Be specific about their situation — reference the reason you are reaching out. "
            "Do not use generic motivational phrases. Sign off as 'Your Coach'."
        )
        grounded_on = [body.action_item.reason]
        human = (
            f"Member: {body.member_name}\n"
            f"Reason for nudge: {body.action_item.reason}\n"
            f"Context: {body.action_item.context}\n\n"
            "Write the nudge message now."
        )
        response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        return NudgeResponse(
            draft_message=response.content,
            grounded_on=grounded_on,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in POST /coach/nudge")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- [x] Endpoint defined with `@router.post("/nudge", response_model=NudgeResponse)` <!-- Completed: 2026-06-11 -->
- [x] Uses `current_active_user` dependency for auth <!-- Completed: 2026-06-11 -->
- [x] Returns `NudgeResponse` with `draft_message` and `grounded_on` <!-- Completed: 2026-06-11 -->
- [x] Uses `claude-haiku-4-5-20251001` model (fast, low-cost for short nudges) <!-- Completed: 2026-06-11 -->
- [x] Exception handling mirrors existing `coach_chat` pattern <!-- Completed: 2026-06-11 -->

### 3. Add `NudgeRequest` / `NudgeResponse` imports to the router  <!-- agent: general-purpose -->

Verify the schema import line in `backend/app/routers/coach.py` includes `NudgeRequest`, `NudgeResponse`, and `ActionItem`. Use Serena `search_for_pattern` to find the existing `from ..schemas.coach import` line, then update it with `replace_content`.

- [x] `NudgeRequest`, `NudgeResponse`, `ActionItem` are imported in `routers/coach.py` <!-- Completed: 2026-06-11 -->

### 4. Manual smoke test  <!-- agent: general-purpose -->

With the stack running (`make up` or `docker compose up`), run:

```bash
set -a && source .env && set +a
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/jwt/login \
  -d "username=alex@example.com&password=password123" | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/coach/nudge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": "demo-member",
    "member_name": "Jordan Rivera",
    "action_item": {
      "priority": "high",
      "member_id": "demo-member",
      "member_name": "Jordan Rivera",
      "reason": "Low adherence this week: 40% (week of 2026-06-01)",
      "context": {"week_of": "2026-06-01", "adherence_pct": 40}
    }
  }' | jq .
```

- [DEFERRED-TO-UAT] Response returns HTTP 200 with a non-empty `draft_message`
- [DEFERRED-TO-UAT] `grounded_on` list contains the reason string

## Acceptance Criteria

- [ ] `POST /coach/nudge` exists and is reachable at `/api/coach/nudge`
- [ ] Returns HTTP 401 when no token is provided
- [ ] Returns HTTP 200 with `draft_message` (non-empty string) and `grounded_on` (non-empty list) when given a valid `NudgeRequest`
- [ ] The generated message references something specific from the `action_item.reason` or `context`
- [ ] No unhandled exceptions — errors return HTTP 500 with a detail message

---
**UAT**: [`.docs/uat/completed/106-coach-nudge-endpoint.uat.md`](../uat/completed/106-coach-nudge-endpoint.uat.md)
