# UAT: Clarification Node Finalization

> **Source task**: [`.docs/tasks/026-clarification-node.md`](../tasks/026-clarification-node.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Working directory is the project root: `/Users/davidtaylor/Repositories/gauntlet/workout-wiz`
- [ ] Python virtual environment exists at `.docs/guides/1-multi-agent/.venv`
- [ ] Dependencies installed: `cd .docs/guides/1-multi-agent && .venv/bin/pip install -e .[dev] -q`
- [ ] `ANTHROPIC_API_KEY` is set in the shell environment (the router node uses `ChatAnthropic`; tests mock it, so the key does not need to be valid — but the import must resolve)

---

## Edge Case Tests

### UAT-EDGE-001: Low-confidence routing triggers clarification (confidence < 0.6)

- **Scenario**: Router returns a `RouteDecision` with `confidence=0.4` (below the 0.6 threshold). The hub must route to the clarification node rather than any sub-agent.
- **Steps**:
  1. Run the pytest suite — `test_clarification_appends_audit` exercises exactly this path (mocks the router to return confidence 0.4, intent COACH).
  2. Confirm the test passes and check the assertion: `trigger == "low_confidence"` and `confidence == 0.4`.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_clarification.py::test_clarification_appends_audit -v
  ```
- **Expected Result**: `1 passed`. Audit log contains exactly one `clarification` entry with `trigger: "low_confidence"` and `confidence: 0.4`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: FALLBACK intent triggers clarification with `fallback_intent` trigger

- **Scenario**: Router returns `intent=FALLBACK, confidence=0.3`. Trigger in the audit entry must be `"fallback_intent"` (not `"low_confidence"`) because the intent itself is FALLBACK regardless of the confidence threshold check. Wait — per the implementation: `"low_confidence" if (rd and rd.confidence < 0.6) else "fallback_intent"`. With confidence 0.3 (< 0.6) the trigger is `"low_confidence"`. Test this boundary with confidence >= 0.6 and intent FALLBACK to confirm `fallback_intent` fires.
- **Steps**:
  1. Run the full suite to confirm all three tests pass — `test_clarification_message_format` uses `confidence=0.3` (FALLBACK + low confidence → `"low_confidence"` trigger).
  2. Manually verify the boundary: the acceptance criteria requires `trigger` distinguishes low-confidence from fallback-intent cases. With `confidence >= 0.6` and `intent=FALLBACK`, the trigger must be `"fallback_intent"`.
  3. Run the one-liner below to invoke `_clarification_node` directly with a high-confidence FALLBACK decision:
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _clarification_node
from workout_wiz.state import RouteDecision, Intent
state = {'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.9, reasoning='off-topic'), 'user_id': 'u-test', 'audit_log': [], 'messages': []}
result = _clarification_node(state)
entry = result['audit_log'][-1]
print('trigger:', entry['trigger'])
print('confidence:', entry['confidence'])
assert entry['trigger'] == 'fallback_intent', f'Expected fallback_intent, got {entry[\"trigger\"]}'
assert entry['confidence'] == 0.9
print('PASS')
"
  ```
- **Expected Result**: Prints `trigger: fallback_intent`, `confidence: 0.9`, `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: Missing `route_decision` (None) produces a safe clarification message

- **Scenario**: `route_decision` is `None` in state (e.g., router node errored or graph started without pre-routing). The node must not raise an exception.
- **Steps**:
  1. Run the one-liner below to invoke `_clarification_node` with `route_decision=None`.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _clarification_node
state = {'route_decision': None, 'user_id': None, 'audit_log': [], 'messages': []}
result = _clarification_node(state)
msg = result['messages'][0].content
entry = result['audit_log'][-1]
assert 'rephrase' in msg.lower() or '?' in msg, 'Message must end with a question'
assert entry['confidence'] is None
assert entry['trigger'] == 'fallback_intent'
print('PASS:', msg[:60])
"
  ```
- **Expected Result**: Prints `PASS:` followed by the start of the clarification message. No exception raised. Audit entry has `confidence: None` and `trigger: "fallback_intent"`.
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: Full pytest suite — all 3 clarification tests pass

- **Components**: `hub.py` (`_clarification_node`), `state.py` (`RouteDecision`, `Intent`, `AgentState`), `tests/test_clarification.py`
- **Flow**: The three pytest tests exercise the clarification node through the full compiled `hub` graph with a mocked router. Each test invokes `hub.invoke()` with a specific `RouteDecision` and asserts on the returned `messages` and `audit_log`.
- **Steps**:
  1. Change into the 1-multi-agent directory and run the test file.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_clarification.py -v
  ```
- **Expected Result**: `3 passed, 0 failed`. Output shows:
  - `test_clarification_message_format PASSED`
  - `test_clarification_appends_audit PASSED`
  - `test_clarification_includes_reasoning PASSED`
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: Clarification message content — all three capabilities listed

- **Components**: `_clarification_node` in `hub.py`
- **Flow**: The message returned by the clarification node must explicitly name all three system capabilities so the user knows what the system can do.
- **Steps**:
  1. Invoke `_clarification_node` directly and assert all three capability keywords appear in the output.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _clarification_node
from workout_wiz.state import RouteDecision, Intent
state = {'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.2, reasoning='unclear'), 'user_id': 'u1', 'audit_log': [], 'messages': []}
result = _clarification_node(state)
msg = result['messages'][0].content
print(msg)
assert 'coaching' in msg.lower() or 'fitness' in msg.lower(), 'Missing coaching capability'
assert 'planning' in msg.lower() or 'workout' in msg.lower(), 'Missing workout planning capability'
assert 'logging' in msg.lower() or 'log' in msg.lower(), 'Missing workout logging capability'
assert msg.strip().endswith('?'), 'Message must end with a question'
print('PASS')
"
  ```
- **Expected Result**: Prints the full clarification message followed by `PASS`. The message contains references to fitness coaching, workout planning, and workout logging, and ends with `"Could you rephrase your request?"`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-003: Clarification message includes `route_decision.reasoning` when present

- **Components**: `_clarification_node`, `RouteDecision.reasoning` field
- **Flow**: When `route_decision.reasoning` is a non-empty string, the clarification message must embed it as `" (reason: <reasoning text>)"` so the user sees why their message was ambiguous.
- **Steps**:
  1. Invoke `_clarification_node` with a known reasoning string and assert it appears verbatim in the output.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _clarification_node
from workout_wiz.state import RouteDecision, Intent
state = {'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.1, reasoning='no recognizable keywords'), 'user_id': None, 'audit_log': [], 'messages': []}
result = _clarification_node(state)
msg = result['messages'][0].content
assert 'no recognizable keywords' in msg, f'Reasoning not in message: {msg}'
assert '(reason: no recognizable keywords)' in msg, f'Reason hint format wrong: {msg}'
print('PASS:', msg[:80])
"
  ```
- **Expected Result**: Prints `PASS:` and the start of the message. The message contains the string `(reason: no recognizable keywords)`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-004: Audit log entry is appended — not replacing existing entries

- **Components**: `_clarification_node`, `AgentState.audit_log`
- **Flow**: The node must append to any pre-existing audit log rather than replace it. This ensures the full event trail (e.g., a prior `routing` entry) is preserved.
- **Steps**:
  1. Call `_clarification_node` with an existing entry in `audit_log` and confirm both the original and the new `clarification` entry are present.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _clarification_node
from workout_wiz.state import RouteDecision, Intent
existing = [{'event': 'routing', 'intent': 'FALLBACK'}]
state = {'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.5, reasoning='ambiguous'), 'user_id': 'u3', 'audit_log': existing, 'messages': []}
result = _clarification_node(state)
log = result['audit_log']
assert len(log) == 2, f'Expected 2 entries, got {len(log)}'
assert log[0]['event'] == 'routing'
assert log[1]['event'] == 'clarification'
assert log[1]['user_id'] == 'u3'
print('PASS: audit_log length', len(log))
"
  ```
- **Expected Result**: Prints `PASS: audit_log length 2`. The original `routing` entry is at index 0; the new `clarification` entry is at index 1.
- [x] Pass <!-- 2026-06-05 -->
