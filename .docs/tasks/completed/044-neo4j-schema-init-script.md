# 044 — Neo4j schema initialization script

> **Depends on**: [041-neo4j-docker-compose](041-neo4j-docker-compose.md), [042-neo4j-python-dependencies](042-neo4j-python-dependencies.md), [043-knowledge-graph-schema-design](043-knowledge-graph-schema-design.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Create an idempotent Neo4j schema initialization script at `backend/app/knowledge_graph/init_schema.py` that creates all uniqueness constraints, lookup indexes, and the Exercise embedding vector index. Running it multiple times must be safe (uses `IF NOT EXISTS` throughout).

## Approach

Create a new `knowledge_graph` package inside `backend/app/`. The `init_schema.py` module exposes a single `init_neo4j_schema(driver)` function that runs all Cypher DDL statements in a write transaction. A `__main__` entry point reads `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` from the environment (via `app.config.settings`) and calls the function, making it runnable as `python -m app.knowledge_graph.init_schema`.

## Steps

### 1. Create the knowledge_graph package  <!-- agent: general-purpose -->

Create `backend/app/knowledge_graph/__init__.py` (empty).

- [ ] `backend/app/knowledge_graph/__init__.py` exists

### 2. Create init_schema.py  <!-- agent: general-purpose -->

Create `backend/app/knowledge_graph/init_schema.py` with:

- `CONSTRAINTS` list of Cypher strings using `CREATE CONSTRAINT ... IF NOT EXISTS`:
  - `member_id`: Member.id IS UNIQUE
  - `exercise_id`: Exercise.id IS UNIQUE
  - `injury_id`: Injury.id IS UNIQUE
  - `workout_session_id`: WorkoutSession.id IS UNIQUE
  - `feedback_event_id`: FeedbackEvent.id IS UNIQUE

- `INDEXES` list of Cypher strings using `CREATE INDEX ... IF NOT EXISTS`:
  - Exercise name (text lookup)
  - Member email (lookup)
  - FeedbackEvent created_at (range queries)
  - WorkoutSession started_at (range queries)

- `VECTOR_INDEXES` list with the Exercise embeddings vector index:
  ```cypher
  CREATE VECTOR INDEX exercise_embeddings IF NOT EXISTS
  FOR (e:Exercise) ON (e.description_embedding)
  OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}
  ```

- `init_neo4j_schema(driver: neo4j.Driver) -> None` function:
  - Runs all constraints, indexes, and vector indexes in a single write session
  - Logs progress for each DDL statement

- `__main__` block: reads `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` from `app.config.settings`, creates driver, calls `init_neo4j_schema`, closes driver

- [ ] `backend/app/knowledge_graph/init_schema.py` exists
- [ ] All 5 uniqueness constraints are present with `IF NOT EXISTS`
- [ ] All 4 indexes are present with `IF NOT EXISTS`
- [ ] Vector index for exercise embeddings is present
- [ ] `init_neo4j_schema(driver)` function is exported
- [ ] `__main__` block is present

### 3. Add Neo4j settings to config.py  <!-- agent: general-purpose -->

Add to `Settings` class in `backend/app/config.py`:
- `neo4j_uri: str = "bolt://localhost:7687"`
- `neo4j_user: str = "neo4j"`
- `neo4j_password: str = "password"`

- [ ] `Settings` in `config.py` has `neo4j_uri`, `neo4j_user`, `neo4j_password`

## Acceptance Criteria

- [ ] `backend/app/knowledge_graph/__init__.py` exists
- [ ] `backend/app/knowledge_graph/init_schema.py` exists and is valid Python
- [ ] `init_neo4j_schema` function accepts a `neo4j.Driver` and is importable
- [ ] All DDL statements use `IF NOT EXISTS` (idempotent)
- [ ] `Settings` in `config.py` exposes `neo4j_uri`, `neo4j_user`, `neo4j_password`
- [ ] Script is runnable as `python -m app.knowledge_graph.init_schema` from `backend/`
