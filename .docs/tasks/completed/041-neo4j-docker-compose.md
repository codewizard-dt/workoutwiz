# 041 — Add Neo4j service to docker-compose

> **Depends on**: none
> **Blocks**: [044-neo4j-schema-init-script](044-neo4j-schema-init-script.md)
> **Parallel-safe with**: [042-neo4j-python-dependencies](042-neo4j-python-dependencies.md), [043-knowledge-graph-schema-design](043-knowledge-graph-schema-design.md)

## Objective

Add a Neo4j 5 service to `docker-compose.yml` alongside the existing PostgreSQL service, including persistent volumes, healthcheck, and environment variable wiring so `docker compose up` starts a production-ready graph database.

## Approach

Extend the root `docker-compose.yml` with a `neo4j` service using the official `neo4j:5` image. Add `neo4j_data` and `neo4j_logs` named volumes. Wire `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` into `.env.example` so developers have an explicit template.

## Steps

### 1. Add neo4j service to docker-compose.yml  <!-- agent: general-purpose -->

Edit `docker-compose.yml` at the project root:

- Add the `neo4j` service block after `db`
- Add `neo4j_data` and `neo4j_logs` to the top-level `volumes:` section
- The service uses `neo4j:5` image
- Ports: `7474:7474` (HTTP browser) and `7687:7687` (Bolt protocol)
- Environment vars: `NEO4J_AUTH`, `NEO4J_PLUGINS`, memory settings
- Named volumes for `/data` and `/logs`
- Healthcheck via `cypher-shell`

- [ ] `docker-compose.yml` contains a `neo4j` service
- [ ] Ports 7474 and 7687 are exposed
- [ ] `neo4j_data` and `neo4j_logs` volumes are declared in the top-level `volumes:` section
- [ ] Healthcheck is configured

### 2. Update .env.example  <!-- agent: general-purpose -->

Add Neo4j connection variables to `.env.example`:
- `NEO4J_URI=bolt://localhost:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=password`

- [ ] `.env.example` contains `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`

## Acceptance Criteria

- [ ] `docker-compose.yml` validates (`docker compose config` exits 0)
- [ ] Neo4j service is present with ports 7474 and 7687
- [ ] Both named volumes (`neo4j_data`, `neo4j_logs`) are declared
- [ ] `.env.example` contains `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
