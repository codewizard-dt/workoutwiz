# 036 — README Production Evaluation Section

> **Depends on**: [030-chat-endpoint](030-chat-endpoint.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md), [035-e2e-smoke-test](035-e2e-smoke-test.md)

## Objective

Add a `## Production Evaluation` section to `.docs/guides/1-multi-agent/README.md` that gives assessors (and future operators) a concrete picture of how to monitor this system in production — key metrics, known failure modes, health signals, and the one-command demo.

## Approach

Write the section directly in `.docs/guides/1-multi-agent/README.md` after any existing content. The section must cover four subsections: metrics (latency per route, routing accuracy, fallback rate), failure modes (LLM timeout, low-confidence routing, fuzzy match failures), health signals (what to observe when the system misbehaves), and the demo runbook (single command to start, what to type for each route). Keep it concise — assessors read this on GitHub; it should be scannable, not a wall of prose.

## Steps

### 1. Read the existing README  <!-- agent: general-purpose -->

Read `.docs/guides/1-multi-agent/README.md` to understand the current structure. Find the last heading so the new section can be appended cleanly after it.

- [ ] Existing README content noted — no existing "Production Evaluation" section

### 2. Append the Production Evaluation section  <!-- agent: general-purpose -->

Append the following section to `.docs/guides/1-multi-agent/README.md` (after all existing content):

```markdown
## Production Evaluation

> How to know if the system is working correctly, what breaks first, and how to demo it.

### Key Metrics to Monitor

| Metric | Target | How to measure |
|--------|--------|----------------|
| Router latency (p95) | < 800 ms | `audit_log[].latency_ms` where `event == "router"` |
| Sub-agent latency (p95) | < 3 000 ms | `audit_log[].latency_ms` for coach/generator/logger events |
| Routing accuracy | ≥ 90 % | Compare `audit_log[].route` to ground-truth intent labels |
| Fallback rate | < 15 % | Count `route == "FALLBACK"` / total requests |
| Invalid ID rate | 0 % | `build_workout_tool` `invalid_ids_skipped` length per call |
| Token budget (p95) | < 2 000 tokens/turn | Sum `tokens_in + tokens_out` across all audit entries per turn |

Retrieve per-session audit data at any time:

```bash
curl http://localhost:8000/audit/{session_id}
```

### Failure Modes

**1. LLM timeout / API error**
The router node and all sub-agent nodes make synchronous Anthropic API calls. If the network or Anthropic is degraded, the call raises an exception that propagates through the hub. The chat endpoint returns HTTP 500.
*Mitigation*: wrap LLM calls in a try/except that returns a FALLBACK route with a user-facing error message; set `httpx` timeout to 30 s.

**2. Low-confidence routing**
When the router's `confidence` is below 0.6, the hub routes to the clarification node. If this happens frequently (> 15 % of requests), the system prompt may need adjustment or the `RouteDecision` schema descriptions need more specificity.
*Signal*: high fallback rate in audit log; users reporting "can you rephrase?" on clearly valid inputs.

**3. Fuzzy match failure in workout logger**
The logger sub-agent uses fuzzy string matching to map free-text exercise names to `exercises.json` IDs. If the user types a name that is too far from any entry (e.g. a brand name or non-English term), the match returns `None` and the exercise is skipped silently.
*Signal*: logged workout has fewer exercises than the user mentioned; `invalid_ids_skipped` is non-empty in generator audit entries.

**4. Session state growth (memory leak)**
The in-memory `_sessions` dict is never evicted. Long-running servers accumulate session state indefinitely.
*Mitigation*: add a TTL-based cleanup job (e.g. `asyncio` background task that deletes sessions older than 24 h). Not implemented in this demo.

**5. Hallucinated exercise IDs**
If the LLM in the generator sub-agent ignores the `search_exercises_tool` results and fabricates UUIDs in `build_workout_tool` arguments, those IDs land in `invalid_ids_skipped`. The grounding test (test B) catches this class of failure at development time.
*Signal*: non-empty `invalid_ids_skipped` in production audit logs.

### Health Signals

When the system misbehaves, check these in order:

1. **`GET /health` returns non-200** → app is not running or crashed on startup (check `uvicorn` logs for import errors).
2. **High fallback rate** → router prompt needs tuning or `RouteDecision` schema descriptions are ambiguous.
3. **All requests route to the same intent** → LLM is ignoring the schema (check `with_structured_output` is wired correctly and the model supports it).
4. **Latency spikes** → Anthropic API is degraded; check [status.anthropic.com](https://status.anthropic.com).
5. **`invalid_ids_skipped` non-empty** → grounding failure; re-run test B and inspect the `search_exercises_tool` output for that session.
6. **`GET /audit/{session_id}` returns 404** → session was deleted or the server was restarted (in-memory state is lost on restart).

### Running the Demo

**Prerequisites**: Python 3.11+, `ANTHROPIC_API_KEY` set in environment.

```bash
# From the repo root
cd 1-multi-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn workout_wiz.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

**Golden-path prompts for each route:**

| Route | Example prompt |
|-------|---------------|
| COACH | "How many rest days should I take per week for hypertrophy?" |
| WORKOUT_GENERATE | "Give me a 45-minute full-body strength workout with dumbbells." |
| WORKOUT_LOG | "I just did 3 sets of 10 bench press at 135 lbs and a 20-minute run." |
| FALLBACK | "What's the best recipe for banana bread?" |
| Clarification | "Maybe I want to do something?" *(low-confidence trigger)* |

Each response includes the route taken and confidence score. The full per-call audit trail is available at `GET /audit/{session_id}` using the `session_id` from the chat response.
```

- [ ] Section appended to `.docs/guides/1-multi-agent/README.md`
- [ ] Four subsections present: Key Metrics, Failure Modes, Health Signals, Running the Demo
- [ ] Metrics table has ≥5 rows with target values and measurement methods
- [ ] Failure modes section covers LLM timeout, low-confidence routing, and fuzzy match failures
- [ ] Demo section includes the one-command startup and golden-path prompt table

### 3. Verify markdown renders cleanly  <!-- agent: general-purpose -->

Open `.docs/guides/1-multi-agent/README.md` in a markdown previewer or push to GitHub and verify:
- No unclosed code fences
- Table columns align (GitHub auto-formats, but check locally)
- All hyperlinks in the document are valid (no broken relative paths)

```bash
# Quick lint: check for unclosed triple-backtick fences
python3 -c "
import sys
content = open('.docs/guides/1-multi-agent/README.md').read()
fences = content.count('\`\`\`')
if fences % 2 != 0:
    print('ERROR: odd number of code fences — likely unclosed block')
    sys.exit(1)
print(f'OK: {fences} code fences (all closed)')
"
```

- [ ] README has an even number of code fences (no unclosed blocks)
- [ ] "Production Evaluation" heading appears in the document

## Acceptance Criteria

- [ ] `.docs/guides/1-multi-agent/README.md` contains a `## Production Evaluation` section
- [ ] Key metrics table includes: router latency, routing accuracy, fallback rate, invalid ID rate, token budget
- [ ] Failure modes cover: LLM timeout, low-confidence routing, fuzzy match failure
- [ ] Health signals list is actionable (tells operator what to check, in what order)
- [ ] Demo runbook shows a single startup command and golden-path prompts for all 4 routes
- [ ] No unclosed markdown code fences in the README
