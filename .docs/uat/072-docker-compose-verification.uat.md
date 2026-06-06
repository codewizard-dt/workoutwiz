# UAT: Docker Compose Verification

> **Source task**: [`.docs/tasks/completed/072-docker-compose-verification.md`](../tasks/completed/072-docker-compose-verification.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Docker Desktop (or Docker Engine + Compose plugin) is running
- [ ] No existing containers from this project are running (`docker compose down` if needed)
- [ ] Root `.env` file exists with at least `NEO4J_PASSWORD` and `ANTHROPIC_API_KEY` set (values can be placeholders for infra tests)
- [ ] Working directory is the project root (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz`)

---

## Integration Tests

### UAT-INT-001: Full Stack Starts Clean from Build

- **Components**: PostgreSQL, Neo4j, backend (FastAPI), frontend (Vite)
- **Flow**: `docker compose up --build -d` → all four services reach `Up` status with no `Exit` codes
- **Steps**:
  1. From the project root, run the command below
  2. Wait approximately 90 seconds for Neo4j to initialize (it has a 60s `start_period` in its healthcheck)
  3. Run `docker compose ps` and verify all four services show `Up` or `healthy` — no `Exit` status on any row
- **Command**:
  ```bash
  docker compose up --build -d 2>&1 | tail -20
  ```
- **Expected Result**: Output ends with lines like `Container workout-wiz-backend-1 Started` and `Container workout-wiz-frontend-1 Started`. No `Error` or `failed` lines.
- [ ] Pass

### UAT-INT-002: All Services Healthy (no Exit codes)

- **Components**: All four services
- **Flow**: After UAT-INT-001, verify service table shows no `Exit` state
- **Steps**:
  1. Wait for Neo4j healthcheck to pass (up to 90s after `docker compose up`)
  2. Run the command below
  3. Confirm `STATUS` column shows `Up` or `Up (healthy)` for all rows — no `Exit N` anywhere
- **Command**:
  ```bash
  docker compose ps
  ```
- **Expected Result**: Four rows — `db`, `neo4j`, `backend`, `frontend` — each with `Up` or `Up (healthy)` in the `STATUS` column. Zero rows with `Exit`.
- [ ] Pass

### UAT-INT-003: Backend Health Endpoint Responds

- **Components**: FastAPI backend on port 8000
- **Flow**: After stack is up, `/healthz` returns `{"status": "ok"}`
- **Steps**:
  1. Ensure stack is running (UAT-INT-001 passed)
  2. Run the curl command below
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/healthz'
  ```
- **Expected Result**: `{"status":"ok"}` (HTTP 200)
- [ ] Pass

### UAT-INT-004: Frontend Serves HTML on Host Port

- **Components**: Vite frontend
- **Flow**: After stack is up, frontend serves the React app HTML on the configured host port
- **Steps**:
  1. Ensure stack is running (UAT-INT-001 passed)
  2. Check the host port: `FRONTEND_PORT` in `.env` (default `5173` if set, else `3000` per docker-compose.yml fallback)
  3. Run the curl command below (substituting the correct port if not 5173)
- **Command**:
  ```bash
  curl -sS 'http://localhost:5173' | head -3
  ```
- **Expected Result**: Response starts with `<!doctype html>` — the Vite dev server HTML shell. No connection refused error.
- [ ] Pass

### UAT-INT-005: Neo4j Browser Reachable on HTTP Port 7474

- **Components**: Neo4j service
- **Flow**: Neo4j HTTP interface is reachable on port 7474 (used by the healthcheck)
- **Steps**:
  1. Ensure stack is running (UAT-INT-001 passed) and Neo4j shows `healthy`
  2. Run the curl command below
- **Command**:
  ```bash
  curl -sS 'http://localhost:7474'
  ```
- **Expected Result**: Response is a JSON object containing Neo4j server metadata (e.g. `{"bolt_routing":...}` or `{"data":...}`). HTTP 200. No connection refused.
- [ ] Pass

### UAT-INT-006: Backend Logs Show Clean Startup (no crash)

- **Components**: FastAPI backend lifespan, Alembic migrations
- **Flow**: Backend logs show application startup complete with no tracebacks or fatal errors
- **Steps**:
  1. Ensure stack is running (UAT-INT-001 passed)
  2. Run the command below
- **Command**:
  ```bash
  docker compose logs backend --tail=25
  ```
- **Expected Result**: Logs include `INFO: Application startup complete.` — no `ERROR`, `Traceback`, or `Exception` lines. Uvicorn is running on `0.0.0.0:8000`.
- [ ] Pass

### UAT-INT-007: Stack Stops Cleanly

- **Components**: All four services + network
- **Flow**: `docker compose down` stops and removes all containers and the default network without errors
- **Steps**:
  1. Ensure stack is running (UAT-INT-001 passed)
  2. Run the command below
  3. Confirm output shows each container `Stopped` and `Removed`, and the network removed
- **Command**:
  ```bash
  docker compose down
  ```
- **Expected Result**: Each of the four containers appears with `Stopping` → `Stopped` → `Removing` → `Removed`. The `workout-wiz_default` network is removed. Exit code 0 (no error text).
- [ ] Pass

### UAT-INT-008: Stack Restarts Cleanly (idempotent)

- **Components**: All services
- **Flow**: After `docker compose down`, `docker compose up -d` (without `--build`) starts all services again without errors — verifying volumes and network are properly recreated
- **Steps**:
  1. Ensure UAT-INT-007 passed (stack is down)
  2. Run the command below
  3. Wait ~30s, then run `docker compose ps` to confirm all services are `Up`
  4. Run `docker compose down` to clean up
- **Command**:
  ```bash
  docker compose up -d 2>&1 | tail -10
  ```
- **Expected Result**: Output shows all four services started. `docker compose ps` confirms no `Exit` status. Stack stops cleanly on the final `docker compose down`.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: Backend Does Not Crash if Neo4j is Slow

- **Scenario**: The backend starts (lifespan completes) without establishing a Neo4j connection at startup — Neo4j connection is per-request only
- **Steps**:
  1. Ensure the stack is running and backend logs show `Application startup complete.`
  2. Run the command below to confirm the lifespan does not attempt a Neo4j connection during startup
- **Command**:
  ```bash
  docker compose logs backend --tail=30
  ```
- **Expected Result**: Logs show `Application startup complete.` with no Neo4j connection errors, no `ServiceUnavailable`, and no crash. The backend starts successfully even if Neo4j was still initializing.
- [ ] Pass
