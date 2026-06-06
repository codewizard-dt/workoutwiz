# UAT: Tool-Call Seam — LangChain Tools for KG Retrieval + Generation

> **Source task**: [`.docs/tasks/completed/066-tool-call-seam.md`](../tasks/completed/066-tool-call-seam.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend dependencies installed (`cd backend && pip install -e ".[dev]"` or `poetry install`)
- [ ] `.env` file present at `backend/.env` with `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` set (values do not need to be a live instance — unit tests mock the driver)
- [ ] `backend/app/kg/tools.py` exists

---

## Unit Tests (via pytest)

These tests verify the module-level contract of `backend/app/kg/tools.py` — importability, schema structure, tool metadata, and return-shape correctness under mocked Neo4j.

### UAT-UNIT-001: Run the full test suite for tools.py
- **Description**: Verify all unit tests in `backend/tests/kg/test_tools.py` pass, covering both tools and the `KG_TOOLS` list.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_tools.py -v
  ```
- **Expected Result**: All tests collected and pass (`5 passed` or more, zero failures, zero errors). Output ends with a green `passed` summary line.
- [x] Pass <!-- 2026-06-06 -->

---

## Import / Static Contract Tests

These verify the module exports the required symbols with the required structure (no Neo4j connection needed).

### UAT-STATIC-001: `backend/app/kg/tools.py` is importable and exports `KG_TOOLS`
- **Description**: Confirm the module can be imported and `KG_TOOLS` is a non-empty list containing both tools.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.tools import KG_TOOLS, kg_recommend_tool, kg_explain_tool; print('tools:', [t.name for t in KG_TOOLS]); assert len(KG_TOOLS) == 2; assert kg_recommend_tool in KG_TOOLS; assert kg_explain_tool in KG_TOOLS; print('OK')"
  ```
- **Expected Result**: Output contains `tools: ['kg_recommend', 'kg_explain']` (order may vary) followed by `OK`. No ImportError or AssertionError.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-002: Both tools have non-empty `description` strings
- **Description**: LangChain tools must expose a description for the hub router to surface them correctly.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.tools import kg_recommend_tool, kg_explain_tool; assert kg_recommend_tool.description, 'recommend description empty'; assert kg_explain_tool.description, 'explain description empty'; print('recommend:', kg_recommend_tool.description[:60]); print('explain:', kg_explain_tool.description[:60]); print('OK')"
  ```
- **Expected Result**: Two lines of description text (truncated to 60 chars) followed by `OK`. No AssertionError.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-003: `KGRecommendInput` has `member_id` and `query` fields with descriptions
- **Description**: Pydantic input schema fields must have `description` values for LangChain structured output.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.tools import KGRecommendInput; s = KGRecommendInput.model_json_schema(); props = s['properties']; assert 'member_id' in props; assert 'query' in props; assert props['member_id'].get('description'), 'member_id missing description'; assert props['query'].get('description'), 'query missing description'; print('member_id desc:', props['member_id']['description']); print('query desc:', props['query']['description']); print('OK')"
  ```
- **Expected Result**: Two description lines printed (non-empty strings) followed by `OK`. No AssertionError.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-004: `KGExplainInput` has `member_id` and `exercise_id` fields with descriptions
- **Description**: Pydantic input schema fields must have `description` values for LangChain structured output.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.tools import KGExplainInput; s = KGExplainInput.model_json_schema(); props = s['properties']; assert 'member_id' in props; assert 'exercise_id' in props; assert props['member_id'].get('description'), 'member_id missing description'; assert props['exercise_id'].get('description'), 'exercise_id missing description'; print('member_id desc:', props['member_id']['description']); print('exercise_id desc:', props['exercise_id']['description']); print('OK')"
  ```
- **Expected Result**: Two description lines printed (non-empty strings) followed by `OK`. No AssertionError.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-005: `kg_recommend_tool` has `args_schema` set to `KGRecommendInput`
- **Description**: The `args_schema` attribute on the tool must be the `KGRecommendInput` Pydantic class so LangChain can validate and parse inputs.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.tools import kg_recommend_tool, KGRecommendInput; assert kg_recommend_tool.args_schema is KGRecommendInput, f'Expected KGRecommendInput, got {kg_recommend_tool.args_schema}'; print('OK')"
  ```
- **Expected Result**: Output is `OK`. No AssertionError.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-006: `kg_explain_tool` has `args_schema` set to `KGExplainInput`
- **Description**: The `args_schema` attribute on the tool must be the `KGExplainInput` Pydantic class.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.tools import kg_explain_tool, KGExplainInput; assert kg_explain_tool.args_schema is KGExplainInput, f'Expected KGExplainInput, got {kg_explain_tool.args_schema}'; print('OK')"
  ```
- **Expected Result**: Output is `OK`. No AssertionError.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: `kg_recommend_tool` returns fallback dict when generation graph yields no recommendation
- **Description**: When the generation graph returns `{"recommendation": None}`, the tool must return `{"exercises": [], "overall_reasoning": "No recommendation generated.", "skipped_exercise_ids": []}` rather than raising.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
import asyncio
from unittest.mock import AsyncMock, patch
from app.kg.tools import kg_recommend_tool

async def run():
    mock_driver = AsyncMock()
    mock_retrieval = AsyncMock()
    mock_retrieval.ainvoke = AsyncMock(return_value={'context': {}})
    mock_generation = AsyncMock()
    mock_generation.ainvoke = AsyncMock(return_value={'recommendation': None})
    with patch('app.kg.tools.neo4j.AsyncGraphDatabase.driver', return_value=mock_driver), \
         patch('app.kg.tools.build_retrieval_graph', return_value=mock_retrieval), \
         patch('app.kg.tools.build_generation_graph', return_value=mock_generation):
        result = await kg_recommend_tool.ainvoke({'member_id': 'test-member', 'query': 'legs'})
    assert result == {'exercises': [], 'overall_reasoning': 'No recommendation generated.', 'skipped_exercise_ids': []}, f'Got: {result}'
    print('OK')

asyncio.run(run())
"
  ```
- **Expected Result**: Output is `OK`. No exception raised.
- [x] Pass <!-- 2026-06-06 -->
