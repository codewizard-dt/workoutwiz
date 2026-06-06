# 042 — Add Neo4j Python driver and LangChain-Neo4j to backend dependencies

> **Depends on**: none
> **Blocks**: [044-neo4j-schema-init-script](044-neo4j-schema-init-script.md)
> **Parallel-safe with**: [041-neo4j-docker-compose](041-neo4j-docker-compose.md), [043-knowledge-graph-schema-design](043-knowledge-graph-schema-design.md)

## Objective

Add the Neo4j Python driver, LangChain-Neo4j integration, and LangChain-Community to `backend/pyproject.toml` so the backend can connect to Neo4j, run Cypher queries, and use Neo4jVector for vector similarity search.

## Approach

Add three new runtime dependencies to `[project].dependencies` in `backend/pyproject.toml`. Also add mypy overrides for the new packages so strict mode doesn't fail on their missing stubs. No new optional-dependency groups needed — these are core dependencies for the knowledge graph feature.

## Steps

### 1. Add dependencies to pyproject.toml  <!-- agent: general-purpose -->

Edit `backend/pyproject.toml`:

- Add to `[project].dependencies`:
  - `neo4j>=5.0` — official async-capable Neo4j Python driver
  - `langchain-neo4j>=0.1` — LangChain Neo4j integration (Neo4jGraph, Neo4jVector)
  - `langchain-community>=0.2` — community integrations required by langchain-neo4j

- Add mypy overrides (in `[[tool.mypy.overrides]]`) for:
  - `neo4j.*`
  - `langchain_neo4j.*`
  - `langchain_community.*`
  - Set `ignore_missing_imports = true` on each

- [ ] `neo4j>=5.0` is in `[project].dependencies`
- [ ] `langchain-neo4j>=0.1` is in `[project].dependencies`
- [ ] `langchain-community>=0.2` is in `[project].dependencies`
- [ ] mypy overrides added for `neo4j.*`, `langchain_neo4j.*`, `langchain_community.*`

## Acceptance Criteria

- [ ] `pyproject.toml` is valid TOML
- [ ] All three packages appear in `[project].dependencies`
- [ ] mypy overrides prevent strict-mode failures on missing stubs
