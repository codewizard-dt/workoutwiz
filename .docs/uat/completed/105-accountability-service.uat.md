# UAT: accountability_service — rank coach action items

> **Source task**: [`.docs/tasks/105-accountability-service.md`](../tasks/105-accountability-service.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Virtual environment installed: `make install` (or `backend/.venv` already exists)
- [ ] All tests discovered from a project-root shell: `backend/.venv/bin/pytest backend/tests/services/test_accountability.py -v`

---

## Integration Tests

### UAT-INT-001: Module is importable from the package path required by downstream tasks

- **Components**: `backend/app/services/accountability.py`, `backend/app/schemas/coach.py`
- **Flow**: Downstream tasks 106 and 107 import `rank_action_items` from `backend.app.services.accountability` and `ActionItem` from `backend.app.schemas.coach`. This test confirms both imports resolve without error.
- **Steps**:
  1. Run the command below from the project root (no server needed).
- **Command**:
  ```bash
  backend/.venv/bin/python -c "from backend.app.services.accountability import rank_action_items; from backend.app.schemas.coach import ActionItem, AdherenceWeek, ChurnRisk; print('imports ok')"
  ```
- **Expected Result**: Prints `imports ok` with exit code 0. No `ModuleNotFoundError` or `ImportError`.
- [x] Pass <!-- 2026-06-11 -->

---

## Edge Case Tests

### UAT-EDGE-001: High churn risk always yields at least one high-priority action item

- **Scenario**: Member has `churn_risk.level == "high"` regardless of adherence.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=80)], ChurnRisk(level='high', reasons=['3 missed workouts']))
assert len(result) >= 1, f'Expected >=1 item, got {len(result)}'
assert result[0].priority == 'high', f'Expected high, got {result[0].priority}'
assert 'high churn risk' in result[0].reason.lower(), f'Unexpected reason: {result[0].reason}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-002: Adherence pct < 50 in most recent week yields high-priority item

- **Scenario**: Member has low churn risk but latest adherence week is 40% (below 50 threshold).
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=40)], ChurnRisk(level='low', reasons=[]))
assert len(result) == 1, f'Expected 1 item, got {len(result)}'
assert result[0].priority == 'high', f'Expected high, got {result[0].priority}'
assert result[0].context['adherence_pct'] == 40, f'Wrong context pct: {result[0].context}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-003: Adherence pct in 50–69 range yields medium-priority item

- **Scenario**: Member has low churn risk and latest adherence week is 60% (between 50 and 69 inclusive).
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=60)], ChurnRisk(level='low', reasons=[]))
assert len(result) == 1, f'Expected 1 item, got {len(result)}'
assert result[0].priority == 'medium', f'Expected medium, got {result[0].priority}'
assert result[0].context['adherence_pct'] == 60, f'Wrong context pct: {result[0].context}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-004: Healthy member (pct >= 70, churn not high) yields empty list

- **Scenario**: Member has adherence 90% and churn level "low". All-clear — no action items expected.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=90)], ChurnRisk(level='low', reasons=[]))
assert result == [], f'Expected empty list, got {result}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-005: High churn AND low adherence yields two high-priority items, high-first sort preserved

- **Scenario**: Both signals fire simultaneously. The function must return two `ActionItem` objects, both `priority="high"`, with the churn item sorted before the adherence item (or both equally high — sort stability test).
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=40)], ChurnRisk(level='high', reasons=['dropout pattern']))
assert len(result) == 2, f'Expected 2 items, got {len(result)}'
assert all(r.priority == 'high' for r in result), f'Not all high: {[r.priority for r in result]}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-006: Empty adherence_weeks list with non-high churn yields empty list

- **Scenario**: No adherence data available and churn is "low". The adherence branch must be skipped entirely.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import ChurnRisk
result = rank_action_items('m1', 'Alice', [], ChurnRisk(level='low', reasons=[]))
assert result == [], f'Expected empty list, got {result}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-007: Adherence boundary — exactly pct=50 yields medium (not high) priority

- **Scenario**: The `pct < 50` threshold is exclusive. A member at exactly 50% should get a medium item, not high.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=50)], ChurnRisk(level='low', reasons=[]))
assert len(result) == 1, f'Expected 1 item, got {len(result)}'
assert result[0].priority == 'medium', f'Expected medium at pct=50, got {result[0].priority}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-008: Adherence boundary — exactly pct=70 yields empty list (not medium)

- **Scenario**: The `pct < 70` threshold is exclusive. A member at exactly 70% with low churn should get no items.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=70)], ChurnRisk(level='low', reasons=[]))
assert result == [], f'Expected empty list at pct=70, got {result}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-009: Only the most recent adherence week is evaluated (last element used)

- **Scenario**: Multiple weeks provided. Only the last element (`adherence_weeks[-1]`) should be evaluated. Earlier low weeks must not trigger items when the latest week is healthy.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-05-25', pct=30), AdherenceWeek(week_of='2026-06-01', pct=85)], ChurnRisk(level='low', reasons=[]))
assert result == [], f'Expected empty list (latest week healthy), got {result}'
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-010: ActionItem context dict carries correct keys for churn item

- **Scenario**: Churn-triggered item must carry `churn_level` and `churn_reasons` keys in `context` so Task 106 nudge endpoint can use them.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=80)], ChurnRisk(level='high', reasons=['missed 3 weeks']))
item = result[0]
assert 'churn_level' in item.context, f'Missing churn_level: {item.context}'
assert 'churn_reasons' in item.context, f'Missing churn_reasons: {item.context}'
assert item.context['churn_level'] == 'high'
assert item.context['churn_reasons'] == ['missed 3 weeks']
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-011: ActionItem context dict carries correct keys for adherence item

- **Scenario**: Adherence-triggered item must carry `week_of` and `adherence_pct` keys in `context` so Task 106 nudge endpoint can use them.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from backend.app.services.accountability import rank_action_items
from backend.app.schemas.coach import AdherenceWeek, ChurnRisk
result = rank_action_items('m1', 'Alice', [AdherenceWeek(week_of='2026-06-01', pct=40)], ChurnRisk(level='low', reasons=[]))
item = result[0]
assert 'week_of' in item.context, f'Missing week_of: {item.context}'
assert 'adherence_pct' in item.context, f'Missing adherence_pct: {item.context}'
assert item.context['week_of'] == '2026-06-01'
assert item.context['adherence_pct'] == 40
print('PASS')
"
  ```
- **Expected Result**: Prints `PASS` with exit code 0.
- [x] Pass <!-- 2026-06-11 -->

---

## Unit Test Suite

### UAT-UNIT-001: All 5 pytest unit tests pass

- **Components**: `backend/tests/services/test_accountability.py`, `backend/app/services/accountability.py`
- **Flow**: Run the full pytest suite for the accountability service. All 5 tests must pass; 0 failures, 0 errors.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/services/test_accountability.py -v
  ```
- **Expected Result**: Output shows `5 passed` with exit code 0. Tests: `test_high_churn_yields_action_item`, `test_low_adherence_yields_high_priority`, `test_medium_adherence_yields_medium_priority`, `test_healthy_member_yields_empty`, `test_high_churn_plus_low_adherence_sorted_high_first`.
- [x] Pass <!-- 2026-06-11 -->
