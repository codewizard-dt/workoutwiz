# Multi-Agent System — Take-Home

**Time:** 2–3 hours · **Stack:** Python, LangGraph, LangChain, any LLM provider

Build a hub agent that routes user requests to specialized sub-agents using LangGraph. The router classifies intent with LLM structured output and dispatches to a coach, a workout generator, or a workout logger.

| Route | Example |
|-------|---------|
| `COACH` | "What muscles does a deadlift work?" |
| `WORKOUT_GENERATE` | "Build me a 30 min upper body session with dumbbells" |
| `WORKOUT_LOG` | "I just did 3x10 bench press at 185 lbs" |

## Files

- **[`ASSESSMENT.md`](./ASSESSMENT.md)** — the full prompt: task, requirements, stretch goals
- **[`exercises.json`](./exercises.json)** — the exercise dataset (50 exercises)

## Submitting

Build in a **public** GitHub repo. Include a runnable demo or transcript and a README covering setup. See [`ASSESSMENT.md`](./ASSESSMENT.md) for the complete requirements.

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
