# 031 — Minimal HTML/JS Web UI

> **Depends on**: [030-chat-endpoint](030-chat-endpoint.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Create a minimal single-file HTML/JS chat interface served by FastAPI at `GET /` that lets assessors interact with all three routing paths (coaching, workout generation, workout logging) in a browser — satisfying the assessment requirement for a runnable demo.

## Approach

A single `demo/index.html` file served by FastAPI's `StaticFiles` mount (or inline via `HTMLResponse`). Pure vanilla HTML/JS — no bundler, no React, no npm. The UI shows a chat window with message history, a text input, and a "Send" button. Each response shows the routing metadata (route, confidence) beneath the reply so assessors can see the system working. Session ID is stored in `sessionStorage` for persistence across page reloads.

## Steps

### 1. Create demo/index.html  <!-- agent: general-purpose -->

Create `.docs/guides/1-multi-agent/demo/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Workout Wiz — Fitness Coaching Demo</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5; display: flex; flex-direction: column; height: 100vh; }
    header { background: #1a1a2e; color: white; padding: 16px 24px; }
    header h1 { font-size: 1.2rem; }
    header p { font-size: 0.8rem; color: #aaa; margin-top: 4px; }
    #chat { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
    .bubble { max-width: 75%; padding: 12px 16px; border-radius: 12px; line-height: 1.5; }
    .user { background: #1a1a2e; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
    .agent { background: white; border: 1px solid #ddd; align-self: flex-start; border-bottom-left-radius: 4px; }
    .meta { font-size: 0.7rem; color: #888; margin-top: 4px; }
    #input-row { display: flex; gap: 8px; padding: 16px 24px; background: white; border-top: 1px solid #ddd; }
    #msg { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; }
    button { padding: 10px 20px; background: #1a1a2e; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }
    button:disabled { background: #999; }
    .typing { color: #888; font-style: italic; }
  </style>
</head>
<body>
  <header>
    <h1>Workout Wiz</h1>
    <p>Fitness coaching · Workout planning · Workout logging</p>
  </header>
  <div id="chat">
    <div class="bubble agent">
      <div>Hi! I can help with fitness coaching, workout planning, or logging your workouts. What would you like to do?</div>
    </div>
  </div>
  <div id="input-row">
    <input id="msg" type="text" placeholder="Ask me anything about fitness..." autofocus>
    <button id="send">Send</button>
  </div>
  <script>
    const API = '';
    let sessionId = sessionStorage.getItem('ww_session') || null;
    const chat = document.getElementById('chat');
    const input = document.getElementById('msg');
    const sendBtn = document.getElementById('send');

    function addBubble(text, role, meta) {
      const div = document.createElement('div');
      div.className = 'bubble ' + role;
      div.innerHTML = '<div>' + text.replace(/\n/g, '<br>') + '</div>';
      if (meta) {
        const m = document.createElement('div');
        m.className = 'meta';
        m.textContent = meta;
        div.appendChild(m);
      }
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    }

    async function send() {
      const message = input.value.trim();
      if (!message) return;
      input.value = '';
      sendBtn.disabled = true;
      addBubble(message, 'user', null);
      const typing = document.createElement('div');
      typing.className = 'bubble agent typing';
      typing.textContent = 'Thinking...';
      chat.appendChild(typing);
      chat.scrollTop = chat.scrollHeight;

      try {
        const resp = await fetch(API + '/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message, session_id: sessionId}),
        });
        const data = await resp.json();
        typing.remove();
        sessionId = data.session_id;
        sessionStorage.setItem('ww_session', sessionId);
        const meta = data.route ? `Route: ${data.route} (${Math.round((data.confidence || 0) * 100)}% confidence)` : null;
        addBubble(data.reply || '(no response)', 'agent', meta);
      } catch (err) {
        typing.remove();
        addBubble('Error: ' + err.message, 'agent', null);
      } finally {
        sendBtn.disabled = false;
        input.focus();
      }
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
  </script>
</body>
</html>
```

- [ ] `demo/index.html` exists
- [ ] Chat UI shows user and agent bubbles
- [ ] Routing metadata (route, confidence) displayed beneath each agent reply
- [ ] `sessionStorage` used to persist session ID across page reloads
- [ ] "Enter" key sends the message

### 2. Serve the UI from FastAPI  <!-- agent: general-purpose -->

Add static file serving to `src/workout_wiz/main.py`. Add these imports and mount after the existing routes:

```python
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Serve demo UI — compute path relative to this file
_DEMO_DIR = Path(__file__).parent.parent.parent.parent / "demo"


@app.get("/", response_class=HTMLResponse)
async def ui():
    """Serve the chat UI."""
    index = _DEMO_DIR / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>Demo UI not found</h1>", status_code=404)
    return HTMLResponse(index.read_text())
```

Note: The path `Path(__file__).parent.parent.parent.parent / "demo"` resolves from `src/workout_wiz/main.py`:
- `.parent` = `src/workout_wiz/`
- `.parent.parent` = `src/`
- `.parent.parent.parent` = `.docs/guides/1-multi-agent/`
- `/ "demo"` = `.docs/guides/1-multi-agent/demo/`

That's 3 `.parent` calls, not 4. Verify and fix if needed.

- [ ] `GET /` serves `demo/index.html` as HTML
- [ ] Path resolution from `main.py` to `demo/index.html` is correct (3 `.parent` calls)

### 3. Test that UI is served  <!-- agent: general-purpose -->

Add a test to `tests/test_chat_endpoint.py` (append, don't replace):

```python
def test_ui_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Workout Wiz" in resp.text
```

Run: `cd 1-multi-agent && .venv/bin/pytest tests/test_chat_endpoint.py::test_ui_served -v`

- [ ] `test_ui_served` passes

## Acceptance Criteria

- [ ] `demo/index.html` exists with a functional chat UI (bubbles, input, send button)
- [ ] UI shows route + confidence metadata beneath each response
- [ ] `GET /` serves `index.html` (status 200, content-type text/html, body contains "Workout Wiz")
- [ ] Session ID persisted in `sessionStorage`
- [ ] `pytest tests/test_chat_endpoint.py::test_ui_served` passes
