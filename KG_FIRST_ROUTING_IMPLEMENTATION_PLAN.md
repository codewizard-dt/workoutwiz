# KG-First Routing Implementation Plan

## Objective

Make the Knowledge Graph pipeline the default implementation behind `WORKOUT_GENERATE` while keeping `COACH` and `WORKOUT_LOG` separate. Preserve the legacy workout generator as a fallback. Fix the current implementation drift between router prompts, intent types, retrieval context, Neo4j schema/property names, embeddings, feedback payloads, API docs, frontend labels, and architecture documentation.

## Current Findings To Fix

1. `Intent.KNOWLEDGE_GRAPH` exists and the hub can route to it, but the router prompt only describes four intents.
2. `WORKOUT_GENERATE` currently routes to the legacy `workout_generator_graph`; KG generation is a separate `KNOWLEDGE_GRAPH` route.
3. The frontend `Use This Workout` flow depends on `ChatResponse.workout_draft`, which is currently extracted only from the legacy `build_workout_tool` result.
4. `retrieval_graph` runs traversal and vector search nodes, then calls `assemble_context()`, which repeats most of that work.
5. `generation_graph` expects `context["contraindicated_ids"]`, but `ContextSlice` does not formally include it.
6. Neo4j `Member` properties drift across files:
   - Schema and ingestion use `equipment_available` and `sessions_per_week`.
   - Traversal currently returns `equipment` and `availability`.
7. Embedding property names drift:
   - Neo4j schema creates a vector index on `description_embedding`.
   - `backend/app/kg/embeddings.py` writes to `embedding`.
8. Feedback context type drifts:
   - Postgres model and KG schema use `exercise`, `set`, `workout`.
   - `FeedbackPayload` defaults to `post_workout`.
9. Chat/OpenAPI descriptions and frontend route labels do not consistently include `KNOWLEDGE_GRAPH`.
10. Root `architecture.md` does not yet exist and needs to document the new KG-first shape after code changes.

## Phase 1: Router And Intent Contract

### 1.1 Update the router system prompt

Target files:
- `backend/app/agents/hub.py`

Steps:
1. Edit `_ROUTER_SYSTEM_PROMPT` to list all five intents:
   - `COACH`
   - `WORKOUT_GENERATE`
   - `WORKOUT_LOG`
   - `KNOWLEDGE_GRAPH`
   - `FALLBACK`
2. Define `WORKOUT_GENERATE` as normal workout creation, planning, and routine design, even when KG powers the implementation.
3. Define `KNOWLEDGE_GRAPH` narrowly as explicit graph, explainability, injury-history, preference-history, or recommendation-reasoning questions.
4. Add examples that reduce ambiguity:
   - `WORKOUT_GENERATE`: "Give me a 45-minute upper-body workout", "Plan a leg day around my knee injury".
   - `KNOWLEDGE_GRAPH`: "Why did you skip squats?", "What does my history suggest?", "Which exercises have I rated highly?", "Explain how my injury affects this plan".
5. Keep the confidence rule: use `< 0.6` only when genuinely ambiguous.

Verification:
- Read the prompt and confirm every `Intent` enum value is represented.
- Add tests in Phase 6 to pin the behavior.

### 1.2 Update route schema descriptions

Target files:
- `backend/app/agents/state.py`
- `backend/app/schemas/chat.py`
- `backend/app/routers/chat.py`

Steps:
1. Update `RouteDecision.intent` description to mention `KNOWLEDGE_GRAPH`.
2. Update `ChatResponse.route` description to list all five route values.
3. Update `/chat` route description to include `KNOWLEDGE_GRAPH`.
4. Keep the wire shape unchanged.

Verification:
- Import `ChatResponse` and `RouteDecision` without errors.
- Add tests or assertions in existing router tests if appropriate.

## Phase 2: KG-First Hub Routing

### 2.1 Preserve the legacy generator under an explicit name

Target files:
- `backend/app/agents/hub.py`
- `backend/app/agents/workout_generator.py`

Steps:
1. Keep the existing compiled `workout_generator_graph`.
2. Import it in `hub.py` as `legacy_workout_generator_graph` or alias it locally.
3. Do not remove the old graph; it remains the fallback path.
4. Keep `workout_generator.py` tool behavior unchanged unless tests require a small compatibility adjustment.

Verification:
- Existing legacy generator tests should still pass.

### 2.2 Add a KG-first workout generation node

Target files:
- `backend/app/agents/hub.py`

Steps:
1. Create an async node such as `_workout_generate_node`.
2. The node should:
   - Read the last human message as `query`.
   - Read `state["user_id"]` as `member_id`.
   - If `member_id` is missing, fall back immediately to legacy generation with reason `missing_member_id`.
   - Open an async Neo4j driver using existing settings.
   - Run `build_retrieval_graph(driver).ainvoke({"member_id": member_id, "query": query})`.
   - Run `build_generation_graph().ainvoke({"member_id": member_id, "query": query, "context": context})`.
   - Validate that the returned recommendation has at least two exercises.
   - Format a user-facing response.
   - Attach a structured workout draft in a predictable state key, for example `workout_draft`.
3. On KG failure, missing context, missing recommendation, or fewer than two exercises, call the legacy generator path.
4. Record an audit entry for KG success:
   - `event: "workout_generate_kg"`
   - `member_id`
   - `exercise_count`
   - `fallback_used: false`
5. Record an audit entry before or after legacy fallback:
   - `event: "workout_generate_legacy_fallback"`
   - `reason`
   - `member_id`
   - `fallback_used: true`
6. Ensure driver close happens in all paths.

Verification:
- Add hub integration tests in Phase 6.
- Manual mocked invocation should return an AI message and a `workout_draft`.

### 2.3 Adapt KG recommendations into the existing WorkoutDraft shape

Target files:
- `backend/app/agents/hub.py` or a new helper module such as `backend/app/kg/workout_draft.py`
- `backend/app/schemas/chat.py`

Steps:
1. Create a helper such as `_recommendation_to_workout_draft(query, recommendation)`.
2. Return:
   - `goal`: the user query or recommendation goal if one exists later.
   - `phases.warmup`: empty list for now.
   - `phases.main`: all recommended exercises.
   - `phases.cooldown`: empty list for now.
   - `total_exercises`: count of recommendation exercises.
   - `invalid_ids_skipped`: `recommendation.skipped_exercise_ids`.
3. Map each `RecommendedExercise` to the existing frontend draft exercise shape:
   - `id`: `exercise_id`
   - `name`
   - `sets`
   - `reps`: string or number accepted by the existing frontend conversion path. Prefer a string for compatibility with the legacy draft.
   - `duration_s`: from `duration_seconds`
   - `rest_s`: default to `90` unless future KG output includes rest.
4. Keep the response contract compatible with `frontend/src/types/index.ts`.

Verification:
- Add a unit test for the adapter.
- Add a `/chat` contract test that confirms `workout_draft.phases.main` is populated on KG success.

### 2.4 Wire the hub graph

Target files:
- `backend/app/agents/hub.py`

Steps:
1. Register `workout_gen` as the new KG-first node, not the legacy compiled graph.
2. Keep `knowledge_graph` as a separate node for explicit KG explainability/history questions.
3. Preserve the existing conditional edge names:
   - `coach`
   - `workout_gen`
   - `workout_log`
   - `knowledge_graph`
   - `clarification`
4. Ensure `_route_selector` still sends `WORKOUT_GENERATE` to `workout_gen`.
5. Ensure `KNOWLEDGE_GRAPH` still routes to `knowledge_graph`.

Verification:
- Hub graph compiles.
- Existing routing tests are updated to patch the right nodes.

## Phase 3: Knowledge Graph Explainability Route

### 3.1 Narrow `KNOWLEDGE_GRAPH` behavior

Target files:
- `backend/app/agents/hub.py`
- Potentially `backend/app/kg/tools.py`

Steps:
1. Rename or document `_knowledge_graph_node` as an explicit KG reasoning/explainability path.
2. For now, keep the current retrieval plus generation behavior only if the message asks for graph-backed reasoning and does not supply a specific skipped exercise ID.
3. If the message clearly asks "why was exercise X skipped?" and an exercise ID is available in context later, call `explain_skipped_exercise`.
4. If there is no extractable exercise ID, return a concise answer that KG can explain skipped exercises when given an exercise ID or a prior skipped recommendation.
5. Record an audit entry:
   - `event: "knowledge_graph_explain"` when explainability is used.
   - `event: "knowledge_graph_reasoning"` when retrieval/generation reasoning is used.

Verification:
- Add tests that `KNOWLEDGE_GRAPH` does not run the legacy generator.
- Keep `/kg/explain` behavior unchanged.

## Phase 4: Retrieval And Context Consistency

### 4.1 Add contraindication IDs to ContextSlice

Target files:
- `backend/app/kg/context_assembler.py`
- `backend/app/kg/retrieval_graph.py`
- Tests under `backend/tests/kg/`

Steps:
1. Add `contraindicated_ids: list[str]` or `set[str]` to `ContextSlice`.
2. Prefer `list[str]` for JSON friendliness.
3. Ensure `assemble_context()` fetches `get_contraindicated_exercise_ids()`.
4. Ensure returned context includes `contraindicated_ids`.
5. Update generation tests if they construct `ContextSlice` manually.

Verification:
- Safety gate tests pass and no longer rely on an undeclared key.

### 4.2 Refactor context assembly to avoid duplicate retrieval

Target files:
- `backend/app/kg/context_assembler.py`
- `backend/app/kg/retrieval_graph.py`

Steps:
1. Add a function such as `assemble_context_from_parts(...)`.
2. Inputs should include:
   - `member_profile`
   - `safe_exercises`
   - `contraindicated_ids`
   - `preferred_exercises`
   - `performed_exercises`
   - `vector_docs`
3. Move deduplication, safe filtering, vector filtering, profile trimming, and token budget enforcement into `assemble_context_from_parts(...)`.
4. Update `assemble_context()` to become a convenience wrapper:
   - Fetch all needed traversal and vector data.
   - Pass results to `assemble_context_from_parts(...)`.
5. Update `retrieval_graph.assemble` node to call `assemble_context_from_parts(...)` using state already produced by prior nodes.
6. Remove direct `assemble_context()` usage from `retrieval_graph`.

Verification:
- Add a test that patches traversal functions and confirms they are called once per retrieval graph invocation.
- Update existing `test_retrieval_graph_invokes_assemble_context` to expect `assemble_context_from_parts`.

### 4.3 Normalize missing-member behavior

Target files:
- `backend/app/kg/context_assembler.py`
- `backend/app/kg/retrieval_graph.py`
- `backend/app/agents/hub.py`

Steps:
1. Choose a single missing-member behavior: return an empty context plus an error marker, not inconsistent exceptions.
2. Recommended behavior:
   - `assemble_context()` returns empty `ContextSlice` with `member_profile: {}`, empty lists, zero token counts, and `error: "member_not_found"` if an error field is added.
   - `retrieval_graph` passes that through.
   - Hub KG-first generation sees no safe exercises or missing profile and falls back to legacy with reason `member_not_found`.
3. Update tests that currently expect `ValueError`.

Verification:
- Missing member test confirms fallback, not an unhandled exception.

## Phase 5: Neo4j Schema And Property Alignment

### 5.1 Align Member profile fields

Target files:
- `backend/app/knowledge_graph/traversal.py`
- `backend/app/knowledge_graph/ingest_members.py`
- `.docs/knowledge-graph-schema.md`
- Tests under `backend/tests/knowledge_graph/` and `backend/tests/kg/`

Steps:
1. Update `_MEMBER_PROFILE_QUERY` to return:
   - `m.equipment_available AS equipment_available`
   - `m.sessions_per_week AS sessions_per_week`
2. Stop returning `m.equipment AS equipment` and `m.availability AS availability`.
3. Update docstrings and test fixtures to use the canonical field names.
4. Leave `ingest_members.py` as-is if it already writes canonical fields.

Verification:
- Traversal tests check canonical fields.
- No test fixture uses stale `equipment` or `availability` unless explicitly testing backwards compatibility.

### 5.2 Align embedding property names

Target files:
- `backend/app/kg/embeddings.py`
- `backend/app/knowledge_graph/init_schema.py`
- `.docs/knowledge-graph-schema.md`
- `backend/tests/kg/test_embeddings.py`

Steps:
1. Change `EMBEDDING_NODE_PROPERTY` from `embedding` to `description_embedding`.
2. Ensure `Neo4jVector.from_existing_graph(...)` writes `description_embedding`.
3. Ensure `Neo4jVector.from_existing_index(...)` reads from the existing `exercise_embeddings` index.
4. Keep `TEXT_NODE_PROPERTIES = ["name", "description"]`.
5. Update embedding tests to expect `description_embedding`.

Verification:
- Embedding unit tests pass.
- Schema and code now point at the same property.

### 5.3 Fix feedback context type validation

Target files:
- `backend/app/schemas/kg.py`
- `backend/app/kg/feedback_service.py`
- `frontend/src/components/FeedbackForm.tsx` if it sends context type
- `backend/tests/kg/test_feedback_service.py`
- `backend/tests/test_kg_router.py`

Steps:
1. Define a strict enum or `Literal["exercise", "set", "workout"]` for `FeedbackPayload.context_type`.
2. Default to `"exercise"`.
3. Update field description to match the KG schema.
4. Ensure `/kg/feedback` returns HTTP 422 for invalid context types.
5. Update frontend feedback submission to send `"exercise"` by default.
6. Do not change `/kg/feedback` response shape.

Verification:
- Feedback tests accept valid values and reject invalid values.
- Router test covers invalid context type with 422.

## Phase 6: Data Ownership And Sync Boundary

### 6.1 Add a sync service boundary

Target files:
- New file such as `backend/app/kg/sync_service.py`
- Potential imports in `feedback_service.py`
- `architecture.md`

Steps:
1. Create a small module that documents and centralizes graph write boundaries.
2. Add explicit functions or placeholders for:
   - `sync_member_profile_to_kg(...)`
   - `sync_workout_to_kg(...)`
   - `sync_feedback_to_kg(...)`
3. Keep implementation minimal if no new migrations are required.
4. Move or wrap direct feedback graph write logic through this service where practical.
5. Add docstrings that PostgreSQL remains source of truth and Neo4j is a derived coaching read model.

Verification:
- Imports work.
- No route response shape changes.

### 6.2 Avoid adding database migrations unless forced

Steps:
1. Review whether any schema change requires Alembic.
2. The expected changes are validation, Neo4j property alignment, and routing logic, so no Postgres migration should be needed.
3. If a migration becomes necessary, stop and evaluate separately before adding it.

Verification:
- `git status` should not show migration files unless deliberately added.

## Phase 7: Frontend And API Contract Updates

### 7.1 Preserve the chat workout draft contract

Target files:
- `backend/app/routers/chat.py`
- `backend/app/schemas/chat.py`
- `frontend/src/types/index.ts`

Steps:
1. Update chat route logic so it first reads `result.get("workout_draft")`.
2. Keep the existing fallback extraction from legacy `ToolMessage(name="build_workout_tool")`.
3. Return `workout_draft` for KG-generated `WORKOUT_GENERATE` responses.
4. Update `ChatResponse.workout_draft` description to say it may come from KG or legacy generation.

Verification:
- API contract test confirms a mocked KG result returns `workout_draft`.

### 7.2 Update frontend route labels

Target files:
- `frontend/src/components/RouteBadge.tsx`
- Any route display components found by `rg "WORKOUT_GENERATE|WORKOUT_LOG|COACH|FALLBACK"`

Steps:
1. Add `KNOWLEDGE_GRAPH` label and tone.
2. Keep `WORKOUT_GENERATE` label as "Generate" because route remains the same for workout planning.
3. Avoid changing user-facing flows unless required for compatibility.

Verification:
- TypeScript compile should not fail on route label maps.

### 7.3 Update KG feedback UI default

Target files:
- `frontend/src/components/FeedbackForm.tsx`
- `frontend/src/hooks` if relevant

Steps:
1. Locate current feedback submission body.
2. Ensure `context_type` is omitted or sent as `"exercise"`.
3. Remove or avoid `"post_workout"`.

Verification:
- Existing KG page still submits feedback.
- Backend payload validation accepts the frontend default.

## Phase 8: Tests

### 8.1 Router unit tests

Target files:
- `backend/tests/test_agents_router.py`

Steps:
1. Add a test that router schema/prompt includes `KNOWLEDGE_GRAPH`.
2. Add mocked classification test for explicit KG phrasing returning `Intent.KNOWLEDGE_GRAPH`.
3. Keep existing mocked tests for `COACH`, `WORKOUT_GENERATE`, `WORKOUT_LOG`, and `FALLBACK`.
4. Add or update assertions that audit route values include new intent values when mocked.

Verification:
- `pytest backend/tests/test_agents_router.py` passes from backend context.

### 8.2 Hub integration tests

Target files:
- `backend/tests/test_routing_integration.py`
- `backend/tests/test_agents_routing.py`
- New focused test file if cleaner, such as `backend/tests/test_kg_first_hub.py`

Steps:
1. Test `WORKOUT_GENERATE` uses KG-first node on success.
2. Mock retrieval and generation graphs to return two recommended exercises.
3. Assert final message contains KG recommendation content.
4. Assert result includes `workout_draft`.
5. Assert audit includes `workout_generate_kg`.
6. Test KG missing-member or failure path uses legacy generator.
7. Assert audit includes `workout_generate_legacy_fallback` and fallback reason.
8. Test `KNOWLEDGE_GRAPH` route does not invoke legacy generator.

Verification:
- Hub tests pass without real LLM or Neo4j connections.

### 8.3 KG context tests

Target files:
- `backend/tests/kg/test_context_assembler.py`
- `backend/tests/kg/test_retrieval_graph.py`
- `backend/tests/test_kg_critical_graph_retrieval.py`
- `backend/tests/test_kg_critical_injury_filtering.py`

Steps:
1. Update context fixtures to include `contraindicated_ids`.
2. Add tests for `assemble_context_from_parts(...)`.
3. Update direct `assemble_context()` tests to confirm convenience-wrapper behavior.
4. Update retrieval graph tests to ensure intermediate node outputs feed the assembler without duplicate traversal.
5. Update missing-member tests to expect empty context and fallback semantics if Phase 4.3 is implemented.

Verification:
- KG context/retrieval tests pass.

### 8.4 Traversal and embedding tests

Target files:
- `backend/tests/knowledge_graph/test_traversal.py`
- `backend/tests/kg/test_embeddings.py`

Steps:
1. Update traversal expected member profile keys to `equipment_available` and `sessions_per_week`.
2. Update embeddings expected `embedding_node_property` to `description_embedding`.
3. Add a regression assertion that schema index property and embedding property constant match, if practical.

Verification:
- Traversal and embedding tests pass.

### 8.5 Feedback tests

Target files:
- `backend/tests/kg/test_feedback_service.py`
- `backend/tests/test_kg_router.py`

Steps:
1. Update default context type from `post_workout` to `exercise`.
2. Add valid cases for `exercise`, `set`, and `workout`.
3. Add invalid case asserting `FeedbackPayload(context_type="post_workout")` fails or `/kg/feedback` returns 422.
4. Ensure `/kg/feedback` response shape is unchanged.

Verification:
- Feedback unit and router tests pass.

### 8.6 Frontend compile or focused check

Target files:
- Frontend files touched in Phase 7

Steps:
1. Run the existing frontend typecheck/build command if available.
2. If no fast command exists, run a focused grep/import sanity check and report that full frontend validation was not run.

Verification:
- TypeScript route label and feedback changes do not introduce obvious type errors.

## Phase 9: Architecture Documentation

### 9.1 Create or update root `architecture.md`

Target files:
- `architecture.md`
- Reference file: `backend/app/agents-kg.flowchart.md`
- Reference file: `.docs/knowledge-graph-schema.md`

Steps:
1. Add a current-state-plus-new-state assessment of `backend/app/agents/` and `backend/app/kg/`.
2. Explain the new flow:
   - `/chat` routes with the hub.
   - `WORKOUT_GENERATE` enters KG-first generation.
   - Legacy generator is fallback only.
   - `/kg/*` still exists as direct KG API endpoints.
3. Explain why `COACH` remains separate:
   - It answers education and advice.
   - It should not create full plans.
   - It does not need graph traversal unless the user asks explicit personal-history reasoning.
4. Explain why Postgres and Neo4j both exist:
   - Postgres is transactional source of truth.
   - Neo4j is the coaching read model for graph traversal, contraindications, history, preference, and vector search.
5. Document shared identifiers:
   - `Member.id == users.id`
   - `Exercise.id == exercises.id`
   - `WorkoutSession.id == workouts.id`
6. Add Mermaid diagrams:
   - KG-first request flow.
   - Hub conditional routing.
   - KG retrieval plus generation pipeline.
   - ERD-style KG graph.
7. Mention fixed drift:
   - Router prompt includes all intents.
   - Context includes `contraindicated_ids`.
   - Member and embedding property names are canonical.
   - Feedback context types are canonical.

Verification:
- Markdown is readable.
- Mermaid blocks are syntactically plausible.

## Phase 10: Focused Validation Commands

Run commands from `backend/` unless noted.

Recommended backend commands:

```bash
uv run pytest tests/test_agents_router.py tests/test_routing_integration.py tests/test_agents_routing.py -q
uv run pytest tests/kg/test_context_assembler.py tests/kg/test_retrieval_graph.py tests/kg/test_generation_graph.py -q
uv run pytest tests/kg/test_embeddings.py tests/kg/test_feedback_service.py tests/test_kg_router.py -q
uv run pytest tests/knowledge_graph/test_traversal.py tests/test_kg_critical_graph_retrieval.py tests/test_kg_critical_injury_filtering.py -q
```

Recommended frontend commands:

```bash
npm run typecheck
```

If `npm run typecheck` is unavailable, use the repository's existing frontend validation command from `package.json`.

## Phase 11: Rollback And Safety

1. Keep all changes scoped to routing, KG pipeline helpers, schema validation, tests, frontend labels/defaults, and documentation.
2. Do not add Postgres migrations unless a test proves one is required.
3. Do not remove the legacy workout generator.
4. If KG-first routing causes broad test failures, revert only the hub node wiring and keep independent drift fixes that are clearly correct:
   - Router prompt includes all intents.
   - Embedding property alignment.
   - Feedback context validation.
   - Member profile property alignment.
5. Preserve `/kg/recommend`, `/kg/explain`, and `/kg/feedback` response shapes.

## Expected End State

1. `WORKOUT_GENERATE` is the normal route for workout planning.
2. KG powers `WORKOUT_GENERATE` by default when member context is available.
3. Legacy generation handles missing KG context and KG failures.
4. `KNOWLEDGE_GRAPH` is reserved for explicit KG reasoning, history, preference, or explainability questions.
5. `/chat` KG-generated workouts include `workout_draft`, so the frontend "Use This Workout" flow still works.
6. Retrieval graph work is not duplicated.
7. Context, schema, traversal, embedding, and feedback names are aligned.
8. `architecture.md` explains the final architecture and the justification for both Postgres and Neo4j.
