# UAT: README Production Evaluation Section

> **Source task**: [`.docs/tasks/036-readme-production-eval.md`](../tasks/036-readme-production-eval.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] `.docs/guides/1-multi-agent/README.md` exists in the repo
- [ ] The multi-agent app can be started (`cd .docs/guides/1-multi-agent && uvicorn workout_wiz.main:app --port 8000`) — required only for API-backed tests; structure tests run offline
- [ ] `ANTHROPIC_API_KEY` is set in the environment

---

## Content Structure Tests

### UAT-CONTENT-001: Production Evaluation heading is present

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify the `## Production Evaluation` heading appears in the README so assessors can locate the section.
- **Steps**:
  1. Run the command below against the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
assert '## Production Evaluation' in content, 'FAIL: heading not found'
print('PASS: ## Production Evaluation heading present')
"
  ```
- **Expected Result**: Prints `PASS: ## Production Evaluation heading present`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-CONTENT-002: Metrics table contains all required rows

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify the Key Metrics table includes all five required metrics: router latency, routing accuracy, fallback rate, invalid ID rate, and token budget.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
required = [
    'Router latency',
    'Routing accuracy',
    'Fallback rate',
    'Invalid ID rate',
    'Token budget',
]
missing = [r for r in required if r not in content]
if missing:
    print('FAIL: missing metrics:', missing)
else:
    print('PASS: all required metrics present')
"
  ```
- **Expected Result**: Prints `PASS: all required metrics present`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-CONTENT-003: Metrics table includes target values and measurement methods

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify every required metric row has a target value and a measurement method (three-column table structure).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
checks = [
    ('< 800 ms', 'router latency target'),
    ('audit_log', 'measurement via audit_log'),
    ('≥ 90 %', 'routing accuracy target'),
    ('< 15 %', 'fallback rate target'),
    ('0 %', 'invalid ID rate target'),
    ('< 2 000 tokens', 'token budget target'),
]
missing = [(txt, label) for txt, label in checks if txt not in content]
if missing:
    print('FAIL: missing content:', missing)
else:
    print('PASS: all target values and measurement methods present')
"
  ```
- **Expected Result**: Prints `PASS: all target values and measurement methods present`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-CONTENT-004: Failure modes cover three required scenarios

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify the Failure Modes subsection covers LLM timeout, low-confidence routing, and fuzzy match failures as required by the acceptance criteria.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
required = [
    'LLM timeout',
    'Low-confidence routing',
    'Fuzzy match failure',
]
missing = [r for r in required if r not in content]
if missing:
    print('FAIL: missing failure modes:', missing)
else:
    print('PASS: all required failure modes documented')
"
  ```
- **Expected Result**: Prints `PASS: all required failure modes documented`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-CONTENT-005: Health signals list is present and actionable

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify the Health Signals subsection exists and references at least the `GET /health` check and audit log checks as per the task's acceptance criteria.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
required = [
    '### Health Signals',
    'GET /health',
    'GET /audit/',
]
missing = [r for r in required if r not in content]
if missing:
    print('FAIL: missing health signal content:', missing)
else:
    print('PASS: health signals section is present and actionable')
"
  ```
- **Expected Result**: Prints `PASS: health signals section is present and actionable`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-CONTENT-006: Demo runbook contains startup command and all four route prompts

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify the Running the Demo subsection includes a `uvicorn` startup command and golden-path example prompts for all four routes (COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
required = [
    'uvicorn workout_wiz.main:app',
    'COACH',
    'WORKOUT_GENERATE',
    'WORKOUT_LOG',
    'FALLBACK',
]
missing = [r for r in required if r not in content]
if missing:
    print('FAIL: missing demo runbook content:', missing)
else:
    print('PASS: startup command and all four route prompts present')
"
  ```
- **Expected Result**: Prints `PASS: startup command and all four route prompts present`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-CONTENT-007: No unclosed markdown code fences

- **File**: `.docs/guides/1-multi-agent/README.md`
- **Description**: Verify the README has an even number of triple-backtick fences, meaning all code blocks are properly closed.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  python3 -c "
content = open('.docs/guides/1-multi-agent/README.md').read()
fences = content.count('\`\`\`')
if fences % 2 != 0:
    print(f'FAIL: odd number of code fences ({fences}) — likely unclosed block')
else:
    print(f'PASS: {fences} code fences, all closed')
"
  ```
- **Expected Result**: Prints `PASS: 4 code fences, all closed` (or any even count)
- [x] Pass <!-- 2026-06-05 -->

---

## API Tests

### UAT-API-001: Health endpoint returns 200

- **Endpoint**: `GET /health`
- **Description**: Verify the server is running and the health endpoint (referenced in the Health Signals section) returns `{"status": "ok"}`. This validates the first health signal the README instructs operators to check.
- **Steps**:
  1. Start the server: `cd .docs/guides/1-multi-agent && uvicorn workout_wiz.main:app --port 8000`
  2. Run the command below
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/health'
  ```
- **Expected Result**: `{"status":"ok"}` with HTTP 200
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-002: Chat endpoint routes COACH intent correctly

- **Endpoint**: `POST /chat`
- **Description**: Verify the golden-path COACH prompt from the README demo table routes to the `COACH` intent and returns a reply with session metadata.
- **Steps**:
  1. Ensure server is running (see UAT-API-001)
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"How many rest days should I take per week for hypertrophy?"}' | jq '{session_id, route, confidence}'
  ```
- **Expected Result**: JSON object with `"route": "COACH"`, a non-null `confidence` value, and a non-empty `session_id`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-003: Chat endpoint routes WORKOUT_GENERATE intent correctly

- **Endpoint**: `POST /chat`
- **Description**: Verify the golden-path WORKOUT_GENERATE prompt from the README demo table routes to the correct intent.
- **Steps**:
  1. Ensure server is running (see UAT-API-001)
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"Give me a 45-minute full-body strength workout with dumbbells."}' | jq '{session_id, route, confidence}'
  ```
- **Expected Result**: JSON object with `"route": "WORKOUT_GENERATE"` and a non-null `confidence`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-004: Chat endpoint routes WORKOUT_LOG intent correctly

- **Endpoint**: `POST /chat`
- **Description**: Verify the golden-path WORKOUT_LOG prompt from the README demo table routes to the correct intent.
- **Steps**:
  1. Ensure server is running (see UAT-API-001)
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"I just did 3 sets of 10 bench press at 135 lbs and a 20-minute run."}' | jq '{session_id, route, confidence}'
  ```
- **Expected Result**: JSON object with `"route": "WORKOUT_LOG"` and a non-null `confidence`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-005: Chat endpoint routes FALLBACK for off-topic input

- **Endpoint**: `POST /chat`
- **Description**: Verify the golden-path FALLBACK prompt from the README demo table routes to the FALLBACK intent (off-topic request).
- **Steps**:
  1. Ensure server is running (see UAT-API-001)
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"What'\''s the best recipe for banana bread?"}' | jq '{session_id, route, confidence}'
  ```
- **Expected Result**: JSON object with `"route": "FALLBACK"` and a non-null `confidence`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-006: Audit endpoint returns session data with audit_log

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the audit endpoint referenced in the README metrics section returns the session audit log with router events. Use the session_id from UAT-API-002.
- **Steps**:
  1. Copy the `session_id` returned from UAT-API-002
  2. Substitute it into the command below (replace `<session-id-from-UAT-API-002>`)
  3. Run the command
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/audit/<session-id-from-UAT-API-002>' | jq '{session_id, total_entries, audit_log_events: [.audit_log[].event]}'
  ```
- **Expected Result**: JSON with `session_id` matching the substituted value, `total_entries` >= 1, and `audit_log_events` array containing at least `"router"`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-007: Audit endpoint returns 404 for unknown session

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the 404 behavior documented in the Health Signals section — "GET /audit/{session_id} returns 404" when the session does not exist.
- **Steps**:
  1. Ensure server is running (see UAT-API-001)
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' 'http://localhost:8000/audit/nonexistent-session-id-00000000'
  ```
- **Expected Result**: `404`
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: Audit log includes latency_ms for router event

- **Scenario**: The metrics table in the README specifies `audit_log[].latency_ms` where `event == "router"` as the measurement method for router latency. Verify this field actually appears in router audit entries.
- **Steps**:
  1. Ensure the server is running (see UAT-API-001)
  2. Send a COACH chat message and capture the session_id
  3. Run the audit endpoint and check for latency_ms in router entries
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"How many rest days for hypertrophy?"}' | jq '.audit_log[] | select(.event == "router") | {event, route, confidence, latency_ms}'
  ```
- **Expected Result**: At least one JSON object with `"event": "router"`, a `route` string, a numeric `confidence`, and a numeric `latency_ms` field
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-EDGE-002: Chat response includes audit_log inline

- **Scenario**: The README states the full per-call audit trail is available in the chat response itself (before fetching `GET /audit/{session_id}`). Verify `audit_log` is non-empty in the direct chat response.
- **Steps**:
  1. Ensure the server is running (see UAT-API-001)
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"What muscles does a squat work?"}' | jq '{route, confidence, audit_log_count: (.audit_log | length)}'
  ```
- **Expected Result**: JSON with a non-null `route`, non-null `confidence`, and `audit_log_count` >= 1
- [x] Pass <!-- 2026-06-05 -->
