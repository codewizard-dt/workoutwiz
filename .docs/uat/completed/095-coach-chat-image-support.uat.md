# UAT: Image Upload & Display in Coach Copilot Chat

> **Source task**: [`.docs/tasks/completed/095-coach-chat-image-support.md`](../../tasks/completed/095-coach-chat-image-support.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Backend server running on `http://localhost:8000`
- [ ] Frontend dev server running on `http://localhost:5173`
- [ ] `$UAT_AUTH_TOKEN` set to a valid JWT (obtain via `POST /api/auth/jwt/login`)
- [ ] Neo4j running with Jordan Rivera's member context seeded

---

## API Tests

### UAT-API-001: POST /coach/chat accepts optional image field without breaking existing request
- **Endpoint**: `POST /api/coach/chat`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify that adding an `image` field (data URL) to the request body is accepted without a validation error and returns the normal response shape including the new `image` field.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"How is adherence?","session_id":null,"image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}' | jq '{reply,session_id,grounded_facts,image}'
  ```
- **Expected Result**: `200 OK` with JSON containing `reply` (non-empty string), `session_id` (non-empty string), `grounded_facts` (array), and `image: null` (field present, value null since the backend does not echo the image in this task).
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-002: POST /coach/chat without image field still works (no regression)
- **Endpoint**: `POST /api/coach/chat`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify the existing chat contract is unbroken — requests without `image` continue to return `200 OK` with the normal response shape.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"What are Jordan'\''s goals?","session_id":null}' | jq '{reply,session_id,grounded_facts,image}'
  ```
- **Expected Result**: `200 OK` with `reply` (non-empty string), `session_id` (non-empty string), `grounded_facts` (array), `image: null`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-003: POST /coach/chat with image=null is accepted
- **Endpoint**: `POST /api/coach/chat`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify that explicitly passing `image: null` is accepted (it is the default value).
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/api/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Brief summary","session_id":null,"image":null}' | jq '{reply,session_id}'
  ```
- **Expected Result**: `200 OK` with `reply` (non-empty string) and `session_id` (non-empty string). No validation error.
- [x] Pass <!-- 2026-06-08 -->

---

## UI Tests

### UAT-UI-001: Image attach button is visible in the Coach Copilot composer
- **Page**: `http://localhost:5173/coach`
- **Description**: Verify a brand-styled image attach button (🖼) is rendered in the composer input row.
- **Steps**:
  1. Navigate to `http://localhost:5173/coach` (log in if redirected)
  2. Scroll to the **Coach Copilot** section at the bottom of the page
  3. Locate the composer area (textarea + Send button)
  4. Look for an image attach button to the left of the textarea
- **Expected Result**: A button with label `🖼` (aria-label "Attach image") is visible in the input row, rendered with `ww-btn ww-btn--ghost ww-btn--sm` classes. The Send button starts disabled (no draft text, no pending image).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-002: Selecting an image shows a removable thumbnail preview
- **Page**: `http://localhost:5173/coach`
- **Description**: Verify that picking an image via the file picker shows a thumbnail preview with a remove button above the input row.
- **Steps**:
  1. Navigate to `http://localhost:5173/coach`
  2. Click the 🖼 attach button to open the file picker
  3. Select any local image file (PNG, JPG, etc.)
  4. Observe the area above the textarea
- **Expected Result**: A thumbnail `<img alt="Attachment preview">` appears above the textarea, constrained to max-height `4rem`. A `✕` button (aria-label "Remove image") is shown beside it. The Send button becomes enabled even with an empty textarea.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-003: Remove button clears the pending image preview
- **Page**: `http://localhost:5173/coach`
- **Description**: Verify that clicking the ✕ button removes the thumbnail and disables Send again (if textarea is also empty).
- **Steps**:
  1. Attach an image as in UAT-UI-002
  2. Click the ✕ (aria-label "Remove image") button
  3. Observe the composer area
- **Expected Result**: The thumbnail preview disappears. The Send button returns to disabled state (empty textarea, no pending image).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-004: Sending a message with an attached image renders image inside the chat bubble
- **Page**: `http://localhost:5173/coach`
- **Description**: Verify that after Send, the user's message bubble contains the attached image rendered via `<img alt="Attached image">`.
- **Steps**:
  1. Attach an image file as in UAT-UI-002
  2. Optionally type a message in the textarea (e.g. "Look at this form")
  3. Click **Send**
  4. Observe the user message bubble that appears in the chat stream
- **Expected Result**: A new user bubble appears containing the attached image (`<img alt="Attached image">`) constrained to max-height `16rem`. If text was typed it also appears in the bubble. The pending preview and textarea are cleared after sending. The `pendingImage` state is reset (Send button is disabled again after the response arrives).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-005: Image-only message can be sent (no text required)
- **Page**: `http://localhost:5173/coach`
- **Description**: Verify Send is enabled and submits successfully when only an image is attached and the textarea is empty.
- **Steps**:
  1. Ensure the textarea is empty
  2. Attach an image file
  3. Confirm the Send button is enabled
  4. Click **Send**
  5. Observe the chat stream
- **Expected Result**: The request is sent and a user bubble containing only the image appears. The assistant replies (may be generic since the backend does not process the image in this task). No JS error is thrown.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-006: Image remains visible in scrollback history after subsequent messages
- **Page**: `http://localhost:5173/coach`
- **Description**: Verify that an image attached in an earlier message stays visible in the conversation history after more messages are exchanged.
- **Steps**:
  1. Send a message with an attached image (UAT-UI-004 scenario)
  2. Wait for the assistant reply
  3. Send a second text-only message (e.g. "How is adherence?")
  4. Wait for the second assistant reply
  5. Scroll up to the first user bubble
- **Expected Result**: The first user bubble still shows the attached image (`<img alt="Attached image">`). The image is not removed or replaced by subsequent messages. Both assistant replies are also visible.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: Send button remains disabled when both textarea and pending image are empty
- **Scenario**: Guard against accidental empty sends after removing pending image
- **Page**: `http://localhost:5173/coach`
- **Steps**:
  1. Navigate to `/coach`
  2. Do not type anything in the textarea
  3. Do not attach any image
  4. Observe the Send button
- **Expected Result**: Send button has the `disabled` attribute and cannot be clicked.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-EDGE-002: Attaching the same file twice works (input is reset after each pick)
- **Scenario**: The hidden file input is reset to `""` after each selection so the `onChange` fires again if the user picks the same file
- **Page**: `http://localhost:5173/coach`
- **Steps**:
  1. Attach an image file
  2. Click ✕ to remove it
  3. Click the 🖼 attach button again
  4. Select the exact same file
- **Expected Result**: The thumbnail preview reappears correctly. No stale state or broken preview.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

*Note: UAT-UI-* tests require human verification (browser interaction). They are marked `[FAIL: auto-judge: UI test requires human verification]` by `/uat-auto`.*
