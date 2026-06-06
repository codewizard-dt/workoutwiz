# 049 — Injury ingestion: condition records → Injury nodes + HAS_INJURY + CONTRAINDICATED_BY edges

> **Depends on**: [044-neo4j-schema-init-script](completed/044-neo4j-schema-init-script.md), [042-neo4j-python-dependencies](completed/042-neo4j-python-dependencies.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md)

## Objective

Implement `backend/app/knowledge_graph/ingest_injuries.py` to load synthetic injury/condition records into Neo4j as `Injury` nodes, create `(Member)-[:HAS_INJURY]->(Injury)` edges for each affected member, and create `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)` edges for every Exercise whose `joints_loaded` overlaps the injury's `affected_joints`. The ingestor must be idempotent (MERGE, not CREATE) and callable as `python -m app.knowledge_graph.ingest_injuries` or imported by the seed loader.

## Approach

The ingestor reads synthetic injury records from the seed data produced in Phase 2 (a Python list/dict structure in `backend/app/knowledge_graph/seed_data.py` or an equivalent JSON file at `backend/app/knowledge_graph/seed/injuries.json`). For each record it:

1. MERGEs an `Injury` node keyed on `id`.
2. MERGEs the `(Member)-[:HAS_INJURY]->(Injury)` relationship using the record's `member_id`.
3. Runs a single Cypher query to MERGE `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)` for all Exercise nodes where `ANY(j IN e.joints_loaded WHERE j IN $affected_joints)`.

All writes use explicit write transactions via the `neo4j` Python driver. The module exposes `ingest_injuries(driver, records)` as its public API so it can be composed by `backend/app/knowledge_graph/seed_loader.py`.

## Steps

### 1. Confirm seed injury data format  <!-- agent: general-purpose -->

Locate the Phase 2 seed data for injuries. Check `backend/app/knowledge_graph/seed_data.py` and `backend/app/knowledge_graph/seed/` (or equivalent paths established during Phase 2).

Expected injury record shape (each element in the `injuries` list):
```python
{
    "id": "<uuid>",
    "member_id": "<uuid matching a Member node>",
    "name": "Knee Tendinopathy",
    "affected_joints": ["knee"],
    "severity": "moderate",          # one of: mild, moderate, severe
    "onset_date": "2024-03-15",      # ISO date string or None
    "status": "active"               # or "resolved"
}
```

If the seed file uses a different structure, adapt the ingestor in step 2 to match — do not modify the seed data.

- [x] Seed injury data location is confirmed and record shape is understood <!-- Completed: 2026-06-06 -->

### 2. Create `ingest_injuries.py`  <!-- agent: general-purpose -->

Create `backend/app/knowledge_graph/ingest_injuries.py` with:

**`_merge_injury_node(tx, record: dict) -> None`** — private helper, runs inside a write transaction:
```cypher
MERGE (i:Injury {id: $id})
SET i.name          = $name,
    i.affected_joints = $affected_joints,
    i.severity      = $severity,
    i.onset_date    = $onset_date,
    i.status        = $status
```

**`_merge_has_injury_edge(tx, member_id: str, injury_id: str) -> None`** — private helper:
```cypher
MATCH (m:Member {id: $member_id})
MATCH (i:Injury {id: $injury_id})
MERGE (m)-[:HAS_INJURY]->(i)
```

**`_merge_contraindicated_by_edges(tx, injury_id: str, affected_joints: list[str]) -> None`** — private helper, one query covers all matching exercises:
```cypher
MATCH (e:Exercise)
WHERE ANY(j IN e.joints_loaded WHERE j IN $affected_joints)
MATCH (i:Injury {id: $injury_id})
MERGE (e)-[:CONTRAINDICATED_BY]->(i)
```

**`ingest_injuries(driver: neo4j.Driver, records: list[dict]) -> None`** — public function:
- Iterates over `records`.
- For each record, opens a write session and runs `_merge_injury_node`, `_merge_has_injury_edge` (using `record["member_id"]`), and `_merge_contraindicated_by_edges` (using `record["id"]` and `record["affected_joints"]`) — each in its own `session.execute_write(...)` call.
- Logs the injury name and count of CONTRAINDICATED_BY edges created (use `RETURN count(e)` in the Cypher to capture it).
- Handles `neo4j.exceptions.Neo4jError` with a logged warning and re-raises.

**`__main__` block**:
```python
if __name__ == "__main__":
    from app.config import settings
    from app.knowledge_graph.seed_data import INJURIES  # adjust import to match Phase 2 module
    import neo4j
    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        ingest_injuries(driver, INJURIES)
    finally:
        driver.close()
```

- [x] `backend/app/knowledge_graph/ingest_injuries.py` created <!-- Completed: 2026-06-06 -->
- [x] `_merge_injury_node` uses `MERGE ... SET` (idempotent)
- [x] `_merge_has_injury_edge` uses `MERGE` (idempotent)
- [x] `_merge_contraindicated_by_edges` uses `ANY(j IN e.joints_loaded ...)` joint overlap logic
- [x] `_merge_contraindicated_by_edges` uses `MERGE` (idempotent)
- [x] `ingest_injuries(driver, records)` is exported at module level
- [x] `__main__` block present and references correct seed import

### 3. Wire into seed loader  <!-- agent: general-purpose -->

Open `backend/app/knowledge_graph/seed_loader.py` (create it if it does not exist yet).

Add or update a section that calls `ingest_injuries`:
```python
from app.knowledge_graph.ingest_injuries import ingest_injuries
from app.knowledge_graph.seed_data import INJURIES  # adjust to match Phase 2 module

def run_seed(driver):
    # ... other ingestors called here (member profiles, etc.) ...
    ingest_injuries(driver, INJURIES)
```

If `seed_loader.py` does not exist, create it with a `run_seed(driver)` function and a `__main__` block identical in structure to the one in step 2.

- [x] `seed_loader.py` imports and calls `ingest_injuries` <!-- Completed: 2026-06-06 -->
- [x] Calling `ingest_injuries` is idempotent when `run_seed` is called multiple times

### 4. Manual smoke test [DEFERRED-TO-UAT] <!-- agent: general-purpose -->

With `docker compose up -d neo4j` running and the schema already initialized (TASK-044), run:

```bash
set -a && source .env && set +a
cd backend
python -m app.knowledge_graph.ingest_injuries
```

Then verify in the Neo4j Browser (`http://localhost:7474`) or via `cypher-shell`:

```cypher
-- Count Injury nodes
MATCH (i:Injury) RETURN count(i);

-- Count HAS_INJURY edges
MATCH ()-[:HAS_INJURY]->(i:Injury) RETURN count(i);

-- Count CONTRAINDICATED_BY edges
MATCH (e:Exercise)-[:CONTRAINDICATED_BY]->(i:Injury) RETURN count(e), i.name;

-- Confirm idempotency: run ingest again, counts must not change
```

- [ ] At least 1 `Injury` node exists after ingest [DEFERRED-TO-UAT]
- [ ] At least 1 `HAS_INJURY` edge exists after ingest [DEFERRED-TO-UAT]
- [ ] At least 1 `CONTRAINDICATED_BY` edge exists after ingest (confirms `joints_loaded` overlap is non-empty) [DEFERRED-TO-UAT]
- [ ] Running ingest a second time does not duplicate nodes or edges [DEFERRED-TO-UAT]

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/ingest_injuries.py` exists and is valid Python
- [x] `ingest_injuries(driver, records)` is importable from that module
- [x] All Cypher write operations use `MERGE` (never `CREATE`) — fully idempotent
- [x] `CONTRAINDICATED_BY` edges are created for every Exercise whose `joints_loaded` intersects the injury's `affected_joints`
- [x] `HAS_INJURY` edges link the correct `Member` node (matched by `member_id`) to each `Injury` node
- [x] `seed_loader.py` calls `ingest_injuries` as part of the full seed pipeline
- [x] Module is runnable standalone: `python -m app.knowledge_graph.ingest_injuries` from `backend/`
- [ ] Second run produces identical graph state (idempotency confirmed) [DEFERRED-TO-UAT]

---
**UAT**: [`.docs/uat/049-injury-ingestion.uat.md`](../uat/049-injury-ingestion.uat.md)
