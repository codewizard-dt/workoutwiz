# 018 — Add "How I Would Evaluate This in Production" README Section

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [015-e2e-tests](015-e2e-tests.md), [016-edge-case-testing](016-edge-case-testing.md), [017-performance-baseline](017-performance-baseline.md)

## Objective

Create a production-ready `README.md` at the project root and add the "How I Would Evaluate This in Production" section required by PRD-001 AC-3. The README should be portfolio-quality: clear setup instructions, architecture overview, and honest engineering evaluation.

## Approach

- Top-level `README.md` (not inside `backend/` or `frontend/`) covering the full project
- "How I Would Evaluate This in Production" section addressing: observability, resilience, scale, security, and data integrity
- Honest about what's dev-only vs. production-ready

## Steps

### 1. Write full project README  <!-- agent: general-purpose -->

Create `/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md` with the following structure:

```markdown
# Workout Wiz

A fitness coaching API and web app built as an AI engineering take-home assessment.

## Architecture

[brief description of FastAPI backend + PostgreSQL + Vite/React/TS frontend + LangGraph multi-agent layer (future)]

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy async + Alembic |
| Database | PostgreSQL 16 |
| Auth | fastapi-users (JWT) |
| Frontend | Vite + React + TypeScript + Tailwind CSS + shadcn/ui |
| State | TanStack Query + React Context |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (for PostgreSQL)

### Backend

\`\`\`bash
cd backend
cp .env.example .env
docker compose up -d db
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_exercises.py
uvicorn app.main:app --reload
\`\`\`

### Frontend

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

## Running Tests

\`\`\`bash
# Backend integration tests (requires workoutwiz_test database)
cd backend && pytest tests/ -v

# Frontend E2E tests (requires both servers running)
cd frontend && npx playwright test
\`\`\`

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | — | Register new user |
| POST | /auth/jwt/login | — | Get JWT token |
| GET | /auth/me | ✓ | Current user |
| GET | /exercises/ | — | List/search exercises |
| GET | /workouts/ | ✓ | User's workouts |
| POST | /workouts/ | ✓ | Create workout |
| GET | /workouts/{id} | ✓ | Get workout |
| PUT | /workouts/{id} | ✓ | Update workout |
| DELETE | /workouts/{id} | ✓ | Delete workout |

## How I Would Evaluate This in Production

### Observability

Currently: structured stdout logging with request IDs, `/healthz` and `/healthz/db` endpoints.

In production I would add:
- **Distributed tracing** (OpenTelemetry → Jaeger/Honeycomb) — the `X-Request-ID` middleware already propagates an ID; the next step is emitting spans for DB queries
- **Metrics** (Prometheus + Grafana): p50/p95/p99 for all endpoints, DB pool saturation, cache hit rate
- **Alerting**: PagerDuty on p99 > 500ms or error rate > 1%
- **Structured JSON logs** in production (replace `basicConfig` with `python-json-logger`)

### Resilience

Currently: `pool_pre_ping=True` drops stale connections; global exception handler returns 500 without leaking stack traces.

In production I would add:
- **Circuit breaker** on the DB connection (e.g., `tenacity` with exponential backoff on `OperationalError`)
- **Graceful shutdown**: drain in-flight requests before closing the DB pool (the lifespan handler already calls `engine.dispose()`)
- **Connection pool sizing**: tune `pool_size` and `max_overflow` based on actual concurrency metrics
- **Health check gate**: return 503 (not 200) from `/healthz/db` if the DB is unreachable, so load balancers stop routing to the instance

### Security

Currently: JWT bearer tokens, bcrypt passwords (via fastapi-users), no secrets in code.

In production I would add:
- **Rotate `SECRET_KEY`** on a schedule; implement token revocation (Redis blocklist or short-lived tokens)
- **Rate limiting** on `/auth/register` and `/auth/jwt/login` (e.g., `slowapi`)
- **HTTPS-only** with HSTS header
- **Input size limits** on request bodies (FastAPI's `max_body_size`)
- **Dependency scanning** in CI (GitHub Dependabot or `pip-audit`)

### Data Integrity

Currently: FK constraints with CASCADE delete, async transactions, `pool_pre_ping`.

In production I would add:
- **Alembic migration tests** in CI: apply all migrations to a fresh DB and downgrade, assert no data loss
- **Soft deletes** for workouts (add `deleted_at` column) so user data is recoverable
- **Backup strategy**: daily pg_dump to S3 with restore drill quarterly
- **Read replicas** for exercise queries (read-heavy, write-rare) to reduce load on primary

### Scale

Currently: single async FastAPI process, single PostgreSQL instance.

At meaningful scale I would:
- **Horizontally scale** the API behind a load balancer (stateless by design — JWTs, no server-side sessions)
- **Cache exercises** in Redis (50 records, rarely change) — skip the DB entirely for `GET /exercises/`
- **Connection pooling at the infrastructure layer**: PgBouncer between FastAPI and PostgreSQL to handle connection surge on deploy
```

- [x] Root-level `README.md` created covering setup, architecture, API reference, and production evaluation
- [x] "How I Would Evaluate This in Production" section covers: observability, resilience, security, data integrity, scale
- [x] Setup instructions are accurate and tested

## Acceptance Criteria

- [x] `README.md` exists at project root (not inside `backend/` or `frontend/`)
- [x] Quick Start section has working commands for both backend and frontend
- [x] "How I Would Evaluate This in Production" section present with at least 5 distinct dimensions
- [x] API endpoint table matches actual implemented routes
- [x] Document is portfolio-quality (clear prose, accurate technical details)
