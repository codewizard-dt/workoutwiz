# UAT: Graceful LLM Error Handling in Coach & Generator Sub-Agents

> **Source task**: [`.docs/tasks/completed/089-subagent-llm-error-handling.md`](../tasks/completed/089-subagent-llm-error-handling.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] `backend/.venv` exists and contains `python` and `pytest`
- [ ] The project root is `/Users/davidtaylor/Repositories/gauntlet/workout-wiz`
- [ ] No live Anthropic API key is required — all LLM calls in these tests are mocked

---

## Edge Case Tests

### UAT-EDGE-001: Coach node returns fallback AIMessage on LLM exception

- **Scenario**: `ChatAnthropic.invoke` raises `Exception("boom")` inside `_chat_node`; the LangGraph node must not propagate the exception, and must return a graceful `AIMessage` with non-empty content.
- **Steps**:
  1. The test `test_coach_llm_error_returns_fallback` in `backend/tests/test_agents_coach.py` covers this directly. Run it in isolation to confirm.
  2. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_coach.py::test_coach_llm_error_returns_fallback -v
  ```
- **Expected Result**: `1 passed` — the test asserts `last` is an `AIMessage`, `last.content` is non-empty, exactly one coach audit entry exists in `audit_log`, `tokens_in == 0`, and `tokens_out == 0`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-EDGE-002: Coach node audit entry is always emitted on LLM failure

- **Scenario**: After `llm.invoke` raises, the coach node must still append exactly one audit entry with `event="coach"` and zeroed token counts to `audit_log` — the audit trail must never be silently dropped.
- **Steps**:
  1. This is covered by `test_coach_llm_error_returns_fallback`. Re-run it and inspect the printed assertion details if it fails.
  2. The command is the same as UAT-EDGE-001 above.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_coach.py::test_coach_llm_error_returns_fallback -v -s
  ```
- **Expected Result**: `1 passed`. The audit entry must contain `event == "coach"`, `tokens_in == 0`, `tokens_out == 0`. A non-zero `latency_ms` value is present (computed from `t0` on both paths).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-EDGE-003: Generator node returns fallback AIMessage on LLM exception

- **Scenario**: `ChatAnthropic(...).bind_tools(...).invoke` raises `Exception("boom")` inside `_generate_node`; the LangGraph node must not propagate the exception and must return a graceful `AIMessage` with non-empty content.
- **Steps**:
  1. The test `test_generator_llm_error_returns_fallback` in `backend/tests/test_agents_generator.py` covers this. The `populate_exercise_cache` fixture (autouse) populates `ex_module._cache` with a fake exercise before each test.
  2. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_generator.py::test_generator_llm_error_returns_fallback -v
  ```
- **Expected Result**: `1 passed` — the test asserts `last` is an `AIMessage`, `last.content` is non-empty, exactly one generator audit entry exists in `audit_log`, `tokens_in == 0`, and `tokens_out == 0`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-EDGE-004: Generator node audit entry is always emitted on LLM failure

- **Scenario**: After `llm.invoke` raises inside `_generate_node`, exactly one audit entry with `event="generator"` and zeroed token counts must be appended to `audit_log`.
- **Steps**:
  1. Covered by `test_generator_llm_error_returns_fallback`. Run with `-s` to see output if it fails.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_generator.py::test_generator_llm_error_returns_fallback -v -s
  ```
- **Expected Result**: `1 passed`. The single generator audit entry has `event == "generator"`, `tokens_in == 0`, `tokens_out == 0`, and a numeric `latency_ms`.
- [x] Pass <!-- 2026-06-07 -->

---

## Integration Tests

### UAT-INT-001: Full agent test suite passes — coach, generator, and critical-generator

- **Components**: `test_agents_coach.py`, `test_agents_generator.py`, `test_agents_critical_generator.py`
- **Flow**: Run all three test modules together (as specified in the task's Step 4 verification command) to confirm the new fallback tests pass alongside all pre-existing tests and no regressions have been introduced.
- **Steps**:
  1. Ensure no live Anthropic API calls are made — existing tests mock `ChatAnthropic`.
  2. Run the exact command from task Step 4:
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_coach.py backend/tests/test_agents_generator.py backend/tests/test_agents_critical_generator.py -q
  ```
- **Expected Result**: All tests pass with `0 failed`. The summary line shows counts for `test_agents_coach.py` (4 tests including `test_coach_llm_error_returns_fallback`), `test_agents_generator.py` (at least 8 tests including `test_generator_llm_error_returns_fallback`), and `test_agents_critical_generator.py` (3 tests). No deprecation warnings should cause failures.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-INT-002: Coach success path is unaffected by error-handling changes

- **Scenario**: Confirm the happy path (LLM returns a valid `AIMessage`) still produces the correct output shape with a non-zero audit entry — the try/except wrapper must not alter success behavior.
- **Steps**:
  1. `test_coach_returns_ai_message` covers this path. It patches `ChatAnthropic` to return `AIMessage(content="Great question! The squat primarily targets the quadriceps.")` and asserts the message content is present.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_coach.py::test_coach_returns_ai_message -v
  ```
- **Expected Result**: `1 passed`. The last message in `result["messages"]` is an `AIMessage` whose content contains "squat" or "quadriceps".
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-INT-003: Generator success path is unaffected by error-handling changes

- **Scenario**: Confirm the generator success path (LLM returns normally, graph may call tools) is unbroken by the error-handling changes. `test_build_workout_tool_valid_ids` exercises the success branch via the tool directly, independent of LLM mocking.
- **Steps**:
  1. Run the existing generator tests that cover the success path.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && backend/.venv/bin/python -m pytest backend/tests/test_agents_generator.py -k "not error" -v
  ```
- **Expected Result**: All non-error tests pass — `test_generator_graph_compiles`, `test_search_exercises_tool_returns_results`, `test_search_exercises_tool_respects_max_results`, `test_build_workout_tool_valid_ids`, `test_build_workout_tool_rejects_invalid_ids`, `test_hub_imports_cleanly`, `test_build_workout_tool_emits_non_empty_cooldown`, `test_build_workout_tool_empty_cooldown_when_no_recovery_exercises`.
- [x] Pass <!-- 2026-06-07 -->
