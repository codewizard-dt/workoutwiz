# 066 — Tool-Call Seam: LangChain Tools for KG Retrieval + Generation

> **Depends on**: [065-kg-fastapi-router](completed/065-kg-fastapi-router.md)
> **Blocks**: [067-hub-integration](067-hub-integration.md)
> **Parallel-safe with**: none

## Objective

Create `backend/app/kg/tools.py` exposing the knowledge graph pipeline as LangChain `@tool`-decorated functions: `kg_recommend_tool` and `kg_explain_tool`. These are callable from the hub router agent and from external LangChain agent invocations.

## Approach

LangChain tools need Pydantic input schemas with field descriptions. Use `@tool` decorator with a typed `BaseTool` subclass or just `@tool(args_schema=...)`.

```python
class KGRecommendInput(BaseModel):
    member_id: str = Field(description="The member's Neo4j UUID")
    query: str = Field(description="The workout request from the user")

class KGExplainInput(BaseModel):
    member_id: str = Field(description="The member's Neo4j UUID")
    exercise_id: str = Field(description="The exercise UUID that was skipped")
```

The tools are **async** and open their own Neo4j driver (using settings), then close it.

```python
@tool("kg_recommend", args_schema=KGRecommendInput)
async def kg_recommend_tool(member_id: str, query: str) -> dict:
    """Retrieve a personalized, injury-aware workout recommendation from the knowledge graph."""
    ...
```

## Steps

### 1. Create `backend/app/kg/tools.py`  <!-- agent: general-purpose -->

Use the `Write` tool to create:
- `KGRecommendInput` and `KGExplainInput` Pydantic models with field descriptions
- `kg_recommend_tool`: opens driver → builds retrieval graph → invokes → builds generation graph → invokes → returns dict with `exercises`, `overall_reasoning`, `skipped_exercise_ids`
- `kg_explain_tool`: opens driver → calls `explain_skipped_exercise` → returns `{"explanation": str}`
- `KG_TOOLS: list` = `[kg_recommend_tool, kg_explain_tool]`

- [ ] `backend/app/kg/tools.py` with 2 tools and `KG_TOOLS` list

### 2. Write unit tests `backend/tests/kg/test_tools.py`  <!-- agent: general-purpose -->

Tests (mock Neo4j driver and all sub-functions):
- `test_kg_recommend_tool_returns_recommendation_dict`: assert returns dict with `exercises` key
- `test_kg_explain_tool_returns_explanation_string`: assert returns dict with `explanation` key
- `test_kg_tools_have_correct_descriptions`: assert `kg_recommend_tool.description` is non-empty

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_tools.py -v
```

- [ ] Tests pass

### 3. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 6 tool-call seam placeholder with `[TASK-066: Tool-call seam...](../tasks/066-tool-call-seam.md)`.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `backend/app/kg/tools.py` with `kg_recommend_tool`, `kg_explain_tool`, `KG_TOOLS`
- [ ] Both tools have `args_schema` with `Field(description=...)` on each field
- [ ] `KG_TOOLS` list is importable and contains both tools
- [ ] Tests pass

---
**UAT**: `.docs/uat/066-tool-call-seam.uat.md`
