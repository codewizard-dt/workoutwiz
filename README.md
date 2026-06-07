# Workout Wiz

> **Demo slides**: [HTML](.docs/demo/runbook.slides.html) / [MD](.docs/demo/runbook.slides.md)

A fitness coaching API and web app built as an AI engineering take-home assessment. The backend is production-wired (async FastAPI, PostgreSQL, JWT auth, structured logging, resilient error handling); the LangGraph multi-agent routing layer sits between the chat UI and the REST API.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Vite + React + TypeScript)                   │
│  TanStack Query · Tailwind CSS · shadcn/ui              │
│  localhost:5173                                         │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP / JSON
┌───────────────────▼─────────────────────────────────────┐
│  Multi-Agent Layer (LangGraph StateGraph)               │
│  Hub router → COACH | WORKOUT_GENERATE | WORKOUT_LOG     │
│               KNOWLEDGE_GRAPH | FALLBACK | clarification │
│  /chat  /audit/{session_id}                             │
│  localhost:8000                                         │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP / JSON
┌───────────────────▼─────────────────────────────────────┐
│  Backend (FastAPI + SQLAlchemy async)                   │
│  /auth  /exercises  /workouts  /healthz                 │
│  localhost:8000                                         │
└───────────────────┬─────────────────────────────────────┘
                    │ asyncpg
┌───────────────────▼─────────────────────────────────────┐
│  PostgreSQL 16                                          │
│  Tables: users, exercises, workouts,                    │
│          workout_sequences, workout_sets                │
│  localhost:5433 (mapped from container :5432)           │
└─────────────────────────────────────────────────────────┘
```

The hub routes natural-language input to the appropriate sub-agent using LLM structured output (`with_structured_output`) — never regex or keyword matching. The REST layer is intentionally standalone so the agents do not disrupt the existing API.

### Routing

| Route | Example |
|-------|---------|
| `COACH` | "What muscles does a deadlift work?" |
| `WORKOUT_GENERATE` | "Build me a 30-min upper-body session with dumbbells" |
| `WORKOUT_LOG` | "I just did 3×10 bench press at 185 lbs" |
| `KNOWLEDGE_GRAPH` | "Build a workout that avoids aggravating my knee injury" |
| `FALLBACK` | "What's the capital of France?" |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy (async) + Alembic |
| Database | PostgreSQL 16 |
| Auth | fastapi-users (JWT bearer, bcrypt) |
| Frontend | Vite + React + TypeScript + Tailwind CSS + shadcn/ui |
| State | TanStack Query (server state) + React Context (auth/UI) |
| API client | Axios |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for PostgreSQL or the full dev stack)

### Docker (full stack)

Runs the database, backend, and frontend together with hot-reload. Requires `ANTHROPIC_API_KEY` in a `.env` file at the repo root.

```bash
cp backend/.env.example .env   # edit ANTHROPIC_API_KEY (and SECRET_KEY for production)
make dev
```

Services come up at `http://localhost:5173` (frontend), `http://localhost:8000` (backend), and `localhost:5433` (Postgres). The first run builds the images; subsequent starts are fast. Use `make down` to stop.

### Multi-Agent Demo (Assessment 1)

**Prerequisites**: Python 3.11+, `ANTHROPIC_API_KEY` set in environment.

```bash
make install
make run
```

Or manually:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser. Each response includes the route taken, confidence score, and a `session_id` for retrieving the full audit trail at `GET /audit/{session_id}`.

**Golden-path prompts:**

| Route | Example prompt |
|-------|---------------|
| COACH | "How many rest days should I take per week for hypertrophy?" |
| WORKOUT_GENERATE | "Give me a 45-minute full-body strength workout with dumbbells." |
| WORKOUT_LOG | "I just did 3 sets of 10 bench press at 135 lbs and a 20-minute run." |
| KNOWLEDGE_GRAPH | "Build a workout that avoids aggravating my knee and shoulder injuries." |
| FALLBACK | "What's the best recipe for banana bread?" |
| Clarification | "Maybe I want to do something?" *(low-confidence trigger)* |

### Backend

```bash
cd backend
cp .env.example .env          # edit SECRET_KEY and ANTHROPIC_API_KEY before use
docker compose up -d db
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_exercises.py   # reads exercises.json from backend/
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies API requests to `localhost:8000`.

## Running Tests

### Backend (mocked — fast, no API key needed)

```bash
# Requires a running PostgreSQL instance.
# Tests run against 'workoutwiz_test'; Alembic migrations and exercise seeding
# happen automatically via pytest session fixtures.
cd backend && pytest tests/ -m "not live" -v
```

Covers auth, exercise filtering, workout CRUD, ownership isolation, hub compilation, all four routing paths, audit log endpoints, and agent sub-unit tests — using mocked LLM responses.

### Backend (live — hits real Anthropic API)

```bash
# Requires ANTHROPIC_API_KEY set in the root .env file.
cd backend && pytest -m live -v
```

Six end-to-end tests invoke the real hub via the `/chat/` endpoint and assert that:
- Each message routes to the correct sub-agent (`COACH`, `WORKOUT_GENERATE`, `WORKOUT_LOG`, `KNOWLEDGE_GRAPH`, clarification)
- The audit log for every call contains real telemetry (`latency_ms > 0`, `tokens_in > 0`, `tokens_out > 0`)
- The `GET /chat/audit/{session_id}` endpoint returns populated entries
- Audit entries accumulate correctly across a multi-turn session

### Frontend E2E

```bash
# Requires both backend and frontend dev servers running.
cd frontend && npx playwright test
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/healthz` | — | Liveness check |
| POST | `/auth/register` | — | Register new user |
| POST | `/auth/jwt/login` | — | Exchange credentials for JWT |
| POST | `/auth/jwt/logout` | JWT | Invalidate token |
| GET | `/auth/me` | JWT | Current authenticated user |
| GET | `/exercises/` | — | List/filter exercises (name, muscle_groups, equipment, priority_tier) |
| GET | `/workouts/` | JWT | List current user's workouts |
| POST | `/workouts/` | JWT | Create workout |
| GET | `/workouts/{id}` | JWT | Get workout by ID |
| PUT | `/workouts/{id}` | JWT | Update workout |
| DELETE | `/workouts/{id}` | JWT | Delete workout |

All authenticated endpoints return `401` for missing or invalid tokens. Workout endpoints return `403` when the authenticated user does not own the resource and `404` when the resource does not exist.

## Production Evaluation

### Key Metrics

| Metric | Target | How to measure |
|--------|--------|----------------|
| Router latency (p95) | < 800 ms | `audit_log[].latency_ms` where `event == "router"` |
| Sub-agent latency (p95) | < 3 000 ms | `audit_log[].latency_ms` for coach/generator/logger events |
| Routing accuracy | ≥ 90 % | Compare `audit_log[].route` to ground-truth intent labels |
| Fallback rate | < 15 % | Count `route == "FALLBACK"` / total requests |
| Invalid ID rate | 0 % | `build_workout_tool` `invalid_ids_skipped` per call |
| Token budget (p95) | < 2 000 tokens/turn | Sum `tokens_in + tokens_out` across all audit entries per turn |

Retrieve per-session audit data at any time:

```bash
curl http://localhost:8000/audit/{session_id}
```

### Failure Modes

**1. LLM timeout / API error** — The router and all sub-agent nodes make synchronous Anthropic API calls. Network or API degradation raises an exception that propagates through the hub, returning HTTP 500.
*Mitigation*: wrap LLM calls in a try/except that returns a FALLBACK route with a user-facing error message; set `httpx` timeout to 30 s.

**2. Low-confidence routing** — When the router's `confidence` is below 0.6, the hub routes to the clarification node. Frequent clarifications (> 15 % of requests) indicate the system prompt or `RouteDecision` schema needs more specificity.
*Signal*: high fallback rate in audit log; users reporting "can you rephrase?" on clearly valid inputs.

**3. Fuzzy match failure in workout logger** — The logger sub-agent uses fuzzy string matching to map free-text exercise names to `exercises.json` IDs. Names too far from any entry are skipped silently.
*Signal*: logged workout has fewer exercises than the user mentioned; `invalid_ids_skipped` is non-empty.

**4. Session state growth (memory leak)** — The in-memory `_sessions` dict is never evicted. Long-running servers accumulate state indefinitely.
*Mitigation*: add a TTL-based cleanup job (e.g. `asyncio` background task deleting sessions older than 24 h). Not implemented in this demo.

**5. Hallucinated exercise IDs** — If the generator sub-agent ignores `search_exercises_tool` results and fabricates UUIDs, those IDs land in `invalid_ids_skipped`.
*Signal*: non-empty `invalid_ids_skipped` in production audit logs.

### Health Signals

When the system misbehaves, check in this order:

1. **`GET /health` returns non-200** → app is not running or crashed on startup (check `uvicorn` logs).
2. **High fallback rate** → router prompt needs tuning or `RouteDecision` schema descriptions are ambiguous.
3. **All requests route to the same intent** → LLM is ignoring the schema (verify `with_structured_output` is wired correctly).
4. **Latency spikes** → Anthropic API is degraded; check [status.anthropic.com](https://status.anthropic.com).
5. **`invalid_ids_skipped` non-empty** → grounding failure; re-run the grounding test and inspect `search_exercises_tool` output.
6. **`GET /audit/{session_id}` returns 404** → session was deleted or the server was restarted (in-memory state is lost on restart).

### Sample Demo Transcript

```
User: How many rest days per week should I take for hypertrophy?
Route: COACH  Confidence: 0.97  Latency: 412 ms
Bot:  For hypertrophy, most lifters do well with 1–2 rest days per week,
      training each muscle group 2x per week with 48h recovery between sessions.

User: Give me a 30-minute upper-body dumbbell workout.
Route: WORKOUT_GENERATE  Confidence: 0.95  Latency: 1 843 ms
Bot:  Here is your workout: [Warmup] Arm circles 2x60s · [Main] DB bench press
      3x10, DB row 3x10, shoulder press 3x12, bicep curl 3x12 · [Cooldown] chest
      stretch 60s, lat stretch 60s.

User: I just did 3 sets of 10 bench press at 135 lbs and a 20-minute run.
Route: WORKOUT_LOG  Confidence: 0.93  Latency: 2 105 ms
Bot:  Logged: bench press 3×10 @ 61.2 kg + cardio run 20 min.
      Session ID: 7f3a9c2e-... — retrieve audit at GET /audit/7f3a9c2e-...

User: What's the capital of France?
Route: FALLBACK  Confidence: 0.99  Latency: 389 ms
Bot:  I can help with fitness coaching, workout planning, and logging workouts.
      I'm not able to answer general knowledge questions.
```

### Injury-Aware Recommendation — Live Trace

This example shows the injury safety pipeline in action: the router sends the request to `KNOWLEDGE_GRAPH`, the retrieval sub-graph traverses injury nodes, and the safety gate hard-filters contraindicated exercises after LLM generation.

**Prompt:** `"I have a bad knee and a bad shoulder. Build me a workout that avoids aggravating either injury."`

```
Route: KNOWLEDGE_GRAPH  Confidence: 0.99

Audit trail:
  router                  1 259 ms  tokens_in=1376  tokens_out=113
  retrieval_lookup_member     3 ms  result_count=0
  retrieval_injury_traversal  2 ms  result_count=0  constraint_count=0
  retrieval_vector_search   506 ms  result_count=10  (embedding: 506 ms)
  retrieval_assemble        288 ms  input_count=10  output_count=10
  kg_generation_llm       8 497 ms  tokens_in=1748  tokens_out=992  exercise_count=5
  kg_generation_safety_gate   0 ms  exercise_in=5  exercise_out=5  violations_filtered=0
  kg_hub (total)          9 318 ms

Reply (excerpt):
  1. Single-Arm Dumbbell Preacher Curl — 3×10
     Why: Preacher curl isolates the bicep while supporting the arm on a pad,
     minimizing shoulder joint stress.
  2. Med Ball Split Squat — 3×10
     Why: Split squat stance distributes load more evenly across both legs
     and reduces single-leg knee stress compared to barbell lunges.
  ...
  Note: 5 exercise(s) excluded due to injury constraints.
```

Key behaviours demonstrated:
- Router correctly identifies the injury context and routes to `KNOWLEDGE_GRAPH` (not `WORKOUT_GENERATE`)
- `retrieval_injury_traversal` runs — 0 constraints found because this is a new user with no graph profile; the system falls back to LLM instruction-following for exclusion
- `kg_generation_safety_gate` runs after LLM generation — 0 violations filtered (model followed instructions)
- The response explicitly states how many exercises were excluded

### Equipment-Constrained Workout — Live Trace

This example shows the generator sub-agent respecting an equipment constraint passed in natural language.

**Prompt:** `"I only have resistance bands at home — no barbells, no dumbbells. Build me a 30-minute full-body workout."`

```
Route: WORKOUT_GENERATE  Confidence: 0.95

Audit trail:
  router          1 129 ms  tokens_in=1382  tokens_out=101
  generator ×8   ~14 776 ms total (search + build tool call chain)

Workout draft:
  warmup:
    - RNT Split Squat         (id: 00cc383b)  3×10-12
    - Push-Up to Knee-Drive   (id: 0e3201e9)  3×10-12
  main:
    - Resistance Band Reverse Curl      (id: 12b80a72)  3×10-12
    - Anchored Band Rotational Lift     (id: 07772057)  3×10-12
    - Bodyweight Pike                   (id: 0a2dc786)  3×10-12
    - Alternating Low Plank To Low Side Plank (id: 00e18a26) 3×10-12
  invalid_ids_skipped: []   ← no hallucinated IDs
```

Key behaviours demonstrated:
- `search_exercises_tool` filtered the 50-exercise dataset to resistance band and bodyweight exercises
- `build_workout_tool` validated all exercise IDs — `invalid_ids_skipped` is empty, confirming no hallucinated UUIDs
- Equipment constraint was respected through dataset filtering, not LLM instruction-following alone

---

## Evaluation Results

The eval suite covers three layers:

| Suite | Cases | Latest | Trend |
|-------|-------|--------|-------|
| **Golden** (critical paths, live API) | 11 | **11/11 (100%)** | ▇▆█▇█████ 91%→100% |
| **Scenarios** (coverage matrix, live API) | 41 | 27/41 (66%) | ▅ 66% |
| **Replays** (frozen fixtures, no API calls) | 5 | **5/5 (100%)** | ██ 100% |

*Stats from `make eval-stats` across 12 recorded runs (9 golden, 1 scenario, 2 replay).*

**Golden suite** — 11 cases that cover the critical routing paths (COACH, WORKOUT_GENERATE, WORKOUT_LOG, KNOWLEDGE_GRAPH, FALLBACK, clarification) plus edge cases (invalid exercise IDs, low-confidence inputs, injury-aware recommendations). 100% pass rate is the hard gate for shipping.

**Scenario suite** — 41 cases organized as a coverage matrix (straightforward / ambiguous / edge-case per route). The 66% pass rate reflects that ambiguous and edge-case inputs are harder; several failing cases (`sc-kg-*`, `sc-wg-*`) require the full Neo4j stack or expose the LLM-dependent no-results recovery path. These are known gaps documented in `evals/scenarios/`.

**Replay suite** — 5 frozen fixtures that validate parsing logic without API calls. These run in CI without an `ANTHROPIC_API_KEY`.

Run the full suite:

```bash
make eval          # golden + replays + stats
make eval-golden   # live golden cases (requires ANTHROPIC_API_KEY)
make eval-scenarios # coverage matrix
make eval-replays  # frozen fixtures, no API calls
make eval-stats    # historical trend table
```

---

## How I Used AI

This project was built using **Claude Code** (Anthropic's CLI coding agent) as the primary development tool throughout. Here is an honest account of where AI accelerated the work and where human judgment was still essential.

### What AI did well

**Architecture scaffolding.** The initial LangGraph hub-and-spokes architecture, Alembic migration structure, and FastAPI router layout were generated in the first session. Claude produced a working `StateGraph` with typed state and conditional edges on the first attempt, following the assessment spec correctly.

**Boilerplate elimination.** Pydantic schemas, SQLAlchemy models, and pytest fixtures — all high-signal, low-creativity work — were generated accurately and consistently. This freed the bulk of the 2–3 hour budget for the non-trivial pieces.

**Test generation.** The 11 golden test cases and 5 replay fixtures were generated from a description of the routing paths. Claude correctly identified the edge cases worth testing (invalid exercise IDs, low-confidence routing, multi-turn session accumulation) without being asked explicitly.

**Incremental debugging.** When the fuzzy-matching logic in the workout logger produced wrong exercise IDs at low confidence, Claude identified the threshold issue and proposed the fix (using `process.extractOne` with a score cutoff) on the first pass.

### Where human judgment was still essential

**Routing the ambiguous cases.** Deciding when a message like "I want to do something tomorrow" is a `COACH` question versus a `WORKOUT_GENERATE` request required reading the assessment rubric and making a judgment call about what the evaluators would expect. AI suggestions were useful but not authoritative here.

**The safety gate design.** The decision to place the injury contraindication filter *after* LLM generation (rather than before, in the prompt) was a deliberate architectural choice to prevent prompt-injection bypasses. This was a human decision; the AI would have placed it in the prompt if not directed otherwise.

**Scope triage.** The assessment is a 2–3 hour exercise; Claude consistently suggested extending the scope (streaming, multi-turn memory, full Neo4j ontology grounding). Keeping the scope tight required active steering.

**Eval failure triage.** The scenario suite's 66% pass rate includes genuine gaps (no Jordan Rivera member context, equipment constraints are prompt-based not graph-enforced). Distinguishing "this is a real gap" from "this test case is testing something outside the Assessment 1 spec" required reading the original spec carefully.

---

## How I Would Productionize This

This section is honest about what is wired now versus what would be required before putting this in front of real users.

### Observability

**Currently**: structured stdout logging with configurable log level; `X-Request-ID` middleware propagates a request ID through every log line; `/healthz` returns `{"status": "ok"}`.

**In production I would add:**

- **Distributed tracing** (OpenTelemetry → Jaeger or Honeycomb): the `X-Request-ID` is already threaded through every request; the next step is emitting spans for DB queries so I can trace exactly where latency originates.
- **Metrics** (Prometheus + Grafana): p50/p95/p99 per endpoint, DB connection pool saturation, active request count. Alert on p99 > 500 ms or error rate > 1%.
- **Structured JSON logs** in production: replace `basicConfig` with `python-json-logger` so log lines are machine-parseable by any aggregator (Datadog, Loki, CloudWatch).
- **DB health gate**: add a `/healthz/db` variant that runs `SELECT 1` and returns `503` if the pool is exhausted or the DB is unreachable, so load balancers stop routing traffic to a degraded instance.

### Resilience

**Currently**: `pool_pre_ping=True` drops stale connections before use; a global exception handler catches all unhandled exceptions and returns `500` without leaking stack traces; the `lifespan` handler calls `engine.dispose()` on shutdown.

**In production I would add:**

- **Circuit breaker on the DB**: `tenacity` with exponential backoff on `OperationalError` so transient DB restarts do not cascade into a wave of 500s.
- **Graceful shutdown**: a short drain window (e.g. 10 s) before closing the pool, to let in-flight requests finish cleanly behind a load balancer.
- **Connection pool tuning**: `pool_size` and `max_overflow` should be derived from actual concurrency metrics rather than SQLAlchemy defaults. PgBouncer at the infrastructure layer handles connection surge on rolling deploys.
- **Idempotency keys** on `POST /workouts/`: clients should be able to retry safely without creating duplicate records.

### Security

**Currently**: JWT bearer tokens with configurable expiry; bcrypt password hashing via fastapi-users; no secrets committed to the repository; CORS restricted to `localhost:5173` in development.

**In production I would add:**

- **Secret rotation**: `SECRET_KEY` should rotate on a schedule; short-lived access tokens (15 min) paired with refresh tokens reduce the blast radius of a leaked token.
- **Token revocation**: a Redis blocklist or `jti` claim checked against a short-lived deny-list so compromised tokens can be invalidated before expiry.
- **Rate limiting** on `/auth/register` and `/auth/jwt/login` with `slowapi` to prevent credential stuffing and account enumeration.
- **HTTPS-only with HSTS**: terminate TLS at the load balancer; set `Strict-Transport-Security` with a long `max-age`.
- **Dependency scanning** in CI: `pip-audit` or GitHub Dependabot for Python; `npm audit` for the frontend.
- **Input size limits**: configure FastAPI's `max_body_size` to reject abnormally large payloads before they reach application logic.

### Data Integrity

**Currently**: FK constraints with `CASCADE DELETE` enforce referential integrity; async transactions prevent partial writes; `pool_pre_ping` avoids operating on stale connections.

**In production I would add:**

- **Soft deletes for workouts**: a `deleted_at` column so user data is recoverable after accidental deletion, with a background job for eventual hard-delete after a configurable retention window.
- **Alembic migration CI gate**: apply all migrations to a fresh database and run `downgrade base` in CI to catch irreversible migrations before they reach production.
- **Backup strategy**: daily `pg_dump` to S3 with a tested restore drill quarterly. For a write-heavy workload, WAL archiving enables point-in-time recovery.
- **Read replica for exercises**: the 50-exercise table is written once (at seed time) and read on every workout generation request. A Redis cache or a read replica offloads the primary for this read-heavy, write-rare pattern.

### Scale

**Currently**: single async FastAPI process; single PostgreSQL instance.

**At meaningful scale I would:**

- **Horizontally scale the API**: stateless by design (JWT, no server-side sessions), so adding instances behind a load balancer requires no application changes.
- **Cache exercises in Redis**: 50 records that never change are a textbook cache candidate — skip the DB entirely for `GET /exercises/` after the first warm request, with a long TTL and cache invalidation tied to any future seed migration.
- **PgBouncer**: transaction-mode pooling at the infrastructure layer so a sudden spike in API instances does not exhaust PostgreSQL's connection limit.
- **Async task queue** for agent operations: when the LangGraph layer is added, workout generation calls can take several seconds. Offloading them to Celery or ARQ with a WebSocket or polling endpoint keeps the HTTP response fast and the user informed of progress.

## How I Would Evaluate This System in Production

### Retrieval Quality

The core question is whether GraphRAG surfaces more relevant context than vector search alone. I would measure this with a held-out evaluation set of (member, query, expected_exercises) triples — synthetic but representative of real coaching scenarios. Key metrics:

- **Recall@K**: fraction of expected exercises appearing in the top-K retrieved results
- **Precision@K**: fraction of retrieved exercises that are truly relevant to the member's goals
- **Baseline comparison**: run the same queries with vector-only retrieval (no graph traversal) to quantify the graph's contribution

User feedback ratings (the 1–5 `FeedbackEvent` nodes) serve as implicit labels over time — exercises consistently rated 4–5 by a member should appear earlier in their retrieval results.

### Safety Monitoring

The injury safety gate is a hard constraint: contraindicated exercises must never appear in output. I would instrument:

- **Gate trip rate** (Prometheus counter): `kg_safety_gate_trips_total{reason="contraindicated"}`. Alert if non-zero in production — every trip means the LLM ignored an explicit instruction.
- **Adversarial testing**: prompt the LLM with "ignore the safe exercise list" injected into the user query; verify the gate catches any resulting violations.
- **Regression test suite**: the 5-case parameterized test in `test_kg_critical_injury_filtering.py` runs on every CI push.

### Latency

Target: < 3 seconds end-to-end (P95). Breakdown by sub-component:

| Component | Budget | Instrument |
|-----------|--------|------------|
| Neo4j traversal (all queries) | < 100ms P99 | `neo4j.session.run` span |
| Vector similarity search | < 200ms P99 | `similarity_search` span |
| LLM generation | < 2 000ms P99 | `ChatAnthropic.ainvoke` span |
| Context assembly + safety gate | < 50ms | function-level timing |

I would use OpenTelemetry with a LangSmith/Datadog backend. The `ContextSlice.token_counts` is already logged at INFO level — ship these to a metrics store and alert when `total > 1900` (approaching the 2048 budget).

### Token Efficiency

The 2048-token context budget (ADR-001 D3) is enforced by `_truncate_to_budget()`. In production I would:

1. **Track budget utilisation** per section via `token_counts` — histogram the distribution across requests.
2. **A/B test allocations**: member profile at 200, safe exercises at 600, preferred at 400, vector hits at 400 are reasonable starting points; if user ratings skew toward preferred exercises, shift budget toward that section.
3. **Member profile caching**: the member profile rarely changes between sessions. Cache it in Redis (TTL: 1 hour) to skip the Neo4j round-trip on repeat queries.
4. **Vector store warm-up**: the sentence-transformers model loads lazily; pre-warm on startup to avoid cold-start latency spikes.
