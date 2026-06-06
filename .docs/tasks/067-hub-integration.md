# 067 — Hub Integration: Full KG Recommendation Flow in Hub Node

> **Depends on**: [066-tool-call-seam](completed/066-tool-call-seam.md)
> **Blocks**: none
> **Parallel-safe with**: [068-critical-path-test-injury-filtering](068-critical-path-test-injury-filtering.md), [069-critical-path-test-graph-retrieval](069-critical-path-test-graph-retrieval.md)

## Objective

Update `_knowledge_graph_node` in `backend/app/agents/hub.py` so that it runs the full retrieval → generation pipeline (not just retrieval) and returns a useful assistant message containing the workout recommendation.

## Approach

The current implementation returns `"Knowledge graph context assembled for member '...'."` — a placeholder. Replace this with a call to `kg_recommend_tool` from TASK-066 (or call the pipeline directly) so the user gets back an actual workout recommendation.

The updated node should:
1. Call the retrieval sub-graph (or `kg_recommend_tool` directly)
2. Format the `WorkoutRecommendation` into a readable message for the user
3. Include the reasoning and any skipped exercise explanations
4. Preserve the existing `audit_log` pattern

**Updated response format:**
```
Here is your personalized workout recommendation:

1. Squats — 3 sets × 10 reps
   Why: Compound movement matching your strength goals.
...

[Reasoning: ...]
[Note: X exercises were excluded due to injury constraints.]
```

No changes to COACH, WORKOUT_GENERATE, or WORKOUT_LOG paths.

## Steps

### 1. Inspect current `_knowledge_graph_node`  <!-- agent: general-purpose -->

Use Serena `find_symbol` with `_knowledge_graph_node` and `include_body=True` to see the exact current implementation.

- [ ] Current implementation confirmed

### 2. Update `_knowledge_graph_node` in `backend/app/agents/hub.py`  <!-- agent: general-purpose -->

Use Serena `replace_symbol_body` or `replace_content` to replace the body:

```python
async def _knowledge_graph_node(state: AgentState) -> dict[str, Any]:
    """Run retrieval → generation pipeline and return formatted recommendation."""
    import neo4j
    from app.kg.retrieval_graph import build_retrieval_graph
    from app.kg.generation_graph import build_generation_graph

    last_human = next(
        (m for m in reversed(state["messages"]) if hasattr(m, "type") and m.type == "human"),
        None,
    )
    query = last_human.content if last_human else ""
    member_id = state.get("user_id") or "unknown-member"

    try:
        async with neo4j.AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        ) as driver:
            retrieval_result = await build_retrieval_graph(driver).ainvoke(
                {"member_id": member_id, "query": query}
            )
            context = retrieval_result.get("context")
            gen_result = await build_generation_graph().ainvoke(
                {"member_id": member_id, "query": query, "context": context}
            )

        rec = gen_result.get("recommendation")
        if rec and rec.exercises:
            lines = ["Here is your personalized workout recommendation:\n"]
            for i, ex in enumerate(rec.exercises, 1):
                rep_str = f"{ex.reps} reps" if ex.reps else f"{ex.duration_seconds}s"
                lines.append(f"{i}. {ex.name} — {ex.sets} sets × {rep_str}")
                lines.append(f"   Why: {ex.reasoning}")
            lines.append(f"\n{rec.overall_reasoning}")
            if rec.skipped_exercise_ids:
                lines.append(f"\nNote: {len(rec.skipped_exercise_ids)} exercise(s) excluded due to injury constraints.")
            content = "\n".join(lines)
        else:
            content = "I couldn't build a recommendation with the available context. Please provide more details."
    except Exception as exc:
        content = f"Knowledge graph recommendation failed: {exc}"
        context = None

    return {
        "messages": [AIMessage(content=content)],
        "audit_log": state.get("audit_log", []) + [{"event": "knowledge_graph", "member_id": member_id}],
    }
```

- [ ] `_knowledge_graph_node` updated with full pipeline call and formatted response

### 3. Run hub import check and existing tests  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -c "from app.agents.hub import hub; print('hub OK')" && python -m pytest tests/test_agents_hub.py tests/test_agents_routing.py -v
```

Fix any import or test failures. COACH/WORKOUT_GENERATE/WORKOUT_LOG tests must still pass.

- [ ] Hub imports without error
- [ ] Existing hub tests still pass

### 4. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 6 hub integration placeholder with `[TASK-067: Hub integration...](../tasks/067-hub-integration.md)`.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `_knowledge_graph_node` updated to call generation after retrieval
- [ ] Returns formatted workout recommendation message (not just "context assembled")
- [ ] `skipped_exercise_ids` and `overall_reasoning` included in response
- [ ] COACH, WORKOUT_GENERATE, WORKOUT_LOG paths unmodified (existing tests pass)
- [ ] Hub imports without error

---
**UAT**: `.docs/uat/067-hub-integration.uat.md`
