# 063 — Fallback Handler: Surface Alternatives When Safe Exercises Are Too Few

> **Depends on**: [060-generation-agent-subgraph](060-generation-agent-subgraph.md), [061-injury-safety-gate](061-injury-safety-gate.md)
> **Blocks**: [065-kg-fastapi-router](065-kg-fastapi-router.md)
> **Parallel-safe with**: [062-explainability-tool](062-explainability-tool.md)

## Objective

Add a `fallback_node` to the generation graph that runs when `fallback_triggered=True`. It picks the top-3 exercises from `context.safe_exercises` (sorted by any available rating, or just the first 3), builds a minimal `WorkoutRecommendation` with those exercises, and sets `overall_reasoning` to explain why the fallback was used.

## Approach

The fallback node is added to `generation_graph.py`. The conditional edge after `validate_context` (and after `safety_gate`) routes to `fallback_node` when `fallback_triggered=True`, then proceeds to `format_response` and END.

**Fallback node logic:**
```python
def _fallback_node(state: GenerationState) -> dict:
    context = state.get("context") or {}
    safe = context.get("safe_exercises", [])[:3]
    exercises = [
        RecommendedExercise(
            exercise_id=e["id"],
            name=e.get("name", e["id"]),
            sets=3,
            reps=10,
            reasoning="Selected as a safe alternative given your current injury profile.",
        )
        for e in safe
    ]
    rec = WorkoutRecommendation(
        exercises=exercises,
        overall_reasoning=(
            "Limited exercise options are available due to injury constraints. "
            "These are the safest alternatives from your profile."
        ),
        member_id=state.get("member_id", ""),
        skipped_exercise_ids=state.get("recommendation", WorkoutRecommendation(exercises=[], overall_reasoning="", member_id="")).skipped_exercise_ids
        if state.get("recommendation") else [],
    )
    return {"recommendation": rec}
```

**Graph re-wiring:** the conditional edge after `safety_gate` should route to `fallback_node` when `fallback_triggered`, otherwise `format_response`.

## Steps

### 1. Add `_fallback_node` to `backend/app/kg/generation_graph.py`  <!-- agent: general-purpose -->

Use Serena `replace_content` to:
1. Add `_fallback_node` function (code above, adjust to actual type names).
2. Update the graph to add `"fallback"` node and wire:
   - After `safety_gate`: conditional edge → `"fallback"` if `fallback_triggered`, else `"format_response"`
   - After `fallback_node`: edge → `"format_response"`
3. Also update the original `validate_context` conditional: route to `"fallback"` (not `END`) when `fallback_triggered=True`.

- [ ] `_fallback_node` added and wired in graph
- [ ] Conditional edges updated for both `validate_context` and `safety_gate`

### 2. Add tests  <!-- agent: general-purpose -->

Add to `backend/tests/kg/test_generation_graph.py`:
- `test_fallback_node_uses_safe_exercises_when_triggered`: context with 3 safe exercises, `fallback_triggered=True`; assert recommendation has ≤3 exercises from safe list.
- `test_fallback_node_uses_empty_list_when_no_safe_exercises`: context with empty safe_exercises; assert `recommendation.exercises == []`.
- `test_fallback_triggered_by_empty_context`: invoke graph with `context=None` or `context={}` (no safe exercises); assert `fallback_triggered=True` in result.

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py -v
```

- [ ] Tests pass

### 3. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 5 fallback placeholder with `[TASK-063: Fallback handler...](../tasks/063-fallback-handler.md)`.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `_fallback_node` added to `generation_graph.py`, wired correctly
- [ ] Fallback produces a `WorkoutRecommendation` with exercises from `context.safe_exercises[:3]`
- [ ] `overall_reasoning` explains the fallback
- [ ] Both `validate_context` and `safety_gate` can trigger the fallback path
- [ ] ≥3 fallback tests passing

---
**UAT**: `.docs/uat/063-fallback-handler.uat.md`
