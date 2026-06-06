# UAT: Member Profile Ingestion

> **Source task**: [`.docs/tasks/051-member-profile-ingestion.md`](../tasks/051-member-profile-ingestion.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] PostgreSQL running and accessible (Docker Compose: `docker compose up -d db`)
- [ ] Neo4j running and accessible (Docker Compose: `docker compose up -d neo4j`)
- [ ] Neo4j schema initialized — `init_schema.py` applied the `member_id` uniqueness constraint (`MATCH (m:Member) RETURN count(m)` does not error)
- [ ] Backend Python environment installed (`cd backend && pip install -e .` or `uv sync`)
- [ ] `.env` file present with valid `DATABASE_URL`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- [ ] Working directory is the project root for all commands below

---

## Script Execution Tests

### UAT-SCRIPT-001: Module runs without error (first run)

- **Description**: Verify `python -m app.knowledge_graph.ingest_members` exits cleanly on a fresh Neo4j instance, seeding all 15 Member nodes.
- **Steps**:
  1. Ensure Neo4j is empty of Member nodes (or freshly started).
  2. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m app.knowledge_graph.ingest_members
  ```
- **Expected Result**: Exits with code 0. Logs contain 15 lines of the form `INFO Merged Member: <name> (<email>)` (one per persona), followed by `INFO Ingested 15 Member nodes into Neo4j.`. No Python exceptions or tracebacks.
- [x] Pass <!-- 2026-06-06 -->

### UAT-SCRIPT-002: Module is idempotent — second run does not create duplicate nodes

- **Description**: Verify running the ingestion script twice leaves exactly 15 Member nodes in Neo4j (MERGE semantics, not CREATE).
- **Steps**:
  1. Ensure UAT-SCRIPT-001 has passed (15 nodes already in Neo4j).
  2. Run the same command a second time.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m app.knowledge_graph.ingest_members
  ```
- **Expected Result**: Exits with code 0. Logs again show 15 `Merged Member` lines and the `Ingested 15 Member nodes` summary. The Neo4j node count verified in UAT-CYPHER-001 below remains exactly 15 — not 30.
- [x] Pass <!-- 2026-06-06 -->

---

## Cypher Verification Tests

> These tests query Neo4j directly via `cypher-shell` (available inside the running Neo4j container) or the HTTP API at `http://localhost:7474`. Run after UAT-SCRIPT-001.

### UAT-CYPHER-001: Exactly 15 Member nodes exist after ingestion

- **Description**: Confirm the Neo4j graph contains the expected 15 nodes — one per persona — no more, no less.
- **Steps**:
  1. Ensure UAT-SCRIPT-001 has passed.
  2. Run the command below.
- **Command**:
  ```bash
  docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH (m:Member) RETURN count(m) AS member_count"
  ```
- **Expected Result**: Output contains `member_count: 15` (or `15` in tabular form). No other count is acceptable.
- [x] Pass <!-- 2026-06-06 -->

### UAT-CYPHER-002: All 7 required properties are present on a spot-checked Member node

- **Description**: Verify that every schema-required property (`id`, `email`, `name`, `goals`, `equipment_available`, `sessions_per_week`, `created_at`) is written to a Member node — none are null or missing.
- **Steps**:
  1. Ensure UAT-SCRIPT-001 has passed.
  2. Run the command below (checks the `alex@example.com` persona).
- **Command**:
  ```bash
  docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH (m:Member {email: 'alex@example.com'}) RETURN m.id, m.email, m.name, m.goals, m.equipment_available, m.sessions_per_week, m.created_at"
  ```
- **Expected Result**: A single row is returned. All seven fields are non-null:
  - `m.id` — a UUID string (not empty)
  - `m.email` — `"alex@example.com"`
  - `m.name` — `"Alex Chen"`
  - `m.goals` — a list containing `"muscle_gain"` and `"strength"`
  - `m.equipment_available` — a non-empty list of strings (e.g. includes `"Barbell"`)
  - `m.sessions_per_week` — `4` (integer)
  - `m.created_at` — a non-empty ISO datetime string
- [x] Pass <!-- 2026-06-06 -->

### UAT-CYPHER-003: Member.id matches the PostgreSQL users.id for the same email

- **Description**: Verify cross-store consistency — the `id` stored on the Member node equals the UUID of the corresponding row in the `users` PostgreSQL table. This confirms `member_map` was applied correctly.
- **Steps**:
  1. Ensure UAT-SCRIPT-001 has passed.
  2. Fetch the UUID from PostgreSQL for `alex@example.com`.
  3. Fetch the `id` from Neo4j for the same email.
  4. Compare the two values.
- **Command** (PostgreSQL — run from project root):
  ```bash
  set -a && source .env && set +a && docker compose exec db psql -U postgres -d workoutwiz -c "SELECT id FROM \"user\" WHERE email = 'alex@example.com';"
  ```
- **Command** (Neo4j — run from project root):
  ```bash
  docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH (m:Member {email: 'alex@example.com'}) RETURN m.id"
  ```
- **Expected Result**: Both commands return the same UUID string. The values must match exactly (case-insensitive comparison acceptable for UUIDs).
- [x] Pass <!-- 2026-06-06 -->

### UAT-CYPHER-004: Idempotency confirmed by node count after second run

- **Description**: After UAT-SCRIPT-002's second run, confirm the node count is still exactly 15 — not doubled.
- **Steps**:
  1. Ensure UAT-SCRIPT-002 has passed.
  2. Run the node count query again.
- **Command**:
  ```bash
  docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH (m:Member) RETURN count(m) AS member_count"
  ```
- **Expected Result**: `member_count: 15` — identical to the result from UAT-CYPHER-001.
- [x] Pass <!-- 2026-06-06 -->

### UAT-CYPHER-005: All 15 persona emails are present as Member nodes

- **Description**: Verify each of the 15 synthetic personas has a corresponding Member node — no persona was skipped.
- **Steps**:
  1. Ensure UAT-SCRIPT-001 has passed.
  2. Run the command below.
- **Command**:
  ```bash
  docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH (m:Member) RETURN m.email ORDER BY m.email"
  ```
- **Expected Result**: Exactly 15 rows are returned, one for each of the following emails (order may vary):
  `alex@example.com`, `avery@example.com`, `cameron@example.com`, `casey@example.com`, `devon@example.com`, `drew@example.com`, `jordan@example.com`, `morgan@example.com`, `parker@example.com`, `quinn@example.com`, `reese@example.com`, `riley@example.com`, `sam@example.com`, `skyler@example.com`, `taylor@example.com`.
- [x] Pass <!-- 2026-06-06 -->

---

## Module Structure / Import Tests

### UAT-IMPORT-001: `ingest_members` is importable and callable

- **Description**: Verify the module has no import errors and the public function is accessible.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.knowledge_graph.ingest_members import ingest_members; print('OK:', ingest_members)"
  ```
- **Expected Result**: Prints `OK: <function ingest_members at 0x...>` with no ImportError, ModuleNotFoundError, or traceback.
- [x] Pass <!-- 2026-06-06 -->

### UAT-IMPORT-002: No circular import between `ingest_members.py` and `seed.py`

- **Description**: Confirm that importing `seed.py` does not raise a circular-import error (seed imports ingest_members inside a function body; ingest_members imports PERSONAS from seed at module level).
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.knowledge_graph.seed import seed_members_neo4j; print('OK:', seed_members_neo4j)"
  ```
- **Expected Result**: Prints `OK: <function seed_members_neo4j at 0x...>` with no ImportError or circular-import traceback.
- [x] Pass <!-- 2026-06-06 -->

### UAT-IMPORT-003: `seed_members_neo4j` in `seed.py` delegates to `ingest_members` — no duplicated Cypher

- **Description**: Verify that `seed_members_neo4j` contains no standalone Cypher — it must delegate entirely to `ingest_members()`.
- **Steps**:
  1. Run the command below from the project root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "import inspect; from app.knowledge_graph.seed import seed_members_neo4j; src = inspect.getsource(seed_members_neo4j); assert 'MERGE' not in src, 'Duplicate Cypher found in seed_members_neo4j'; assert '_ingest_members' in src or 'ingest_members' in src, 'Delegation call not found'; print('OK: delegation confirmed, no duplicate Cypher')"
  ```
- **Expected Result**: Prints `OK: delegation confirmed, no duplicate Cypher`. If `MERGE` appears in `seed_members_neo4j`'s source, the assertion fails, indicating duplicated logic.
- [x] Pass <!-- 2026-06-06 -->

---

## Logging Tests

### UAT-LOG-001: INFO log emitted for each merged Member

- **Description**: Verify the module logs `Merged Member: <name> (<email>)` exactly once per persona at INFO level.
- **Steps**:
  1. Run the ingestion command and capture stdout/stderr.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m app.knowledge_graph.ingest_members 2>&1 | grep -c "Merged Member:"
  ```
- **Expected Result**: Prints `15` — one `Merged Member:` log line per persona.
- [x] Pass <!-- 2026-06-06 -->

### UAT-LOG-002: Final count log emitted after ingestion

- **Description**: Verify the module logs `Ingested 15 Member nodes into Neo4j.` after completing the loop.
- **Steps**:
  1. Run the ingestion command and capture output.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m app.knowledge_graph.ingest_members 2>&1 | grep "Ingested"
  ```
- **Expected Result**: Output contains exactly one line matching `Ingested 15 Member nodes into Neo4j.`.
- [x] Pass <!-- 2026-06-06 -->
