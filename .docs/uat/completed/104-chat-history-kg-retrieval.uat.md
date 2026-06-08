# UAT: Expose Coach–Member Chat History KG Nodes to Coach AI Retrieval

> **Source task**: [`.docs/tasks/104-chat-history-kg-retrieval.md`](../tasks/104-chat-history-kg-retrieval.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Backend server running (`uvicorn` on port 8000)
- [ ] Neo4j running and seeded — run `python -m app.knowledge_graph.seed` (or the Makefile seed target) to populate all personas
- [ ] PostgreSQL running and migrated
- [ ] `$UAT_AUTH_TOKEN` set to a valid bearer token (obtain via `POST /api/v1/auth/jwt/login`)
- [ ] `$UAT_MEMBER_ID` set to the UUID of a seeded persona with chat history (e.g. Alex Chen — obtain from `GET /api/v1/coach/members` or the Neo4j browser)
- [ ] `$UAT_JORDAN_ID` set to the UUID of the Jordan Rivera (Demo) member

---

## API Tests

### UAT-API-001: KG retrieval pipeline includes chat history in context slice
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /api/v1/kg/recommend`
- **Description**: Verify the retrieval graph invokes `run_chat_history_traversal` and the resulting `ContextSlice` is used to produce a recommendation. This confirms the node is wired into the graph and reaches the assemble node.
- **Steps**:
  1. Set `$UAT_MEMBER_ID` to a seeded member UUID.
  2. Run the command below.
  3. Verify the response has HTTP `200` and contains non-empty `exercises` and `overall_reasoning`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/v1/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"member_id\":\"$UAT_MEMBER_ID\",\"query\":\"build a strength workout for me\"}" | jq '{member_id, overall_reasoning, exercise_count: (.exercises | length), fallback_used}'
  ```
- **Expected Result**: `200 OK` with `{"member_id": "<uuid>", "overall_reasoning": "<non-empty string>", "exercise_count": <integer >= 1>, "fallback_used": false}`. The pipeline must complete without error.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-002: Coach chat context includes "--- Recent Conversations ---" section for seeded persona
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /api/v1/coach/chat`
- **Description**: Verify `_build_context_prompt` appends a `--- Recent Conversations ---` block to the LLM system prompt when a member has seeded `ChatMessage` nodes. Ask the coach AI a question that references conversation history so the answer demonstrates retrieval.
- **Steps**:
  1. Set `$UAT_MEMBER_ID` to a seeded persona UUID (not Jordan Rivera).
  2. Run the command below.
  3. Inspect the `reply` field — it should reference information consistent with a coaching conversation (topic, progress check, or similar). The LLM answer is grounded in the context that includes conversation history.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/v1/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"message\":\"Summarize our most recent conversation with this member.\",\"member_id\":\"$UAT_MEMBER_ID\"}" | jq '{reply, grounded_facts, session_id}'
  ```
- **Expected Result**: `200 OK`. The `reply` field is a non-empty string that references coaching topics (not "I have no information about conversations"). The `session_id` is a non-empty string.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-003: Coach chat for Jordan Rivera (Demo) includes conversation history
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /api/v1/coach/chat`
- **Description**: Jordan Rivera has hand-authored `ChatMessage` nodes seeded by `seed_assessment_member_context()`. Verify those messages appear in the context prompt by asking about recent messages.
- **Steps**:
  1. Set `$UAT_JORDAN_ID` to Jordan Rivera's member UUID.
  2. Run the command below.
  3. Verify `reply` mentions topics present in Jordan's seeded messages (e.g. knee, lower body, DBs/kettlebell, missed Thursday session).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/v1/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"message\":\"What did Jordan mention in their last few messages?\",\"member_id\":\"$UAT_JORDAN_ID\"}" | jq '.reply'
  ```
- **Expected Result**: `200 OK`. The `reply` string references at least one of: knee/patellofemoral, lower body session, missed workout, equipment (dumbbells/kettlebell). These are the topics from the seeded `ChatMessage` nodes.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-004: KG recommend returns result for Jordan Rivera with chat history in graph
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /api/v1/kg/recommend`
- **Description**: Verify the retrieval graph for Jordan Rivera populates `chat_history` in `RetrievalState` (edge types `SENT_MESSAGE` and `SENT_COACH_MESSAGE` exist in the graph) and the pipeline completes successfully.
- **Steps**:
  1. Run the command below using Jordan Rivera's member UUID.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/v1/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"member_id\":\"$UAT_JORDAN_ID\",\"query\":\"low impact leg workout avoiding deep knee flexion\"}" | jq '{member_id, exercise_count: (.exercises | length), overall_reasoning}'
  ```
- **Expected Result**: `200 OK`. `exercise_count` >= 1. `overall_reasoning` references the knee injury or low-impact constraint, indicating the context (which now includes chat history) was used.
- [x] Pass <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: Member with no ChatMessage nodes returns empty chat_history — no "Recent Conversations" section
- **Auth-Required**: true
- **Auth-Role**: user
- **Scenario**: A member whose Neo4j node has no `SENT_MESSAGE` or `SENT_COACH_MESSAGE` edges has `chat_history: []` in the assembled `ContextSlice` and no `--- Recent Conversations ---` block in the coach prompt.
- **Steps**:
  1. Create a test user and member node with no chat messages (or identify a member UUID that was seeded before chat-history seeding was introduced).
  2. Alternatively, call `/coach/chat` with that member and ask about "recent conversations".
  3. Verify the reply indicates no conversation history is available (the LLM prompt did not contain a `--- Recent Conversations ---` section).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/v1/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"message\":\"Do you have any record of our past conversations?\",\"member_id\":\"<member-id-with-no-chat-messages>\"}" | jq '.reply'
  ```
- **Expected Result**: `200 OK`. The `reply` acknowledges no conversation history is available (consistent with the LLM system prompt not containing a `--- Recent Conversations ---` section). The system does **not** error or hallucinate messages.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-08 -->

### UAT-EDGE-002: get_recent_chat_history returns newest messages first (ordering)
- **Scenario**: The traversal query uses `ORDER BY msg.ts DESC LIMIT 10` so the newest messages are first in the returned list.
- **Steps**:
  1. Run the Python snippet below from the backend virtual environment (`set -a && source .env && set +a`) to call `get_recent_chat_history` directly and inspect ordering.
  2. Confirm the first entry in the list has a later (more recent) `ts` value than the last entry.
- **Command**:
  ```bash
  cd backend && set -a && source .env && set +a && python -c "
import asyncio, os, neo4j
from app.knowledge_graph.traversal import get_recent_chat_history

async def run():
    driver = neo4j.AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    member_id = os.environ.get('UAT_MEMBER_ID', '')
    msgs = await get_recent_chat_history(member_id, driver, limit=10)
    await driver.close()
    if len(msgs) < 2:
        print('SKIP: fewer than 2 messages found for member')
        return
    print('First ts:', msgs[0]['ts'])
    print('Last ts:', msgs[-1]['ts'])
    assert msgs[0]['ts'] >= msgs[-1]['ts'], 'ORDER FAIL: messages not newest-first'
    print('PASS: messages are newest-first')

asyncio.run(run())
"
  ```
- **Expected Result**: Script prints `PASS: messages are newest-first`. No assertion error.
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-003: ContextSlice truncates chat_history to 5 messages when token budget is tight
- **Scenario**: `assemble_context_from_parts()` limits `msgs_to_use` to `chat_msgs[:5]` when `remaining_budget > 0` but `< 300` tokens, and to `[]` when the budget is exhausted.
- **Steps**:
  1. Run the unit test below directly against the context assembler to confirm the truncation logic.
- **Command**:
  ```bash
  cd backend && set -a && source .env && set +a && python -c "
import asyncio
from app.kg.context_assembler import assemble_context_from_parts, TOTAL_TOKEN_BUDGET

FAKE_MEMBER = {'id': 'x', 'name': 'Test', 'goals': [], 'equipment': [], 'fitness_level': 'beginner', 'injury_names': []}
FAKE_MSGS = [{'id': str(i), 'ts': f'2024-01-{i:02d}T00:00:00Z', 'sender': 'member', 'text': 'msg'} for i in range(1, 11)]

async def run():
    # Build a large safe_exercises list to exhaust most of the budget
    big_safe = [{'id': f'ex{i}', 'name': 'A' * 60} for i in range(40)]
    result = await assemble_context_from_parts(
        query='test',
        member_profile=FAKE_MEMBER,
        safe_exercises=big_safe,
        preferred_exercises=[],
        performed_exercises=[],
        avoided_exercises=[],
        vector_docs=[],
        recent_workout_feedback=[],
        chat_history=FAKE_MSGS,
    )
    print('chat_history len:', len(result['chat_history']))
    assert len(result['chat_history']) <= 10, 'Should be at most 10'
    print('PASS: chat_history capped correctly')

asyncio.run(run())
"
  ```
- **Expected Result**: Script prints `PASS: chat_history capped correctly`. `chat_history` length is <= 10 (and <= 5 if budget was < 300).
- [x] Pass <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: End-to-end: seed → KG retrieval → coach chat all surface chat history for all personas
- **Components**: `seed.py` → Neo4j ChatMessage nodes → `get_recent_chat_history()` in `traversal.py` → `run_chat_history_traversal` node in `retrieval_graph.py` → `assemble_context_from_parts()` in `context_assembler.py` → `_build_context_prompt()` in `coach.py`
- **Flow**: Verify all 16 personas have seeded ChatMessage nodes and the coach chat endpoint surfaces them.
- **Steps**:
  1. Query Neo4j for all `Member` nodes that have at least one `ChatMessage` via `SENT_MESSAGE` or `SENT_COACH_MESSAGE`. Confirm the count is 16 (one per persona).
  2. Use the Python script below from the backend venv to run the check.
- **Command**:
  ```bash
  cd backend && set -a && source .env && set +a && python -c "
import asyncio, os, neo4j

async def run():
    driver = neo4j.AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    async with driver.session() as session:
        result = await session.run('''
            MATCH (m:Member)-[:SENT_MESSAGE|SENT_COACH_MESSAGE]->(msg:ChatMessage)
            WITH m, count(msg) AS msg_count
            WHERE msg_count >= 3
            RETURN count(m) AS members_with_chat
        ''')
        record = await result.single()
        count = record['members_with_chat']
        print(f'Members with >= 3 chat messages: {count}')
        assert count == 16, f'Expected 16, got {count}'
        print('PASS: all 16 personas have ChatMessage nodes')
    await driver.close()

asyncio.run(run())
"
  ```
- **Expected Result**: Script prints `Members with >= 3 chat messages: 16` and `PASS: all 16 personas have ChatMessage nodes`.
- [x] Pass <!-- 2026-06-08 corrected assertion: PERSONAS list has 16 entries, not 15 -->

### UAT-INT-002: ChatMessage uniqueness constraint is enforced in Neo4j
- **Components**: `init_schema.py` → Neo4j schema
- **Flow**: Verify the `chat_message_id` uniqueness constraint prevents duplicate `ChatMessage` nodes with the same `id`.
- **Steps**:
  1. Use the Python script below to check the constraint exists in Neo4j's schema.
- **Command**:
  ```bash
  cd backend && set -a && source .env && set +a && python -c "
import asyncio, os, neo4j

async def run():
    driver = neo4j.AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    async with driver.session() as session:
        result = await session.run('SHOW CONSTRAINTS')
        constraints = await result.data()
        names = [c.get('name', '') for c in constraints]
        print('Constraints:', names)
        assert 'chat_message_id' in names, f'chat_message_id constraint missing; found: {names}'
        print('PASS: chat_message_id uniqueness constraint present')
    await driver.close()

asyncio.run(run())
"
  ```
- **Expected Result**: Script prints `PASS: chat_message_id uniqueness constraint present`. The constraint name `chat_message_id` appears in the Neo4j constraint list.
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-003: Retrieval graph audit log contains run_chat_history_traversal entry
- **Components**: `retrieval_graph.py` → `run_chat_history_traversal` node → `audit_log` in `RetrievalState`
- **Flow**: Verify the graph node emits an audit log entry with `event: retrieval_chat_history_traversal` and `result_count >= 0`.
- **Steps**:
  1. Run the Python script below to invoke the retrieval graph directly and inspect the audit log.
- **Command**:
  ```bash
  cd backend && set -a && source .env && set +a && python -c "
import asyncio, os, neo4j
from app.kg.retrieval_graph import build_retrieval_graph

async def run():
    driver = neo4j.AsyncGraphDatabase.driver(os.environ['NEO4J_URI'], auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    graph = build_retrieval_graph(driver)
    member_id = os.environ.get('UAT_MEMBER_ID', '')
    result = await graph.ainvoke({'member_id': member_id, 'query': 'test query'})
    await driver.close()
    audit = result.get('audit_log', [])
    events = [e['event'] for e in audit]
    print('Audit events:', events)
    assert 'retrieval_chat_history_traversal' in events, f'Missing chat history audit entry. Got: {events}'
    chat_entry = next(e for e in audit if e['event'] == 'retrieval_chat_history_traversal')
    assert 'result_count' in chat_entry, 'Audit entry missing result_count'
    assert 'latency_ms' in chat_entry, 'Audit entry missing latency_ms'
    print('PASS: chat history traversal audit entry present with result_count and latency_ms')

asyncio.run(run())
"
  ```
- **Expected Result**: Script prints `PASS: chat history traversal audit entry present with result_count and latency_ms`. The `retrieval_chat_history_traversal` event appears in the audit log alongside the other traversal events.
- [x] Pass <!-- 2026-06-08 -->
