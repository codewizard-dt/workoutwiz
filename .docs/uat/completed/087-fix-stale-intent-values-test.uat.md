# UAT: Fix Stale test_intent_values Assertion (add KNOWLEDGE_GRAPH)

> **Source task**: [`.docs/tasks/087-fix-stale-intent-values-test.md`](../tasks/087-fix-stale-intent-values-test.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] Backend virtualenv is available (`backend/.venv/` exists or a system venv with project deps installed)
- [ ] `.env` is present at the repository root (the pytest command sources it)
- [ ] `python -m pytest` is executable from within `backend/`

---

## Edge Case Tests

### UAT-EDGE-001: Assertion in test_intent_values contains all five Intent members

- **Scenario**: The one-line fix has been applied — the expected set in `backend/tests/test_agents_state.py::test_intent_values` must include `Intent.KNOWLEDGE_GRAPH` alongside the original four members.
- **Steps**:
  1. From the repository root, run the command below to print the assertion line from the test file.
- **Command**:
  ```bash
  python3 -c "
import ast, sys
src = open('backend/tests/test_agents_state.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'test_intent_values':
        lines = src.splitlines()[node.lineno - 1 : node.end_lineno]
        print('\n'.join(lines))
"
  ```
- **Expected Result**: Output contains a single `assert set(Intent) == {...}` line that includes all five members: `Intent.COACH`, `Intent.WORKOUT_GENERATE`, `Intent.WORKOUT_LOG`, `Intent.FALLBACK`, and `Intent.KNOWLEDGE_GRAPH`. The member `Intent.KNOWLEDGE_GRAPH` must be present; absence means the fix was not applied.
- [x] Pass <!-- 2026-06-07 -->

---

## Integration Tests

### UAT-INT-001: Full test_agents_state.py suite passes with no failures

- **Components**: `backend/tests/test_agents_state.py`, `backend/app/agents/state.py` (`Intent` enum, `RouteDecision` model)
- **Flow**: Source `.env`, activate the backend virtualenv, run pytest on the single test module, confirm all three tests (`test_intent_values`, `test_route_decision_valid`, `test_route_decision_confidence_bounds`) report `PASSED`.
- **Steps**:
  1. From the repository root, run the command below (it sources `.env` then runs pytest).
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/test_agents_state.py -v
  ```
- **Expected Result**: Exit code `0`. Output shows:
  ```
  PASSED tests/test_agents_state.py::test_route_decision_valid
  PASSED tests/test_agents_state.py::test_route_decision_confidence_bounds
  PASSED tests/test_agents_state.py::test_intent_values
  3 passed
  ```
  No failures, no errors. The `test_intent_values` test must report `PASSED` (not `FAILED` with `AssertionError`).
- [x] Pass <!-- 2026-06-07 -->

### UAT-INT-002: Intent enum in state.py defines exactly five members including KNOWLEDGE_GRAPH

- **Components**: `backend/app/agents/state.py`
- **Flow**: Verify the source enum that the test exercises has exactly the five members the test asserts against, confirming enum and test are in sync.
- **Steps**:
  1. From the repository root, run the command below.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.agents.state import Intent; members = [m.value for m in Intent]; print(members); assert set(members) == {'COACH','WORKOUT_GENERATE','WORKOUT_LOG','FALLBACK','KNOWLEDGE_GRAPH'}, f'Unexpected members: {members}'"
  ```
- **Expected Result**: Exit code `0`. Output prints the list of five values, e.g. `['COACH', 'WORKOUT_GENERATE', 'WORKOUT_LOG', 'FALLBACK', 'KNOWLEDGE_GRAPH']` (order may vary). The assertion in the command itself passes silently, meaning the enum contains exactly those five members and no others.
- [x] Pass <!-- 2026-06-07 -->
