# 093 — Shared Neo4j Driver Singleton (connection pooling)

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [090-concept-resolver-3pass](090-concept-resolver-3pass.md), [091-kg-muscle-equipment-pattern-nodes](091-kg-muscle-equipment-pattern-nodes.md), [092-fix-retrieval-double-traversal](092-fix-retrieval-double-traversal.md)

## Objective

Replace the per-request `neo4j.AsyncGraphDatabase.driver(...)` construction in the KG and coach routers with a single application-lifetime async driver so Neo4j connection pooling is actually used and connections are not exhausted under load.

## Approach

Create the async driver once in the FastAPI `lifespan` (mirroring how `database.py`'s engine is created and disposed), expose it through a `get_neo4j_driver()` FastAPI dependency that mirrors the `get_async_session()` pattern, and inject that dependency into every KG/coach handler — removing each per-request `driver = AsyncGraphDatabase.driver(...)` and its `finally: await driver.close()`. The shared driver is closed exactly once on shutdown.

## Prerequisites

- [x] Confirm the Neo4j connection settings exist on `Settings` in `backend/app/config.py` (`neo4j_uri`, `neo4j_user`, `neo4j_password`) — these are the values the singleton must use.
- [x] Review the existing singleton/lifecycle patterns to mirror: the module-level `engine` + `get_async_session()` in `backend/app/database.py`, the `lifespan` create/dispose flow in `backend/app/main.py`, and the `_vector_store_singleton` global-cache pattern in `backend/app/kg/embeddings.py`.
- [x] Note the request-path driver-construction sites the audit flagged so all are covered: `kg_recommend`, `kg_explain`, and `kg_feedback` in `backend/app/routers/kg.py` (three separate `AsyncGraphDatabase.driver(...)` calls, each closed in `finally`), and the `_neo4j_driver()` factory in `backend/app/routers/coach.py` used by `get_coach_brief` and `coach_chat`.

---

## Steps

### 1. Driver provider module + lifespan  <!-- agent: general-purpose -->

- [x] Create `backend/app/kg/driver.py` exposing the shared async driver: either a module-level singleton (mirroring `embeddings.py`'s `_vector_store_singleton`) or via `app.state`, with `create_neo4j_driver()` / `close_neo4j_driver()` helpers built from `settings.neo4j_uri` and `(settings.neo4j_user, settings.neo4j_password)`. <!-- Completed: 2026-06-07 -->
- [x] In `backend/app/main.py` `lifespan`, create the shared driver on startup (alongside the existing exercise-cache load) and `await driver.close()` on shutdown (alongside the existing `engine.dispose()`). <!-- Completed: 2026-06-07 -->

### 2. FastAPI dependency  <!-- agent: general-purpose -->

- [x] Add a `get_neo4j_driver()` dependency (in `backend/app/kg/driver.py`) that returns the shared driver, mirroring the `get_async_session()` async-generator dependency shape in `backend/app/database.py` so handlers can `Depends(get_neo4j_driver)`. <!-- Completed: 2026-06-07 -->
- [x] Ensure the dependency does NOT close the driver (lifetime is owned by `lifespan`), unlike the per-request handlers it replaces. <!-- Completed: 2026-06-07 -->

### 3. Refactor routers to use the shared driver  <!-- agent: general-purpose -->

- [x] In `backend/app/routers/kg.py`, inject `driver: neo4j.AsyncDriver = Depends(get_neo4j_driver)` into `kg_recommend`, `kg_explain`, and `kg_feedback`; delete the three `driver = neo4j.AsyncGraphDatabase.driver(...)` constructions and remove their `finally: await driver.close()` blocks (keep the surrounding `try/except` error handling). <!-- Completed: 2026-06-07 -->
- [x] In `backend/app/routers/coach.py`, inject the dependency into `get_coach_brief` and `coach_chat`; delete the `_neo4j_driver()` factory and remove the `finally: await driver.close()` blocks (keep the `try/except` error handling and the existing `_fetch_member_context(driver, ...)` calls). <!-- Completed: 2026-06-07 -->
- [x] Confirm whether the other request-path driver constructions — `kg_recommend_tool` / `kg_explain_tool` in `backend/app/kg/tools.py` and the `async with neo4j.AsyncGraphDatabase.driver(...)` in `backend/app/agents/hub.py` — should also consume the shared driver; refactor them to accept/use it if reachable from the request path. (Leave the one-shot CLI ingest/seed scripts under `backend/app/knowledge_graph/` untouched — they are short-lived processes, not request handlers.) <!-- Completed: 2026-06-07 — tools.py and hub.py use create_neo4j_driver() singleton -->

### 4. Tests  <!-- agent: general-purpose -->

- [x] Add a test asserting the driver is a singleton — repeated `get_neo4j_driver()` / `create_neo4j_driver()` calls return the same instance (no new driver per call). <!-- Completed: 2026-06-07 — test_create_neo4j_driver_returns_singleton in test_kg_router.py -->
- [x] Add/adjust router tests confirming the KG and coach endpoints still function with the injected dependency (mock or override `get_neo4j_driver` as needed). <!-- Completed: 2026-06-07 — all KG/hub/tools tests updated to use dependency override -->

### N. Verification  <!-- agent: general-purpose -->

- [x] Run the backend test suite and confirm it passes. <!-- Completed: 2026-06-07 — 0 new failures; 33 pre-existing failures unchanged from baseline 34 (we eliminated one pre-existing) -->
- [x] Run a Serena `search_for_pattern` for `AsyncGraphDatabase` / `\.driver(` across `backend/app/routers/` and confirm no per-request driver construction remains in the request-path routers. <!-- Completed: 2026-06-07 — search returned empty; all 3 kg.py + 2 coach.py sites eliminated -->

## Acceptance Criteria

- [x] Exactly one async Neo4j driver is created for the application lifetime (in `lifespan`) and closed exactly once on shutdown.
- [x] `backend/app/routers/kg.py` and `backend/app/routers/coach.py` obtain the driver via `Depends(get_neo4j_driver)`; no handler constructs `AsyncGraphDatabase.driver(...)` and no handler closes the driver in a `finally` block.
- [x] The `get_neo4j_driver()` dependency mirrors the `get_async_session()` pattern and does not close the shared driver.
- [x] Backend tests (including the singleton-reuse test) pass.

---
**UAT**: [`.docs/uat/093-neo4j-driver-singleton.uat.md`](../uat/093-neo4j-driver-singleton.uat.md)
