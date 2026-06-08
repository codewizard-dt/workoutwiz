# Roadmap 004: Knowledge Graph Coaching System

> Build a Neo4j-backed coaching layer with GraphRAG retrieval, injury-aware generation, and exercise feedback — delivering all Assessment 2 core requirements.

- **Status**: done
- **Created**: 2026-06-06
- **Last updated**: 2026-06-06 (TASK-066 complete — tool-call seam)
- **Owner**: David Taylor
- **Linked PRD**: — (PRD-002 to be created from `.docs/guides/2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md`)
- **Linked ADRs**: [ADR-001: GraphRAG Retrieval Strategy](../adr/001-graphrag-retrieval-strategy.md)
- **Tags**: knowledge-graph, neo4j, graphrag

## Goal

Build a Neo4j knowledge graph coaching layer integrated into the existing FastAPI backend via a minimal tool-call seam. The system ingests synthetic member profiles, injury records, workout history, and exercise feedback (1–5 ratings + text), then uses GraphRAG retrieval (graph traversal + vector search) to generate injury-aware, explainable workout recommendations. When every box is checked, the system delivers all Assessment 2 core requirements: documented schema, ingestion pipeline, GraphRAG retrieval, REST API, frontend integration, Docker Compose setup, 2 critical-path tests, and a production-evaluation README section.

## Phase 1: Infra

> Stand up Neo4j in Docker and lay the graph schema foundation.

- [x] [TASK-041: Add Neo4j service to docker-compose](../tasks/completed/041-neo4j-docker-compose.md)
- [x] [TASK-043: Design and document the knowledge graph schema](../tasks/completed/043-knowledge-graph-schema-design.md)
- [x] [TASK-042: Add Neo4j Python driver and langchain-neo4j to backend dependencies](../tasks/completed/042-neo4j-python-dependencies.md)
- [x] [TASK-044: Schema initialization script](../tasks/completed/044-neo4j-schema-init-script.md)

## Phase 2: Seed

> Generate synthetic member data representing realistic coaching scenarios.

- [x] Design synthetic member profiles (2+ personas with varied goals, equipment, availability, injury history)
- [x] Generate synthetic workout history (sessions, sets, timestamps) per member
- [x] Generate synthetic exercise feedback (1–5 ratings + free-text) per exercise, set, and workout
- [x] Generate synthetic injury/condition records (e.g., knee tendinopathy, shoulder impingement) with affected joints
- [x] Idempotent seed loader script (runs on `docker compose up` or via CLI)

## Phase 3: Ingest

> Load all seed data into Neo4j as structured nodes and edges.

- [x] [TASK-050: Exercise Neo4j ingestion](../tasks/completed/050-exercise-neo4j-ingestion.md)
- [x] [TASK-051: Member profile ingestion](../tasks/completed/051-member-profile-ingestion.md)
- [x] [TASK-049: Injury ingestion: condition records → Injury nodes + HAS_INJURY + CONTRAINDICATED_BY edges](../tasks/completed/049-injury-ingestion.md)
- [x] [TASK-052: Workout history ingestion into Neo4j](../tasks/completed/052-ingest-workout-history-neo4j.md)
- [x] [TASK-053: Feedback ingestion: FeedbackEvent nodes + edges to Exercise, WorkoutSession, and Set](../tasks/completed/053-feedback-ingestion-neo4j.md)

## Phase 4: GraphRAG

> Architecture decision point — design the retrieval layer before any generation code is written.

- [x] [TASK-054: ADR — GraphRAG retrieval strategy](../tasks/completed/054-graphrag-adr.md)
- [x] [TASK-055: Vector embeddings — embed exercises into Neo4j vector index](../tasks/completed/055-vector-embeddings.md)
- [x] [TASK-056: Graph traversal queries — injury-aware exercise filtering](../tasks/completed/056-injury-traversal-queries.md)
- [x] [TASK-057: Preference/feedback traversal — surface highly-rated and performed exercises](../tasks/completed/057-preference-feedback-traversal.md)
- [x] [TASK-058: Context assembler — merge traversal results and vector hits into token-budget context](../tasks/completed/058-context-assembler.md)
- [x] [TASK-059: Retrieval sub-graph — LangGraph StateGraph wrapping traversal and vector search](../tasks/completed/059-retrieval-subgraph.md)

## Phase 5: Generation

> Injury-aware, personalized, explainable workout recommendations.

- [x] [TASK-060: Generation agent sub-graph — context slice → structured workout recommendation](../tasks/completed/060-generation-agent-subgraph.md)
- [x] [TASK-061: Injury safety gate — post-generation validation, no contraindicated exercises in output](../tasks/061-injury-safety-gate.md)
- [x] [TASK-062: Explainability tool — traverse graph to explain why an exercise was skipped](../tasks/completed/062-explainability-tool.md)
- [x] [TASK-063: Fallback handler — surface alternatives when safe exercises are too few](../tasks/completed/063-fallback-handler.md)
- [x] [TASK-064: Feedback write-back — persist post-workout ratings/text via FeedbackEvent ingestion](../tasks/completed/064-feedback-writeback.md)

## Phase 6: Backend API Integration

> Wire the knowledge graph layer into the existing FastAPI app via tool calls.

- [x] [TASK-065: KG FastAPI router — /kg/recommend, /kg/explain, /kg/feedback with typed Pydantic schemas](../tasks/completed/065-kg-fastapi-router.md)
- [x] [TASK-066: Tool-call seam — expose retrieval + generation as LangChain tools callable from hub](../tasks/completed/066-tool-call-seam.md)
- [x] [TASK-067: Hub integration — full KG recommendation flow in hub node](../tasks/completed/067-hub-integration.md)
- [x] [TASK-068: Critical-path test 1 — injury filtering correctness](../tasks/completed/068-critical-path-test-injury-filtering.md)
- [x] [TASK-069: Critical-path test 2 — graph retrieval returns member-relevant context](../tasks/completed/069-critical-path-test-graph-retrieval.md)

## Phase 7: Frontend Integration

> Complete the Assessment 2 frontend and Docker Compose deliverable.

- [x] [TASK-070: KG chat/dashboard — knowledge graph frontend page](../tasks/completed/070-kg-chat-dashboard.md)
- [x] [TASK-071: Feedback submission UI — rate exercise 1–5, submit text feedback](../tasks/071-feedback-submission-ui.md)
- [x] [TASK-072: Docker Compose verification — full stack starts clean](../tasks/completed/072-docker-compose-verification.md)
- [x] [TASK-073: README production evaluation section — retrieval quality, safety, latency, token efficiency](../tasks/completed/073-readme-production-eval.md)

## Notes

PRD-002 should be created before execution begins: `prd-create` from `.docs/guides/2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md`.

Phase 4 is an intentional architecture pause — write the ADR before any retrieval or generation code. GraphRAG design decisions (traversal depth, embedding model, context token budget) affect all downstream work.

Integration seam decision: the existing hub and knowledge graph layer interact only via LangChain tool calls. Assessment 1 code paths (COACH, WORKOUT_GENERATE, WORKOUT_LOG) are not modified.

**Schema changes completed (prerequisite for Phase 2 and Phase 3):**
- `Exercise` model: added `joints_loaded` (ARRAY text[], NOT NULL, GIN-indexed), `side` (String(10), nullable), `estimated_rep_duration` (Float, nullable); changed `movement_patterns` from JSON to ARRAY(String).
- New `ExerciseFeedback` model + `FeedbackContextType` enum in `backend/app/models/feedback.py`.
- Migration `e4a51dde0a60` applied to both local (port 5432) and Docker (port 5433) databases.
- `faker>=24.0` added to dev dependencies in `backend/pyproject.toml`.
