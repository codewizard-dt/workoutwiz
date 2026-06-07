# 087 — Fix Stale test_intent_values Assertion (add KNOWLEDGE_GRAPH)

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [086-readme-kg-production-eval](086-readme-kg-production-eval.md), [088-build-workout-cooldown-phase](088-build-workout-cooldown-phase.md), [089-subagent-llm-error-handling](089-subagent-llm-error-handling.md)

## Objective

Update the stale `test_intent_values` unit test so its expected set includes the `KNOWLEDGE_GRAPH` member that was added to the `Intent` enum.

## Approach

`backend/app/agents/state.py` defines `Intent` with five members (`COACH`, `WORKOUT_GENERATE`, `WORKOUT_LOG`, `FALLBACK`, `KNOWLEDGE_GRAPH`), but `test_intent_values` in `backend/tests/test_agents_state.py` still asserts the old four-value set, so it fails. Add `Intent.KNOWLEDGE_GRAPH` to the expected set in that one assertion.

## Prerequisites

- [ ] Backend virtualenv is available and `python -m pytest` runs from `backend/`
- [ ] `.env` is present (the verification command sources it)

---

## Steps

### 1. Update the expected-set assertion  <!-- agent: general-purpose -->

- [ ] Edit `backend/tests/test_agents_state.py`, function `test_intent_values`, and change the single assertion so the expected set includes the new enum member.
  - Current (stale) line: `assert set(Intent) == {Intent.COACH, Intent.WORKOUT_GENERATE, Intent.WORKOUT_LOG, Intent.FALLBACK}`
  - New line: `assert set(Intent) == {Intent.COACH, Intent.WORKOUT_GENERATE, Intent.WORKOUT_LOG, Intent.FALLBACK, Intent.KNOWLEDGE_GRAPH}`
  - Do not change the function name, signature, or any other line; this is a one-line edit.

### 2. Verification  <!-- agent: general-purpose -->

- [ ] Run `set -a && source .env && set +a && cd backend && python -m pytest tests/test_agents_state.py -v` and confirm pass
  - Confirm `test_intent_values` reports `PASSED` (the other tests in the file, `test_route_decision_valid` and `test_route_decision_confidence_bounds`, should remain passing).

## Acceptance Criteria

- [ ] The expected set in `test_intent_values` (`backend/tests/test_agents_state.py`) contains all five members, including `Intent.KNOWLEDGE_GRAPH`.
- [ ] `python -m pytest tests/test_agents_state.py -v` passes with no failures.
- [ ] No other file is modified.

---
**UAT**: [`.docs/uat/087-fix-stale-intent-values-test.uat.md`](../uat/087-fix-stale-intent-values-test.uat.md)
