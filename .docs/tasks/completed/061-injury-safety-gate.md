# 061 — Injury Safety Gate: Post-Generation Validation

> **Depends on**: [060-generation-agent-subgraph](060-generation-agent-subgraph.md)
> **Blocks**: [063-fallback-handler](063-fallback-handler.md), [065-kg-fastapi-router](065-kg-fastapi-router.md)
> **Parallel-safe with**: [062-explainability-tool](062-explainability-tool.md)

## Objective

Add a `safety_gate` node to the generation graph (`backend/app/kg/generation_graph.py`) that runs after `generate_workout`. It checks each recommended exercise's `exercise_id` against `context.contraindicated_ids` (populated by the retrieval sub-graph) and removes any violations. If any violation is found, the removed exercise IDs are recorded in `recommendation.skipped_exercise_ids`.

## Approach

The LLM is instructed to only pick from `safe_exercises`, but the safety gate is a hard post-generation check: even if the LLM ignores the constraint, unsafe exercises are filtered out before the response is returned.

**Safety gate logic:**
```python
def _safety_gate_node(state: GenerationState) -> dict:
    if state.get("fallback_triggered") or not state.get("recommendation"):
        return {}
    context = state["context"]
    contraindicated = set(context.get("contraindicated_ids", []))
    rec = state["recommendation"]
    safe = [e for e in rec.exercises if e.exercise_id not in contraindicated]
    removed = [e.exercise_id for e in rec.exercises if e.exercise_id in contraindicated]
    if removed:
        rec = rec.model_copy(update={
            "exercises": safe,
            "skipped_exercise_ids": rec.skipped_exercise_ids + removed,
            "overall_reasoning": rec.overall_reasoning + f" (Removed {len(removed)} contraindicated exercise(s).)",
        })
    return {"recommendation": rec}
```

Wire `safety_gate` between `generate_workout` and `format_response` in the graph.

**Also**: if `len(safe) < 2` after filtering (fallback threshold), set `fallback_triggered = True` so the fallback handler (TASK-063) can pick it up.

## Steps

### 1. Inspect `generation_graph.py`  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/kg/generation_graph.py`. Confirm the exact node sequence and how `GenerationState` is defined.

- [x] Node sequence and `GenerationState` fields confirmed <!-- Completed: 2026-06-06 -->

### 2. Add `_safety_gate_node` to `backend/app/kg/generation_graph.py`  <!-- agent: general-purpose -->

Use Serena `replace_content` to:
1. Add the `_safety_gate_node` function (code above, adjusted to actual field names).
2. Re-wire edges in `build_generation_graph()`: `generate_workout → safety_gate → format_response`.

```python
builder.add_edge("generate_workout", "safety_gate")
builder.add_edge("safety_gate", "format_response")
```

- [x] `_safety_gate_node` added and wired into graph <!-- Completed: 2026-06-06 -->
- [x] `fallback_triggered` set to `True` when fewer than 2 safe exercises remain <!-- Completed: 2026-06-06 -->

### 3. Add tests to `backend/tests/kg/test_generation_graph.py`  <!-- agent: general-purpose -->

Add:
- `test_safety_gate_removes_contraindicated_exercise`: set up context with `contraindicated_ids={"ex-1"}`, mock LLM to return recommendation with `ex-1` in exercises, assert `ex-1` is in `skipped_exercise_ids` and not in final exercises.
- `test_safety_gate_passes_clean_recommendation`: no contraindicated IDs; assert recommendation unchanged.
- `test_safety_gate_triggers_fallback_when_too_few_exercises`: after gate removes exercises leaving 0 or 1 valid, assert `fallback_triggered=True`.

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py -v
```

- [x] ≥3 new safety gate tests added and passing <!-- Completed: 2026-06-06 -->

### 4. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 5 safety gate placeholder with `[TASK-061: Injury safety gate...](../tasks/061-injury-safety-gate.md)`.

- [x] Roadmap updated <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `_safety_gate_node` added to `generation_graph.py`, wired between `generate_workout` and `format_response`
- [x] Any exercise in `context.contraindicated_ids` is removed from `recommendation.exercises`
- [x] Removed exercise IDs appended to `recommendation.skipped_exercise_ids`
- [x] `fallback_triggered=True` when ≤1 exercise survives the gate
- [x] ≥3 safety gate tests passing

---
**UAT**: [`.docs/uat/061-injury-safety-gate.uat.md`](../uat/061-injury-safety-gate.uat.md)
