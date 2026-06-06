# UAT: Minimal HTML/JS Web UI

> **Source task**: [`.docs/tasks/031-web-ui.md`](../tasks/031-web-ui.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] `1-multi-agent/.venv` exists and dependencies are installed (`cd 1-multi-agent && pip install -e ".[dev]"` if not)
- [ ] Working directory for all shell commands is `1-multi-agent/`
- [ ] `1-multi-agent/demo/index.html` exists
- [ ] No `ANTHROPIC_API_KEY` required — all tests are pure-function (no real LLM calls)

---

## API Tests

### UAT-API-001: `GET /` returns 200 with HTML content-type

- **Endpoint**: `GET /`
- **Description**: Verify FastAPI serves `demo/index.html` at the root path with status 200 and `text/html` content-type.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_chat_endpoint.py::test_ui_served -v
  ```
- **Expected Result**: Exits 0. Output shows `test_ui_served PASSED`. Status code is 200 and `text/html` is in the `content-type` header.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-002: `GET /` response body contains "Workout Wiz"

- **Endpoint**: `GET /`
- **Description**: Verify the served HTML includes the application title so assessors can confirm the correct file is being served.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
resp = client.get('/')
assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
assert 'Workout Wiz' in resp.text, 'Title not found in response'
assert 'text/html' in resp.headers['content-type'], f'Wrong content-type: {resp.headers[\"content-type\"]}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-003: `GET /` response body contains the chat input and send button

- **Endpoint**: `GET /`
- **Description**: Verify the HTML contains the `#msg` input, the `#send` button, and the `#chat` container — the three structural elements required by the task.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
html = client.get('/').text
assert 'id=\"msg\"' in html, '#msg input missing'
assert 'id=\"send\"' in html, '#send button missing'
assert 'id=\"chat\"' in html, '#chat container missing'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-004: `GET /` response body includes session storage and `/chat` fetch call

- **Endpoint**: `GET /`
- **Description**: Verify the embedded JavaScript references `sessionStorage` for session persistence and `fetch` against `/chat` for API calls.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
html = client.get('/').text
assert 'sessionStorage' in html, 'sessionStorage not found in HTML'
assert \"'/chat'\" in html or '\"/chat\"' in html or \"+ '/chat'\" in html or \"API + '/chat'\" in html, '/chat fetch not found in HTML'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-005: `_DEMO_DIR` path resolution points to the correct directory

- **Endpoint**: N/A (module-level constant)
- **Description**: Verify `_DEMO_DIR` in `main.py` resolves to the `1-multi-agent/demo/` directory and that `demo/index.html` exists there — confirming the 3-parent traversal is correct.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.main import _DEMO_DIR
assert _DEMO_DIR.is_dir(), f'_DEMO_DIR is not a directory: {_DEMO_DIR}'
assert (_DEMO_DIR / 'index.html').exists(), f'index.html not found in {_DEMO_DIR}'
assert _DEMO_DIR.name == 'demo', f'Expected directory named demo, got {_DEMO_DIR.name}'
print(f'PASS: _DEMO_DIR={_DEMO_DIR}')
"
  ```
- **Expected Result**: Exits 0. Prints `PASS: _DEMO_DIR=<path>/1-multi-agent/demo`.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: Other endpoints still respond after `GET /` is mounted

- **Scenario**: Mounting the UI at `GET /` must not shadow or break `/health`, `/chat`, or `/audit/{session_id}`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
# Health must still work
h = client.get('/health')
assert h.status_code == 200, f'/health returned {h.status_code}'
# Audit 404 on unknown session must still work
a = client.get('/audit/no-such-session')
assert a.status_code == 404, f'/audit returned {a.status_code}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-002: UI response body includes routing metadata display logic

- **Scenario**: The JavaScript must format and display route + confidence metadata under each agent reply. Verify the meta-display code is present.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
html = client.get('/').text
assert 'data.route' in html, 'Route display logic missing'
assert 'confidence' in html, 'Confidence display logic missing'
assert 'meta' in html.lower(), 'Meta element creation missing'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-003: UI response body includes Enter-key send handler

- **Scenario**: The JS must bind Enter (without Shift) to the send function so keyboard-only interaction works.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
html = client.get('/').text
assert 'Enter' in html, 'Enter key handler missing'
assert 'shiftKey' in html or 'Shift' in html, 'Shift-Enter guard missing'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-004: Welcome bubble is present in initial HTML

- **Scenario**: The initial page load must include a pre-rendered agent bubble with a greeting, so assessors see content immediately without sending a message.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app
client = TestClient(app)
html = client.get('/').text
assert 'bubble agent' in html, 'No initial agent bubble in HTML'
assert 'Hi!' in html or 'help' in html.lower(), 'Welcome message missing'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

---

## Integration Tests

### UAT-INT-001: Full pytest suite for UI — `test_ui_served` passes alongside existing tests

- **Components**: `GET /`, `demo/index.html`, `_DEMO_DIR` path, FastAPI `HTMLResponse`
- **Flow**: Run the complete `test_chat_endpoint.py` suite; `test_ui_served` must pass and existing tests must not regress.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_chat_endpoint.py -v
  ```
- **Expected Result**: Exits 0. All tests pass, including `test_ui_served`. No regressions to `test_health`, `test_chat_returns_session_id`, `test_chat_reuses_session`, `test_chat_user_id_header`, `test_clear_session`.
- [ ] Pass

### UAT-INT-002: `demo/index.html` file content matches expected structure

- **Components**: `demo/index.html` (static file)
- **Flow**: Confirm the file on disk has a `<!DOCTYPE html>` declaration, the correct `<title>`, and the required CSS classes for user/agent bubbles.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from pathlib import Path
html = Path('demo/index.html').read_text()
assert html.strip().startswith('<!DOCTYPE html>'), 'Missing DOCTYPE'
assert 'Workout Wiz' in html, 'Title missing'
assert 'class=\"bubble user\"' in html or '.user' in html, 'User bubble style missing'
assert 'class=\"bubble agent\"' in html or '.agent' in html, 'Agent bubble style missing'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass
