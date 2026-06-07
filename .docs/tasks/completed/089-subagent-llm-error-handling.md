# 089 — Graceful LLM Error Handling in Coach & Generator Sub-Agents

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [086-readme-kg-production-eval](086-readme-kg-production-eval.md), [087-fix-stale-intent-values-test](087-fix-stale-intent-values-test.md)

## Objective

Wrap the Anthropic LLM invocations in the coach and workout-generator sub-agent nodes so an API exception returns a graceful fallback `AIMessage` plus an audit entry instead of propagating through LangGraph as an HTTP 500.

## Approach

Mirror the existing `_knowledge_graph_node` pattern in `backend/app/agents/hub.py`: wrap `llm.invoke(...)` in a `try`/`except Exception`, capture `latency_ms` on both paths, set fallback `content`/`tokens` in the `except` block, and always emit an audit entry appended via `list(state.get("audit_log", [])) + [audit_entry]`. The node must return `{"messages": [AIMessage(content=...)], "audit_log": ...}` on failure rather than raising.

## Prerequisites

- [ ] Read the reference implementation `_knowledge_graph_node` in `backend/app/agents/hub.py` (try/except + `latency_ms`-on-both-paths + audit-entry shape).
- [ ] Confirm the current node bodies: `_chat_node` in `backend/app/agents/coach.py` (lines ~22-49) and `_generate_node` in `backend/app/agents/workout_generator.py` (lines ~145-166), neither of which currently guards `llm.invoke`.
- [ ] Confirm the audit-entry keys used by these nodes: `event`, `model`, `provider`, `latency_ms`, `tokens_in`, `tokens_out`.

---

## Steps

### 1. Coach node error handling  <!-- agent: general-purpose -->

- [ ] In `_chat_node` (`backend/app/agents/coach.py`), move the `t0 = time.monotonic()` before the call and wrap `response = llm.invoke(messages)` in a `try`/`except Exception as exc` block.
- [ ] On the success path, keep the existing `latency_ms`, `usage`, `tokens_in`/`tokens_out` extraction unchanged.
- [ ] In the `except` block, compute `latency_ms` from `t0`, set `response = AIMessage(content=...)` with a graceful, user-facing fallback message (e.g. an apology that the coach is temporarily unavailable), and set `tokens_in = 0` / `tokens_out = 0`.
- [ ] Build the `audit_entry` (keys `event="coach"`, `model`, `provider="anthropic"`, `latency_ms`, `tokens_in`, `tokens_out`) on both paths and return `{"messages": [response], "audit_log": list(state.get("audit_log", [])) + [audit_entry]}` exactly as today — no exception escapes the node.
- [ ] Ensure `AIMessage` is imported in `coach.py` (add to the existing `langchain_core.messages` import if not already present).

### 2. Generator node error handling  <!-- agent: general-purpose -->

- [ ] In `_generate_node` (`backend/app/agents/workout_generator.py`), apply the same wrap: `try`/`except Exception as exc` around `response = llm.invoke(messages)`, computing `latency_ms` on both paths.
- [ ] In the `except` block, set `response = AIMessage(content=...)` with a graceful fallback message and `tokens_in = 0` / `tokens_out = 0` (no tool calls in the fallback response).
- [ ] Build the `audit_entry` (`event="generator"`, `model`, `provider="anthropic"`, `latency_ms`, `tokens_in`, `tokens_out`) and return `{"messages": [response], "audit_log": list(state.get("audit_log", [])) + [audit_entry]}` unchanged in shape.
- [ ] Ensure `AIMessage` is imported in `workout_generator.py`.

### 3. Tests  <!-- agent: general-purpose -->

- [ ] In `backend/tests/test_agents_coach.py`, add a test that patches `app.agents.coach.ChatAnthropic` so `mock_cls.return_value.invoke.side_effect = Exception("boom")`, invokes the compiled coach graph, and asserts the result contains a fallback `AIMessage` (last message is an `AIMessage` with non-empty content) rather than the call raising.
- [ ] Assert the fallback path still appends exactly one coach audit entry with `tokens_in == 0` and `tokens_out == 0`.
- [ ] In `backend/tests/test_agents_generator.py` (or `test_agents_critical_generator.py`), add the equivalent test patching `app.agents.workout_generator.ChatAnthropic` with an `invoke.side_effect` exception and asserting a graceful fallback message + audit entry instead of propagation.

### 4. Verification  <!-- agent: general-purpose -->

- [ ] Run `backend/.venv/bin/python -m pytest backend/tests/test_agents_coach.py backend/tests/test_agents_generator.py backend/tests/test_agents_critical_generator.py -q` and confirm all pass (new and existing).

## Acceptance Criteria

- [ ] An exception raised by `llm.invoke` in `_chat_node` is caught; the node returns a fallback `AIMessage` and a coach audit entry instead of raising.
- [ ] An exception raised by `llm.invoke` in `_generate_node` is caught; the node returns a fallback `AIMessage` and a generator audit entry instead of raising.
- [ ] Both nodes still return the same dict shape (`messages`, `audit_log`) on the success path, with unchanged behaviour.
- [ ] The error-handling structure mirrors `_knowledge_graph_node` (try/except, `latency_ms` computed on both paths, zeroed tokens on failure, audit entry always emitted).
- [ ] New tests covering the failure path pass alongside the existing agent test suite.

---
**UAT**: [`.docs/uat/completed/089-subagent-llm-error-handling.uat.md`](../uat/completed/089-subagent-llm-error-handling.uat.md)
