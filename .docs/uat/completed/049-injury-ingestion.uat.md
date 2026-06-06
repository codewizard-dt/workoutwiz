# UAT: Injury Ingestion — Injury Nodes, HAS_INJURY, and CONTRAINDICATED_BY Edges

> **Source task**: [`.docs/tasks/049-injury-ingestion.md`](../tasks/049-injury-ingestion.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Docker is running: `docker compose up -d neo4j db`
- [ ] Both the `neo4j` and `db` services pass their healthchecks (`docker compose ps` shows "healthy")
- [ ] `.env` file is populated with `NEO4J_PASSWORD`, `DATABASE_URL`, and `SECRET_KEY` (see `.env.example`)
- [ ] Neo4j schema constraints/indexes already initialised (TASK-044). If not, run: `cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.init_schema`
- [ ] Member nodes already exist in Neo4j (seeded via `ingest_members`). If not, run the full seed pipeline via `seed_loader.py` instead of the standalone ingest step.
- [ ] Working directory for all CLI commands below: `backend/` (i.e. `cd backend`)

---

## Smoke Tests — Module Invocation

### UAT-SMOKE-001: Standalone module run completes without errors

- **Description**: Verify `python -m app.knowledge_graph.ingest_injuries` runs to completion, emitting INFO log lines for each Injury merged.
- **Steps**:
  1. From the repo root, open a terminal
  2. Run the command below
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.ingest_injuries
  ```
- **Expected Result**: Process exits with code `0`. Stdout/stderr contains multiple lines matching `Merged Injury '<name>' (id=<uuid>) → <N> CONTRAINDICATED_BY edge(s).` for each active injury. No Python tracebacks or `ERROR`/`WARNING` lines (other than expected Neo4j advisory notices).
- [x] Pass <!-- 2026-06-06 -->

### UAT-SMOKE-002: Module is importable and `ingest_injuries` is exported

- **Description**: Verify the public API is importable without side-effects.
- **Steps**:
  1. Run the command below from inside `backend/`
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -c "from app.knowledge_graph.ingest_injuries import ingest_injuries, build_injury_records; print('OK')"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. No import errors.
- [x] Pass <!-- 2026-06-06 -->

---

## Graph State Tests — Injury Nodes

### UAT-GRAPH-001: Injury nodes exist after ingest

- **Description**: At least one `Injury` node exists in Neo4j after running the ingestor.
- **Steps**:
  1. Ensure UAT-SMOKE-001 has passed (ingest has run at least once)
  2. Run the Cypher query below
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (i:Injury) RETURN count(i) AS injury_count'
  ```
- **Expected Result**: `injury_count` is greater than `0`. Based on seed data (13 personas, most with at least 1 injury), expect at least `10` Injury nodes.
- [x] Pass <!-- 2026-06-06 -->

### UAT-GRAPH-002: Injury node properties are correctly set

- **Description**: Verify an Injury node has all expected properties: `id`, `name`, `affected_joints`, `severity`, `onset_date`, `status`.
- **Steps**:
  1. Run the query below
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (i:Injury) RETURN i.id, i.name, i.affected_joints, i.severity, i.onset_date, i.status LIMIT 5'
  ```
- **Expected Result**: Each row has non-null values for `i.id` (UUID string), `i.name` (string), `i.affected_joints` (list of strings), `i.severity` (one of `mild`, `moderate`, `severe`), `i.status` (one of `active`, `resolved`). `i.onset_date` may be null but must not error.
- [x] Pass <!-- 2026-06-06 -->

---

## Graph State Tests — HAS_INJURY Edges

### UAT-GRAPH-003: HAS_INJURY edges exist after ingest

- **Description**: At least one `(Member)-[:HAS_INJURY]->(Injury)` edge exists after ingest.
- **Steps**:
  1. Run the query below
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (m:Member)-[:HAS_INJURY]->(i:Injury) RETURN count(i) AS has_injury_count'
  ```
- **Expected Result**: `has_injury_count` is greater than `0`. Expect at least `10` edges (one per injury record created from personas).
- [x] Pass <!-- 2026-06-06 -->

### UAT-GRAPH-004: HAS_INJURY edges link correct Member to Injury

- **Description**: Each `HAS_INJURY` edge connects the correct `Member` node (matched by `member_id` from the injury record) to the `Injury` node.
- **Steps**:
  1. Run the query below to inspect a sample of member–injury pairings
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (m:Member)-[:HAS_INJURY]->(i:Injury) RETURN m.email, i.name, i.affected_joints LIMIT 10'
  ```
- **Expected Result**: Rows show recognisable pairings — e.g. the persona whose email appears in seed data has the injury name that matches the seed record. No row has a `null` `m.email`.
- [x] Pass <!-- 2026-06-06 -->

---

## Graph State Tests — CONTRAINDICATED_BY Edges

### UAT-GRAPH-005: CONTRAINDICATED_BY edges exist for active injuries

- **Description**: At least one `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)` edge exists for active injuries with non-empty `affected_joints`.
- **Steps**:
  1. Run the query below
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (e:Exercise)-[:CONTRAINDICATED_BY]->(i:Injury) RETURN count(e) AS contraindicated_count'
  ```
- **Expected Result**: `contraindicated_count` is greater than `0`. Because the seed data contains many active injuries across joints (knee, shoulder, ankle, wrist, hip, elbow, thoracic spine, cervical spine) and exercises have `joints_loaded` populated, many `CONTRAINDICATED_BY` edges should exist.
- [x] Pass <!-- 2026-06-06 -->

### UAT-GRAPH-006: CONTRAINDICATED_BY edges link exercises via joint overlap

- **Description**: Exercises contraindicated by a given injury load at least one of that injury's `affected_joints`.
- **Steps**:
  1. Run the query below to verify the join condition holds for a sample injury
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (e:Exercise)-[:CONTRAINDICATED_BY]->(i:Injury) WHERE i.name = "Left knee tendinopathy" RETURN e.name, e.joints_loaded, i.affected_joints LIMIT 10'
  ```
- **Expected Result**: Every returned exercise has `joints_loaded` containing at least `"knee"`. If `"Left knee tendinopathy"` does not exist, substitute another active knee injury name from UAT-GRAPH-002 output. No exercise appears that has no joints overlapping `["knee"]`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-GRAPH-007: Resolved injuries do NOT create CONTRAINDICATED_BY edges

- **Description**: Injuries with `status: "resolved"` must not generate `CONTRAINDICATED_BY` edges (per implementation: `ingest_injuries` only calls `_merge_contraindicated_by_edges` when `status == "active"`).
- **Steps**:
  1. Run the query below — seed data includes a persona with a resolved "Knee sprain"
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (e:Exercise)-[:CONTRAINDICATED_BY]->(i:Injury {status: "resolved"}) RETURN count(e) AS resolved_contraindications'
  ```
- **Expected Result**: `resolved_contraindications` is `0`. Resolved injuries must not contraindicate any exercise.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Persona with no injuries produces no Injury nodes or edges

- **Description**: A persona with an empty `injuries` list (e.g., "Jordan Cole" in seed data) must not cause errors and must not create any Injury nodes or HAS_INJURY edges for that member.
- **Steps**:
  1. After UAT-SMOKE-001 passes, run the query below to find the Member with no injuries
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (m:Member) WHERE NOT (m)-[:HAS_INJURY]->() RETURN m.email, m.name'
  ```
- **Expected Result**: At least one row appears (the persona(s) with no injuries). No error. The ingestor did not raise an exception for these personas.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Injury with empty `affected_joints` skips CONTRAINDICATED_BY edges

- **Description**: If a record has `affected_joints: []`, the ingestor must skip the `_merge_contraindicated_by_edges` call for that record (implementation guards: `if record.get("status") == "active" and affected_joints`). The Injury node and HAS_INJURY edge must still be created.
- **Steps**:
  1. This test is verified by inspecting the implementation: `ingest_injuries` only calls `_merge_contraindicated_by_edges` when `affected_joints` is non-empty.
  2. To confirm no unexpected CONTRAINDICATED_BY edges exist for empty-joints injuries, also run: UAT-GRAPH-005 count remains consistent across runs (see UAT-IDEM-001).
  3. Optionally, inspect the log output from UAT-SMOKE-001 for lines showing `→ 0 CONTRAINDICATED_BY edge(s)` for any injury without joints.
- **Expected Result**: No Python exception during ingest for injuries with empty `affected_joints`. Log line shows `→ 0 CONTRAINDICATED_BY edge(s)` for such injuries.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

---

## Idempotency Tests

### UAT-IDEM-001: Second ingest run produces identical graph state

- **Description**: Running the ingestor twice must not duplicate Injury nodes, HAS_INJURY edges, or CONTRAINDICATED_BY edges. All writes use `MERGE`.
- **Steps**:
  1. Record counts from UAT-GRAPH-001, UAT-GRAPH-003, and UAT-GRAPH-005 (first run).
  2. Run the ingestor a second time:
  3. Re-run the count queries and compare.
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.ingest_injuries
  ```
- **Expected Result**: After the second run, `MATCH (i:Injury) RETURN count(i)`, `MATCH ()-[:HAS_INJURY]->() RETURN count(*)`, and `MATCH ()-[:CONTRAINDICATED_BY]->() RETURN count(*)` each return the **same values** as before the second run. No duplicates.
- [x] Pass <!-- 2026-06-06 -->

### UAT-IDEM-002: Verify node counts unchanged after second run

- **Description**: Confirm counts via a single compound query after UAT-IDEM-001.
- **Command**:
  ```bash
  docker exec workout-wiz-neo4j-1 cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" 'MATCH (i:Injury) WITH count(i) AS injuries MATCH ()-[r:HAS_INJURY]->() WITH injuries, count(r) AS has_inj MATCH ()-[c:CONTRAINDICATED_BY]->() RETURN injuries, has_inj, count(c) AS contraind'
  ```
- **Expected Result**: All three counts are identical to those recorded before the second ingest run in UAT-IDEM-001.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: seed_loader.py calls ingest_injuries as part of full pipeline

- **Description**: Verify that `run_seed` in `seed_loader.py` calls `ingest_injuries` and produces the same graph state as standalone invocation.
- **Steps**:
  1. Clear graph state if needed (or run against a clean Neo4j volume).
  2. Run `seed_loader.py` to invoke the full pipeline.
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.seed_loader
  ```
- **Expected Result**: Process exits with code `0`. Stdout logs include a line `Ingesting Injury nodes and edges …` (from `run_seed`). After completion, UAT-GRAPH-001 and UAT-GRAPH-003 counts are non-zero (same as after standalone ingest).
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: `build_injury_records` produces records with required shape

- **Description**: Verify the `build_injury_records` function returns records matching the required shape (`id`, `member_id`, `name`, `affected_joints`, `severity`, `onset_date`, `status`) before ingest.
- **Steps**:
  1. Run the command below to print a sample record
- **Command**:
  ```bash
  cd backend && set -a && source ../.env && set +a && python -c "
import sqlalchemy, sqlalchemy.orm
from app.config import settings
from app.knowledge_graph.ingest_injuries import build_injury_records
from app.knowledge_graph.seed import seed_postgres_users
engine = sqlalchemy.create_engine(settings.database_url.replace('+asyncpg', ''))
with sqlalchemy.orm.Session(engine) as s:
    mm = seed_postgres_users(s)
    s.commit()
recs = build_injury_records(mm)
import json; print(json.dumps(recs[0], indent=2))
print(f'Total records: {len(recs)}')
"
  ```
- **Expected Result**: Printed JSON contains keys `id` (UUID string), `member_id` (UUID string), `name` (string), `affected_joints` (list), `severity` (string), `onset_date` (string or null), `status` (string). `Total records:` is greater than `0`.
- [x] Pass <!-- 2026-06-06 -->
