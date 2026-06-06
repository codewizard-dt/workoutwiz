# 051 — Member profile ingestion

> **Depends on**: [044-neo4j-schema-init-script](completed/044-neo4j-schema-init-script.md), [042-neo4j-python-dependencies](completed/042-neo4j-python-dependencies.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md)

## Objective

Create `backend/app/knowledge_graph/ingest_members.py` — a standalone, idempotent ingestion module that reads the 15 fixed synthetic personas defined in `seed.py` and MERGEs each as a `Member` node in Neo4j with all schema-required properties (`id`, `email`, `name`, `goals`, `equipment_available`, `sessions_per_week`, `created_at`). The module is runnable as `python -m app.knowledge_graph.ingest_members` and callable as a library function from the combined `seed.py` orchestrator.

## Approach

Extract the member-ingestion concern from `seed.py`'s `seed_members_neo4j()` function into a dedicated module following the same package pattern as `init_schema.py`. The module imports `PERSONAS` from `seed.py` and the PostgreSQL `member_map` (a `{email: UUID}` dict) is passed in as a parameter so the module does not own the PostgreSQL connection — matching the existing separation of concerns in `seed.py`. The ingestion uses `MERGE` on `Member.id` (the uniqueness constraint set up in TASK-044) followed by `SET m += {...}` to make it idempotent. A `__main__` block wires up both a PostgreSQL session (to fetch or create user UUIDs) and a Neo4j driver, making the module self-contained for CLI use.

The module must **not** duplicate `PERSONAS` — it imports them from `seed.py`. The existing `seed_members_neo4j()` function in `seed.py` should be replaced with a thin call to the new module's public function so no member-ingestion logic lives in two places.

## Steps

### 1. Create `ingest_members.py`  <!-- agent: general-purpose -->

Create `backend/app/knowledge_graph/ingest_members.py` with the following:

**Imports:**
```python
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone

import neo4j

from app.knowledge_graph.seed import PERSONAS  # source of truth for synthetic profiles
```

**Public function — `ingest_members(driver, member_map)`:**
```python
def ingest_members(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
) -> None:
    """
    MERGE Member nodes in Neo4j for each persona.

    Args:
        driver: Connected Neo4j driver instance.
        member_map: Mapping of {email: postgres_uuid} — determines the Member.id
                    stored in Neo4j, ensuring cross-store consistency.
    """
```

Implementation details:
- Open a single `driver.session()` for all personas (batching reduces round-trips)
- For each persona in `PERSONAS`, run:
  ```cypher
  MERGE (m:Member {id: $id})
  SET m += {
      email:               $email,
      name:                $name,
      goals:               $goals,
      equipment_available: $equipment,
      sessions_per_week:   $sessions_per_week,
      created_at:          $created_at
  }
  ```
  Parameters:
  - `id`: `str(member_map[persona["email"]])` (UUID from PostgreSQL, cast to string)
  - `email`: `persona["email"]`
  - `name`: `persona["name"]`
  - `goals`: `persona["goals"]`
  - `equipment`: `persona["equipment"]`
  - `sessions_per_week`: `persona["sessions_per_week"]`
  - `created_at`: `datetime.now(timezone.utc).isoformat()` (stable enough for seed data; use `neo4j.time.DateTime` if the driver version supports it)
- Log `"Merged Member: %s (%s)"` for each persona at INFO level
- Log `"Ingested %d Member nodes into Neo4j."` after the loop

**`__main__` block:**

Wire up PostgreSQL + Neo4j independently so the module is CLI-runnable without importing `seed.py`'s `main()`:
```python
if __name__ == "__main__":
    import sqlalchemy
    from app.config import settings
    from app.knowledge_graph.seed import seed_postgres_users  # reuse existing pg upsert

    engine = sqlalchemy.create_engine(settings.database_url)
    with sqlalchemy.orm.Session(engine) as pg_session:
        member_map = seed_postgres_users(pg_session)
        pg_session.commit()

    neo4j_driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        ingest_members(neo4j_driver, member_map)
    finally:
        neo4j_driver.close()
```

Acceptance checkboxes:
- [x] `backend/app/knowledge_graph/ingest_members.py` exists <!-- Completed: 2026-06-06 -->
- [x] `ingest_members(driver, member_map)` is the sole public function; imports `PERSONAS` from `seed.py`
- [x] All 7 Member properties written: `id`, `email`, `name`, `goals`, `equipment_available`, `sessions_per_week`, `created_at`
- [x] Cypher uses `MERGE` on `Member.id` (idempotent — safe to run multiple times)
- [x] `__main__` block is present and runnable as `python -m app.knowledge_graph.ingest_members`
- [x] INFO-level logging for each merged member and a final count log

### 2. Refactor `seed.py` to delegate to `ingest_members`  <!-- agent: general-purpose -->

Replace the body of `seed_members_neo4j()` in `backend/app/knowledge_graph/seed.py` with a one-liner that calls the new module, eliminating the duplicate logic:

```python
from app.knowledge_graph.ingest_members import ingest_members as _ingest_members

def seed_members_neo4j(
    driver: neo4j.Driver,
    member_map: dict[str, uuid.UUID],
) -> None:
    """MERGE Member nodes using PostgreSQL UUIDs as id."""
    _ingest_members(driver, member_map)
```

This keeps `seed.py`'s orchestration intact while making `ingest_members.py` the single source of member-ingestion logic.

Acceptance checkboxes:
- [x] `seed_members_neo4j()` in `seed.py` delegates to `ingest_members()` — no duplicated Cypher <!-- Completed: 2026-06-06 -->
- [x] `seed.py` `main()` still runs end-to-end without errors (member ingestion path unchanged externally)
- [x] No circular import: `ingest_members.py` imports from `seed.py` only for `PERSONAS` and `seed_postgres_users`; `seed.py` imports from `ingest_members.py` only for `ingest_members`

### 3. Verify idempotency  <!-- agent: general-purpose -->

Confirm the ingestion is safe to run multiple times by checking the Cypher and the uniqueness constraint:

- `MERGE (m:Member {id: $id})` relies on the `member_id` uniqueness constraint created by `init_schema.py` (TASK-044). Running the script twice must not create duplicate nodes.
- `SET m += {...}` is additive/update — it does not delete properties not in the map.

Manual verification (documented for the UAT):
```bash
set -a && source .env && set +a
cd backend
python -m app.knowledge_graph.ingest_members
python -m app.knowledge_graph.ingest_members  # second run must be a no-op for node count
```

Expected: Neo4j contains exactly 15 Member nodes after either one or two runs.

Acceptance checkboxes:
- [DEFERRED-TO-UAT] Running the script twice does not increase the Member node count above 15
- [DEFERRED-TO-UAT] All 15 personas from `PERSONAS` produce a Member node (count confirmed via Cypher: `MATCH (m:Member) RETURN count(m)`)

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/ingest_members.py` exists and is valid Python (no import errors) <!-- Completed: 2026-06-06 -->
- [x] `ingest_members(driver, member_map)` is importable and callable with a neo4j Driver + dict
- [x] All Member node properties match the schema in `.docs/knowledge-graph-schema.md`: `id`, `email`, `name`, `goals`, `equipment_available`, `sessions_per_week`, `created_at`
- [x] MERGE semantics are used (not CREATE) — running twice produces 15 nodes, not 30
- [x] `seed_members_neo4j()` in `seed.py` delegates to `ingest_members()` — single source of truth
- [DEFERRED-TO-UAT] Module is runnable standalone: `python -m app.knowledge_graph.ingest_members` succeeds
- [x] No circular import between `ingest_members.py` and `seed.py`

---
**UAT**: [`.docs/uat/051-member-profile-ingestion.uat.md`](../uat/051-member-profile-ingestion.uat.md)
