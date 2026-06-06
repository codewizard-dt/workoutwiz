# 072 — Docker Compose Verification: Full Stack Starts Clean

> **Depends on**: [065-kg-fastapi-router](completed/065-kg-fastapi-router.md)
> **Blocks**: none
> **Parallel-safe with**: [070-kg-chat-dashboard](070-kg-chat-dashboard.md), [071-feedback-submission-ui](071-feedback-submission-ui.md), [073-readme-production-eval](073-readme-production-eval.md)

## Objective

Verify that `docker compose up` starts the full stack (PostgreSQL, Neo4j, backend, frontend) and that all services become healthy. Fix any startup issues. The final state must be a stack that starts clean from `docker compose up --build` with no manual intervention.

## Approach

1. Check `docker-compose.yml` for Neo4j service configuration.
2. Ensure the backend's startup sequence works with Neo4j (connection not required for startup — just log a warning if unavailable).
3. Ensure health checks are correctly configured.
4. Fix any issues found.

## Steps

### 1. Read `docker-compose.yml`  <!-- agent: general-purpose -->

Use the `Read` tool on `docker-compose.yml`. Confirm:
- Neo4j service is defined with correct port mappings (7474, 7687)
- Backend depends_on: neo4j, postgres
- Health check conditions are correct
- Environment variables for Neo4j connection match `Settings` defaults

- [ ] `docker-compose.yml` reviewed; issues identified

### 2. Check backend startup for Neo4j dependency  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/main.py`. Confirm the lifespan function handles Neo4j connection failure gracefully (log warning, don't crash). The backend should start even if Neo4j is not yet ready.

Fix `main.py` if it crashes on Neo4j startup failure.

- [ ] Backend starts without crashing if Neo4j is slow to start

### 3. Run the stack  <!-- agent: general-purpose -->

```bash
docker compose up --build -d 2>&1 | tail -30
sleep 20
docker compose ps
docker compose logs backend --tail=20
```

Check that all services show `Up` or `healthy`.

- [ ] All services start (`docker compose ps` shows no `Exit` status)

### 4. Verify key endpoints  <!-- agent: general-purpose -->

```bash
curl -s http://localhost:8000/health || curl -s http://localhost:8000/ || curl -s http://localhost:8000/docs
curl -s http://localhost:3000 | head -5
```

- [ ] Backend responds on port 8000
- [ ] Frontend serves on port 3000

### 5. Stop the stack  <!-- agent: general-purpose -->

```bash
docker compose down
```

- [ ] Stack stops cleanly

### 6. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 7 Docker Compose placeholder.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `docker compose up --build` starts all services with no Exit codes
- [ ] Backend healthcheck passes
- [ ] Neo4j service reachable on bolt://localhost:7687
- [ ] Frontend serves on port 3000
- [ ] `docker compose down` stops cleanly

---
**UAT**: `.docs/uat/072-docker-compose-verification.uat.md`
