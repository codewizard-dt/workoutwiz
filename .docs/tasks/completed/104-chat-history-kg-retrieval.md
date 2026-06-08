# 104 — Expose Coach–Member Chat History KG Nodes to Coach AI Retrieval

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [071-feedback-submission-ui](071-feedback-submission-ui.md), [084-test-source-type-population](084-test-source-type-population.md), [102-visual-architecture-diagrams](102-visual-architecture-diagrams.md), [103-biomarker-kg-retrieval](103-biomarker-kg-retrieval.md)

## Objective

`ChatMessage` nodes are already seeded in Neo4j via `seed_rich_member_context_all()` with `speaker`, `content`, `timestamp`, and `intent` properties, but are not surfaced to the Coach AI — `ContextSlice` in `context_assembler.py` has no chat history field. This task wires the existing nodes into the retrieval graph so the Coach AI Copilot can reference prior conversations when coaching a member.

## Approach

1. Add `get_recent_chat_history()` to `traversal.py` — Cypher query returning the 10 most recent `ChatMessage` nodes for a member, ordered by timestamp descending.
2. Extend `ContextSlice` in `context_assembler.py` to include a `chat_history` field.
3. Add a `run_chat_history_traversal()` node in `retrieval_graph.py` and wire it before `assemble`, parallel with other traversal nodes.
4. Extend `assemble_context_from_parts()` to format chat history as a compact transcript block within the 2048-token budget (lowest priority — truncate to 5 messages if budget is tight).
5. Verify seed coverage: all personas in `PERSONAS` should have `ChatMessage` nodes, not just Jordan Rivera.

## Steps

### 1. Add get_recent_chat_history traversal function  <!-- agent: general-purpose -->

File: `backend/app/knowledge_graph/traversal.py`

Add after `get_lab_results()` (or after existing traversal functions if TASK-103 is not yet merged):

```python
async def get_recent_chat_history(driver, member_id: str, limit: int = 10) -> list[dict]:
    """Return up to `limit` most recent ChatMessage nodes for a member."""
    query = """
    MATCH (m:Member {id: $member_id})-[:SENT|RECEIVED]->(msg:ChatMessage)
    RETURN msg ORDER BY msg.timestamp DESC LIMIT $limit
    """
    async with driver.session() as session:
        result = await session.run(query, member_id=member_id, limit=limit)
        records = await result.fetch(limit)
        return [dict(r["msg"]) for r in records]
```

Check the actual edge type used by the seed (`SENT`, `HAS_MESSAGE`, or similar) by searching `seed.py` for `ChatMessage` before writing the query. Use the correct relationship name.

- [ ] Edge type verified against `seed.py` — use the relationship name actually seeded
- [ ] `get_recent_chat_history(driver, member_id, limit=10)` added to `traversal.py`
- [ ] Returns list of dicts ordered by `timestamp` descending (newest first)
- [ ] Uses `async with driver.session()` consistent with existing traversal patterns

### 2. Extend ContextSlice and assemble_context_from_parts  <!-- agent: general-purpose -->

File: `backend/app/kg/context_assembler.py`

2a. Add `chat_history` to the `ContextSlice` TypedDict:

```python
class ContextSlice(TypedDict):
    # ... existing fields ...
    chat_history: list[dict]   # up to 10 recent ChatMessage nodes, newest first
```

2b. In `assemble_context_from_parts()`, format chat history as a compact transcript and append it after exercise data (and after biomarkers if TASK-103 is present). Cap at 5 messages if token budget is under 300 tokens remaining. Omit the section entirely if budget is exhausted.

Example format:
```
--- Recent Conversations ---
[2024-11-10 coach]: Great work on the squat progression. Let's add more hip hinge volume next week.
[2024-11-08 member]: My lower back felt tight after deadlifts. Should I reduce weight?
[2024-11-08 coach]: Yes, drop 10% and focus on bracing cues. Log how it feels.
```

- [ ] `ContextSlice` has `chat_history: list[dict]` field
- [ ] `assemble_context_from_parts()` formats and appends transcript block
- [ ] Truncated to 5 messages when budget < 300 tokens, omitted when budget exhausted
- [ ] When `chat_history` is empty, no `--- Recent Conversations ---` section is emitted
- [ ] Messages formatted as `[YYYY-MM-DD speaker]: content` per line

### 3. Add run_chat_history_traversal node to the retrieval graph  <!-- agent: general-purpose -->

File: `backend/app/kg/retrieval_graph.py`

3a. Extend `RetrievalState` TypedDict:

```python
class RetrievalState(TypedDict):
    # ... existing fields ...
    chat_history: list[dict]
```

3b. In `_make_nodes()`, add a `run_chat_history_traversal` async function:

```python
async def run_chat_history_traversal(state: RetrievalState) -> dict:
    member_id = state["member_id"]
    history = await get_recent_chat_history(driver, member_id, limit=10)
    return {"chat_history": history}
```

3c. In `build_retrieval_graph()`:
- `graph.add_node("run_chat_history_traversal", run_chat_history_traversal)`
- Add edge: `lookup_member` → `run_chat_history_traversal`
- Add edge: `run_chat_history_traversal` → `assemble`

3d. Import `get_recent_chat_history` from `traversal`.

- [ ] `RetrievalState` has `chat_history: list[dict]` field
- [ ] `run_chat_history_traversal` node added and registered
- [ ] Node runs after `lookup_member`, before `assemble` (parallel with other traversals)
- [ ] Imports updated

### 4. Verify ChatMessage schema constraint  <!-- agent: general-purpose -->

File: `backend/app/knowledge_graph/init_schema.py`

Check whether a uniqueness constraint exists for `ChatMessage`. If missing, add:

```cypher
CREATE CONSTRAINT chat_message_id IF NOT EXISTS
  FOR (c:ChatMessage) REQUIRE c.id IS UNIQUE;
```

Also verify that each `ChatMessage` node in `seed.py` has an `id` property (add `str(uuid4())` if missing).

- [ ] `ChatMessage` uniqueness constraint present in `init_schema.py` (add if missing)
- [ ] All seeded `ChatMessage` nodes have an `id` property (add if missing)

### 5. Verify seed coverage for all personas  <!-- agent: general-purpose -->

File: `backend/app/knowledge_graph/seed.py`

Inspect `seed_rich_member_context_all()`. Confirm the function iterates over all entries in `PERSONAS` (15 personas), not just Jordan Rivera. If any `ChatMessage` seeding is guarded by a persona-specific check (e.g. `if persona["email"] == "jordan@..."`), remove the guard and seed 3–5 representative messages per persona with varied but realistic content.

- [ ] `seed_rich_member_context_all()` seeds `ChatMessage` nodes for all 15 personas
- [ ] Each persona gets at least 3 `ChatMessage` nodes (alternating coach/member speaker)
- [ ] No persona-specific guard gates `ChatMessage` seeding

## Acceptance Criteria

- [ ] `get_recent_chat_history()` exists in `traversal.py` with correct edge type from seed
- [ ] `ContextSlice` includes `chat_history: list[dict]` field
- [ ] `run_chat_history_traversal` node is wired into the retrieval graph
- [ ] Coach AI context string includes a `--- Recent Conversations ---` section when history is present
- [ ] `ChatMessage` uniqueness constraint exists in `init_schema.py`
- [ ] All 15 personas have seeded `ChatMessage` nodes

---
**UAT**: [`.docs/uat/104-chat-history-kg-retrieval.uat.md`](../uat/104-chat-history-kg-retrieval.uat.md)
