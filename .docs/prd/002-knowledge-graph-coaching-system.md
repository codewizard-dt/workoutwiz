# PRD 002: Knowledge Graph Coaching System

> An AI coaching assistant that builds a knowledge graph of member context — injuries, history, goals, and preferences — and generates personalized, injury-aware, explainable workout recommendations traceable to graph relationships.

- **Status**: draft
- **Created**: 2026-06-06
- **Last updated**: 2026-06-06
- **Owner**: David Taylor
- **Stakeholders**: Recruiting engineer / assessor
- **Tags**: knowledge-graph, fitness, graphrag

## Problem Statement

Fitness coaches need a system that builds a persistent, structured representation of each member's context — including injuries, workout history, goals, and equipment constraints — so that an AI assistant can generate personalized, injury-aware workout recommendations. Current approaches rely on flat semantic search or ad-hoc LLM context stuffing, which cannot reliably enforce safety constraints (e.g. never recommending a contraindicated exercise) or provide traceable explanations (e.g. "barbell squats were skipped because of your knee injury, which loads the patellofemoral joint"). A knowledge graph as the retrieval substrate is what makes both safety and explainability possible in a way that can be audited and trusted. This system addresses Assessment 2 of the AI Engineering take-home, demonstrating graph-grounded reasoning over member context.

## Goals

| # | Goal | Linked Success Metric |
|---|------|-----------------------|
| 1 | Injury contraindication filtering is perfectly reliable — no contraindicated exercise ever appears in a generated workout | SM-1 |
| 2 | Every recommendation the coach questions can be traced to a specific graph path, enabling the coach to understand and trust the output | SM-2 |
| 3 | GraphRAG retrieval surfaces the correct member context for a given query | SM-3 |
| 4 | The system responds to coaching queries within an acceptable latency window | SM-4 |
| 5 | A developer can bring up the entire stack with a single command | SM-5 |

## Non-Goals (explicit out-of-scope)

| # | Non-Goal | Why excluded |
|---|----------|--------------|
| 1 | Real member or patient data | The assessment explicitly requires synthetic data only; real PII introduces compliance obligations out of scope for a 1–2 day exercise |
| 2 | SNOMED CT integration | A clean hand-rolled ontology is acceptable for this scope; SNOMED CT is listed as a stretch goal, not a requirement |
| 3 | Billing or authentication system | The assessment focus is knowledge graph reasoning and safety, not access control; auth is already addressed in Assessment 1 |
| 4 | Multi-agent hub router (Assessment 1 architecture) | Assessment 2 is a separate deliverable; the only integration point with Assessment 1 is a tool-call seam, not a rebuild of the hub |
| 5 | Production deployment or cloud infrastructure | The deliverable is a Dockerized local stack; no live deployment is required |

## Personas

| Persona | Context | Primary goal in this PRD |
|---------|---------|--------------------------|
| **Alex's Coach (fitness coach)** | Professional or semi-professional coach who manages multiple members, each with distinct injury histories and goals; must trust and explain every recommendation they give | Ask the system to build a member's workout session and receive an injury-aware plan they can present with confidence, including the ability to ask "why was X skipped?" |
| **Alex (member)** | A member with at least one documented injury, specific equipment constraints, and a workout history stored in the system; does not interact with the system directly but whose context shapes all outputs | Have all recommendations respect injury constraints, match available equipment, align with stated goals, and reflect recent workout history |
| **The recruiting engineer / assessor** | Reviews the submitted public GitHub repo to evaluate knowledge graph design, GraphRAG retrieval, safety filtering, explainability, and developer experience | Quickly assess whether the graph does real relational work (not just semantic search with extra steps), whether safety filtering is reliable, and whether the system runs with one command |

## User Stories

### US-1. Generate an injury-aware member workout

> As **Alex's Coach**, I want to ask the system "Build a lower-body session for Alex this week" so that I receive a personalized workout plan that respects Alex's documented injuries, equipment, goals, and recent training history — with no contraindicated exercises present.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | The system retrieves Alex's member context from the knowledge graph, including injury nodes and their associated joint/muscle constraints |
| 2 | No exercise appears in the generated workout that loads a joint or muscle group flagged as injured or contraindicated for Alex |
| 3 | The generated workout reflects Alex's available equipment — no exercise requiring unavailable equipment is included |
| 4 | The response is returned within 5 seconds of the coach submitting the request |
| 5 | The output is a structured workout plan (not raw graph data or a raw LLM completion), readable by the coach |

### US-2. Explain why an exercise was excluded

> As **Alex's Coach**, I want to ask "Why did you skip barbell squats for Alex?" so that I receive a graph-traceable explanation that I can use to build trust in the recommendation and communicate the reasoning to Alex.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | The system returns a human-readable explanation that cites the specific graph path used to exclude the exercise (e.g. "Alex has a knee injury → patellofemoral joint → barbell squats load the patellofemoral joint → exercise excluded") |
| 2 | The explanation references real nodes and edges from Alex's graph, not a generic LLM-generated rationale |
| 3 | The explanation is returned within 5 seconds |

### US-3. Surface member context and adherence signals

> As **Alex's Coach**, I want to ask "What should I watch for with Alex this week?" so that the system surfaces relevant context — flagged injuries, adherence trends, stated goals, and recent chat signals — drawn from the knowledge graph.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | The system retrieves and summarizes Alex's most recent workout history, any flagged injury nodes, and stated goals from the graph |
| 2 | Any adherence trend surfaced (e.g. missed sessions, declining volume) is derived from actual workout history nodes, not fabricated |
| 3 | The response clearly distinguishes between information grounded in the graph and any inferred or uncertain context |

### US-4. One-command stack startup

> As **the recruiting engineer / assessor**, I want to run `docker compose up` and have the full stack — graph database, backend API, and frontend — start and be reachable with no manual configuration steps so that I can evaluate the system immediately.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | `docker compose up` (from the repo root) starts all services without requiring any manual environment setup beyond what is documented in the README |
| 2 | The frontend is reachable in a browser and can submit a coaching query end-to-end within 2 minutes of `docker compose up` completing |
| 3 | The README includes a "How I would evaluate this system in production" section covering retrieval quality, safety/failure mode monitoring, latency, and success signals |

## Success Metrics

| ID | Signal | Threshold | When measured |
|----|--------|-----------|---------------|
| SM-1 | Contraindicated exercises appearing in generated workouts for members with documented injuries | 0 occurrences across all test scenarios | At project completion, via explicit test cases covering known injury→exercise contraindication paths |
| SM-2 | Coach "why?" queries that return a response traceable to a real graph path (not a vague LLM rationale) | 100% of "why?" queries return a graph-path citation | At project completion, verified manually against graph state |
| SM-3 | GraphRAG retrieval surfaces the correct member context (correct member's injuries, history, goals) for a given query | Correct context retrieved in all manually verified test scenarios | At project completion, verified against known graph state for synthetic members |
| SM-4 | End-to-end response latency for coaching queries | p50 under 5 seconds | Measured via manual timing on local Docker stack at project completion |
| SM-5 | Stack startup requiring manual steps beyond `docker compose up` | 0 additional manual steps required | Verified by assessor following README from a clean clone |

## Constraints

| # | Constraint | Source |
|---|------------|--------|
| 1 | All member data must be synthetic — no real personal or health data may be used | Assessment requirement (technical / regulatory) |
| 2 | The system must run end-to-end on a local Docker setup without cloud dependencies | Assessment requirement (business) |
| 3 | The exercise dataset is fixed at the 50 exercises in `exercises.json` — no external exercise APIs | Assessment requirement (business) |

## Assumptions

| # | Assumption | If false, impact |
|---|------------|------------------|
| 1 | A Neo4j instance (or compatible graph database) can be included in the Docker Compose stack without licensing friction for a public demo | If a license is required, the graph database choice must change to an open-source alternative (e.g. Apache AGE on PostgreSQL), and the graph schema design may need to adapt |
| 2 | Synthetic member profiles with 1–3 injuries and 2–4 weeks of workout history are sufficient to demonstrate graph traversal and safety filtering | If the assessors expect richer longitudinal data, the ingestion pipeline scope expands |
| 3 | The existing `exercises.json` dataset contains `joints_loaded` field values sufficient to model injury-to-exercise contraindication edges | If `joints_loaded` is absent or incomplete, the contraindication graph schema must be supplemented with a manual mapping |

## Open Questions

| # | Question | Owner | Resolution by |
|---|----------|-------|---------------|
| 1 | Should the knowledge graph schema ground injury concepts in SNOMED CT node IDs (stretch goal), or is a clean hand-rolled ontology the right tradeoff given the 1–2 day timeline? | David Taylor | 2026-06-07 |
| 2 | Which LLM provider should be used for generation and embedding? Assess cost/latency tradeoffs between OpenAI, Anthropic, and a local model. | David Taylor | 2026-06-07 |

## Linked ADRs

> Filled in by `/prd-extract-decisions`. Each row tracks one Architecturally Significant Requirement that became (or will become) an ADR.

| ASR | ADR | Status |
|-----|-----|--------|
| — | — | — |

## Linked Tasks

> Filled in as `/task-add --prd PRD-002` runs. The PRD is delivered when all linked tasks complete.

| Task | Status |
|------|--------|
| — | — |

## Amendments

> Appended by `/prd-update`. Never edit prior amendments — append a new one.

<!-- Amendments appear here as `## Amendment 1`, `## Amendment 2`, etc. -->
