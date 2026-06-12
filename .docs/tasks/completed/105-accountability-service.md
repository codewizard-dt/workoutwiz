# 105 — accountability_service: rank coach action items from adherence + churn-risk signals

> **Depends on**: none
> **Blocks**: [106-coach-nudge-endpoint](106-coach-nudge-endpoint.md), [107-coach-page-action-items](107-coach-page-action-items.md)
> **Parallel-safe with**: [109-coach-draft-persistence](109-coach-draft-persistence.md)

## Objective

Create `backend/app/services/accountability.py` — a pure service module that ranks coach action items from the signals already present in `CoachBriefResponse` (adherence weeks and churn risk). This is Phase 1 of Roadmap 007 and the foundation for `POST /coach/nudge` and the `CoachPage` action-item cards.

## Approach

No new data fetching — the `CoachBriefResponse` schema already exposes `adherence_weeks` (list of `AdherenceWeek(week_of, pct)`) and `churn_risk` (level + reasons). The service consumes these and emits a ranked list of `ActionItem` objects.

Ranking heuristic (in priority order):
1. `high` churn risk → always rank first with reasons as context
2. Adherence `pct < 50` in the most recent week → high priority
3. Adherence `pct < 70` in the most recent week → medium priority
4. All-clear → no items emitted (empty list is valid)

Each `ActionItem` carries: `priority` (high/medium/low), `member_id`, `member_name`, `reason` (human-readable), and `context` (dict of raw signals for nudge-message grounding in Task 106).

New Pydantic schemas live in `backend/app/schemas/coach.py` alongside the existing coaching models. The service function is a synchronous pure function — no DB, no LLM, no I/O — so it's trivially testable.

## Steps

### 1. Add `ActionItem` schema to `backend/app/schemas/coach.py`  <!-- agent: general-purpose -->

Using Serena `insert_after_symbol` after `CoachBriefResponse` (line 61), add:

```python
class ActionItem(BaseModel):
    priority: str  # "high" | "medium" | "low"
    member_id: str
    member_name: str
    reason: str
    context: dict
```

- [x] `ActionItem` class exists in `backend/app/schemas/coach.py` with all five fields <!-- Completed: 2026-06-11 -->
- [x] `ActionItem` is exported from the module (no `__all__` needed — Pydantic classes are importable by default) <!-- Completed: 2026-06-11 -->

### 2. Create `backend/app/services/accountability.py`  <!-- agent: general-purpose -->

```python
from backend.app.schemas.coach import ActionItem, AdherenceWeek, ChurnRisk


def rank_action_items(
    member_id: str,
    member_name: str,
    adherence_weeks: list[AdherenceWeek],
    churn_risk: ChurnRisk,
) -> list[ActionItem]:
    items: list[ActionItem] = []

    if churn_risk.level == "high":
        items.append(ActionItem(
            priority="high",
            member_id=member_id,
            member_name=member_name,
            reason=f"High churn risk: {'; '.join(churn_risk.reasons)}",
            context={"churn_level": churn_risk.level, "churn_reasons": churn_risk.reasons},
        ))

    if adherence_weeks:
        latest = adherence_weeks[-1]
        if latest.pct < 50:
            items.append(ActionItem(
                priority="high",
                member_id=member_id,
                member_name=member_name,
                reason=f"Low adherence this week: {latest.pct}% (week of {latest.week_of})",
                context={"week_of": latest.week_of, "adherence_pct": latest.pct},
            ))
        elif latest.pct < 70:
            items.append(ActionItem(
                priority="medium",
                member_id=member_id,
                member_name=member_name,
                reason=f"Below-target adherence this week: {latest.pct}% (week of {latest.week_of})",
                context={"week_of": latest.week_of, "adherence_pct": latest.pct},
            ))

    # Sort: high > medium > low
    order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda x: order.get(x.priority, 3))
    return items
```

- [x] `backend/app/services/accountability.py` exists <!-- Completed: 2026-06-11 -->
- [x] `rank_action_items` function is defined with the signature above <!-- Completed: 2026-06-11 -->
- [x] Returns an empty list when adherence is healthy and churn risk is not "high" <!-- Completed: 2026-06-11 -->
- [x] Returns items sorted by priority (high first) <!-- Completed: 2026-06-11 -->

### 3. Write unit tests in `backend/tests/services/test_accountability.py`  <!-- agent: general-purpose -->

Create `backend/tests/services/` directory (add `__init__.py`) and write:

```python
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk


def test_high_churn_yields_action_item():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=80)],
        churn_risk=ChurnRisk(level="high", reasons=["3 missed workouts"]),
    )
    assert len(result) == 1
    assert result[0].priority == "high"


def test_low_adherence_yields_high_priority():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=40)],
        churn_risk=ChurnRisk(level="low", reasons=[]),
    )
    assert len(result) == 1
    assert result[0].priority == "high"


def test_medium_adherence_yields_medium_priority():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=60)],
        churn_risk=ChurnRisk(level="low", reasons=[]),
    )
    assert len(result) == 1
    assert result[0].priority == "medium"


def test_healthy_member_yields_empty():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=90)],
        churn_risk=ChurnRisk(level="low", reasons=[]),
    )
    assert result == []


def test_high_churn_plus_low_adherence_sorted_high_first():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=40)],
        churn_risk=ChurnRisk(level="high", reasons=["dropout pattern"]),
    )
    assert all(r.priority == "high" for r in result)
    assert len(result) == 2
```

Run via: `cd backend && python -m pytest tests/services/test_accountability.py -v`

- [x] Test file exists at `backend/tests/services/test_accountability.py` <!-- Completed: 2026-06-11 -->
- [x] All 5 tests pass when run with pytest <!-- Completed: 2026-06-11 -->

## Acceptance Criteria

- [x] `rank_action_items` is importable from `backend.app.services.accountability` <!-- Completed: 2026-06-11 -->
- [x] `ActionItem` schema is importable from `backend.app.schemas.coach` <!-- Completed: 2026-06-11 -->
- [x] A member with `churn_risk.level == "high"` always yields at least one `ActionItem` <!-- Completed: 2026-06-11 -->
- [x] A member with adherence `pct < 50` in the most recent week yields a `high` priority item <!-- Completed: 2026-06-11 -->
- [x] A member with adherence `pct` in 50–69 in the most recent week yields a `medium` priority item <!-- Completed: 2026-06-11 -->
- [x] A member with adherence `pct >= 70` and churn not "high" yields an empty list <!-- Completed: 2026-06-11 -->
- [x] All 5 unit tests pass <!-- Completed: 2026-06-11 -->

---
**UAT**: [`.docs/uat/completed/105-accountability-service.uat.md`](../uat/completed/105-accountability-service.uat.md)
