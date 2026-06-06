# 060 — Generation Agent Sub-Graph: Context Slice → Structured Workout Recommendation

> **Depends on**: [059-retrieval-subgraph](completed/059-retrieval-subgraph.md)
> **Blocks**: [061-injury-safety-gate](061-injury-safety-gate.md), [062-explainability-tool](062-explainability-tool.md), [063-fallback-handler](063-fallback-handler.md)
> **Parallel-safe with**: [064-feedback-writeback](064-feedback-writeback.md)

## Objective

Create `backend/app/kg/generation_graph.py` — a LangGraph `StateGraph` that accepts a `ContextSlice` and the user's query, calls Claude to generate a structured workout recommendation, and returns a `WorkoutRecommendation` TypedDict with exercises, sets, reasoning, and a list of skipped exercise IDs.

## Approach

The generation graph has 3 nodes: `validate_context`, `generate_workout`, `format_response`.

- **validate_context**: checks that `context.safe_exercises` is non-empty; if empty, sets `fallback_triggered = True` and routes to END with an empty recommendation.
- **generate_workout**: calls Claude (`settings.generator_model`) with `with_structured_output(WorkoutRecommendation)`. The system prompt injects the full `ContextSlice` (member profile, safe exercises, preferred exercises) into XML-tagged sections. The LLM must only reference exercise `id` values present in `context.safe_exercises`.
- **format_response**: packages the LLM output into the final `GenerationState`.

The graph uses `StateGraph(GenerationState)` with a conditional edge after `validate_context`: if `fallback_triggered`, skip to END; otherwise proceed to `generate_workout`.

**`WorkoutRecommendation` schema (Pydantic model):**
```python
class RecommendedExercise(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: int | None = None
    duration_seconds: int | None = None
    weight_kg: float | None = None
    reasoning: str

class WorkoutRecommendation(BaseModel):
    exercises: list[RecommendedExercise]
    overall_reasoning: str
    member_id: str
    skipped_exercise_ids: list[str] = []
```

**System prompt template** (in `_GENERATION_SYSTEM_PROMPT`): explain that the assistant is a fitness coach building a personalized workout. Inject member profile, safe exercises, and preferred exercises. Instruct the LLM to only pick exercises from the provided safe list and document reasoning per exercise.

## Steps

### 1. Define `WorkoutRecommendation` Pydantic model in `backend/app/kg/generation_graph.py`  <!-- agent: general-purpose -->

Use Serena `write_memory` or `replace_content`; or the `Write` tool to create the file with:
- Imports: `from langchain_anthropic import ChatAnthropic`, `from langgraph.graph import StateGraph, END`, `from app.kg.context_assembler import ContextSlice`, `from app.config import settings`
- `RecommendedExercise` and `WorkoutRecommendation` Pydantic models
- `GenerationState` TypedDict with fields: `member_id`, `query`, `context`, `recommendation`, `fallback_triggered`, `error`
- `_GENERATION_SYSTEM_PROMPT` constant

- [ ] File created with models and TypedDict

### 2. Implement the 3 node functions  <!-- agent: general-purpose -->

Add to `backend/app/kg/generation_graph.py`:

```python
def _validate_context_node(state: GenerationState) -> dict:
    context = state.get("context")
    if not context or not context.get("safe_exercises"):
        return {"fallback_triggered": True}
    return {"fallback_triggered": False}

async def _generate_workout_node(state: GenerationState) -> dict:
    context = state["context"]
    llm = ChatAnthropic(
        model=settings.generator_model,
        api_key=settings.anthropic_api_key,
    ).with_structured_output(WorkoutRecommendation)
    
    prompt = _build_generation_prompt(state["query"], context)
    recommendation = await llm.ainvoke(prompt)
    recommendation.member_id = state["member_id"]
    return {"recommendation": recommendation}

def _format_response_node(state: GenerationState) -> dict:
    return {}  # state already has recommendation
```

Also implement `_build_generation_prompt(query, context) -> list[BaseMessage]` that constructs the human message with the context injected.

- [ ] `_validate_context_node` implemented, returns `fallback_triggered: True` when no safe exercises
- [ ] `_generate_workout_node` calls LLM with `with_structured_output(WorkoutRecommendation)`
- [ ] `_build_generation_prompt` formats context into a structured prompt

### 3. Build and compile the StateGraph  <!-- agent: general-purpose -->

```python
def build_generation_graph() -> CompiledGraph:
    builder = StateGraph(GenerationState)
    builder.add_node("validate_context", _validate_context_node)
    builder.add_node("generate_workout", _generate_workout_node)
    builder.add_node("format_response", _format_response_node)
    builder.set_entry_point("validate_context")
    builder.add_conditional_edges(
        "validate_context",
        lambda s: "generate_workout" if not s.get("fallback_triggered") else END,
    )
    builder.add_edge("generate_workout", "format_response")
    builder.add_edge("format_response", END)
    return builder.compile()
```

- [ ] `build_generation_graph()` builds and compiles the StateGraph
- [ ] Conditional edge skips to END when `fallback_triggered`

### 4. Write unit tests in `backend/tests/kg/test_generation_graph.py`  <!-- agent: general-purpose -->

Tests (all mocked — no live LLM):
- `test_build_generation_graph_returns_compiled_graph`: assert returned object has `.ainvoke`
- `test_validate_context_triggers_fallback_when_no_safe_exercises`: invoke with empty safe_exercises, assert `fallback_triggered=True`
- `test_generate_workout_returns_recommendation`: mock LLM to return a `WorkoutRecommendation`; assert result has `exercises` list
- `test_generate_workout_skips_generation_when_fallback_triggered`: assert `generate_workout` node never called when fallback triggered

- [ ] `backend/tests/kg/test_generation_graph.py` with ≥4 tests, all passing

### 5. Run tests  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py -v
```

Fix any failures.

- [ ] All tests pass

### 6. Update roadmap  <!-- agent: general-purpose -->

Edit `.docs/roadmaps/004-knowledge-graph-coaching-system.md`: replace the inline Phase 5 placeholder for the generation sub-graph with `[TASK-060: Generation agent sub-graph...](../tasks/060-generation-agent-subgraph.md)`. Update `**Last updated**`.

- [ ] Roadmap updated with task link

## Acceptance Criteria

- [ ] `backend/app/kg/generation_graph.py` with `WorkoutRecommendation`, `RecommendedExercise`, `GenerationState`, `build_generation_graph()`
- [ ] `build_generation_graph().ainvoke({"member_id": ..., "query": ..., "context": <ContextSlice>})` returns dict with `recommendation: WorkoutRecommendation`
- [ ] `fallback_triggered=True` when `safe_exercises` is empty; generation node never called in that case
- [ ] `_generate_workout_node` uses `with_structured_output(WorkoutRecommendation)` — not JSON parsing
- [ ] `backend/tests/kg/test_generation_graph.py` with ≥4 tests, all passing
- [ ] Roadmap updated

---
**UAT**: `.docs/uat/060-generation-agent-subgraph.uat.md`
