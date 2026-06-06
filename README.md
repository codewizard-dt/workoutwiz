# Workout Wiz

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
│  Hub router → COACH | WORKOUT_GENERATE | WORKOUT_LOG    │
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
- Each message routes to the correct sub-agent (`COACH`, `WORKOUT_GENERATE`, `WORKOUT_LOG`, clarification)
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
