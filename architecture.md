# Architecture

Workout Wiz is a fitness coaching system built on a **LangGraph multi-agent hub** backed by a **FastAPI + PostgreSQL REST layer** and an optional **Neo4j knowledge-graph** for injury-aware, preference-weighted recommendations.

---

## System Overview

```
┌──────────────────────────────────────────────────────┐
│  Frontend                                            │
│  Vite · React · TypeScript · Tailwind · shadcn/ui    │
│  localhost:5173                                      │
└──────────────┬───────────────────────────────────────┘
               │ HTTP/JSON (Axios · TanStack Query)
┌──────────────▼───────────────────────────────────────┐
│  Multi-Agent Layer  (FastAPI routers)                │
│  POST /chat/                                         │
│  GET  /chat/audit/{session_id}                       │
│  POST /kg/recommend  · POST /kg/explain              │
│  GET  /kg/audit/{member_id}                          │
│  localhost:8000                                      │
└──────────────┬───────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────────────────────────────┐
│  PostgreSQL │  │  Neo4j                               │
│  users      │  │  Member · Exercise · Injury          │
│  exercises  │  │  BodyStructure · Disorder nodes      │
│  workouts   │  │  SNOMED traversal + vector index     │
│  sequences  │  │  bolt://localhost:7687               │
│  sets       │  └─────────────────────────────────────┘
│  :5433      │
└─────────────┘
```

---

## Hub StateGraph

The hub is a LangGraph `StateGraph[HubState]` with typed state and explicit conditional edges. Every incoming chat message passes through the router; the resulting intent determines which branch executes.

```
HubState
  ├─ messages        : list[BaseMessage]
  ├─ route           : str | None
  ├─ confidence      : float | None
  ├─ clarification   : str | None
  ├─ workout_draft   : WorkoutPlan | None
  ├─ kg_result       : KGResult | None
  └─ audit_log       : list[AuditEntry]
```

### Node graph

```
                   ┌──────────────────────┐
  user message ──▶ │    router_node        │
                   │  ChatAnthropic        │
                   │  .with_structured_output(RouteDecision)
                   │  → intent + confidence│
                   └──────────┬───────────┘
                              │
              ┌───────────────┼────────────────────┐
              │               │                    │
    confidence < 0.6    intent == X           FALLBACK
              │               │                    │
              ▼       ┌───────┼───────┐            ▼
      clarification  COACH  WORKOUT  KNOWLEDGE  fallback
        _node              _GENERATE  _GRAPH     _node
                           │         │
                    ┌──────┘    ┌────┘
                    │           │
             workout_gen   kg_node
              _node         │
                       retrieval_graph
                       generation_graph
                       safety_gate
```

### Routing decision

The router calls `ChatAnthropic.with_structured_output(RouteDecision)`, which forces the model to return a Pydantic model with `intent` (enum) and `confidence` (float 0–1). No regex or keyword matching is used.

| Intent | Threshold | Action |
|--------|-----------|--------|
| `COACH` | ≥ 0.6 | coach sub-graph |
| `WORKOUT_GENERATE` | ≥ 0.6 | workout generator sub-graph |
| `WORKOUT_LOG` | ≥ 0.6 | workout logger sub-graph |
| `KNOWLEDGE_GRAPH` | ≥ 0.6 | KG retrieval + generation pipeline |
| `FALLBACK` | any | polite out-of-scope reply |
| any | < 0.6 | clarification node |

---

## Sub-Agent Graphs

Each sub-agent is a **separate `StateGraph`** compiled into a `CompiledGraph` and composed into the hub as a node — not an inlined function.

### Coach sub-graph (`backend/app/agents/coach.py`)

A single-node graph that invokes `ChatAnthropic` with a system prompt grounding it in exercise science. Returns a coaching answer. No tool calls.

### Workout Generator sub-graph (`backend/app/agents/workout_generator.py`)

A ReAct-style tool-calling loop. Two tools with Pydantic input schemas:

| Tool | Behaviour |
|------|-----------|
| `search_exercises_tool` | Queries PostgreSQL for exercises matching muscle groups, equipment, movement patterns |
| `build_workout_tool` | Assembles selected exercise IDs into a warmup/main/cooldown plan; validates every ID against the DB; hallucinated UUIDs land in `invalid_ids_skipped` |

The generator calls `search_exercises_tool`, then `build_workout_tool`, then generates a human-readable response. Loop exits when no further tool calls are made.

### Workout Logger sub-graph (`backend/app/agents/workout_logger.py`)

A single-pass LLM node that extracts structured JSON from free-text input (exercise name, sets, reps, weight, duration). The extracted exercise name is fuzzy-matched against the exercise dataset using RapidFuzz; low-confidence matches are flagged rather than silently accepted.

---

## Knowledge Graph Pipeline

```
POST /kg/recommend
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  Retrieval Graph  (backend/app/kg/retrieval_graph.py) │
│                                                       │
│  ┌─────────────────┐  ┌──────────────────────────┐   │
│  │ member_lookup   │  │ injury_traversal          │   │
│  │ Neo4j: MATCH    │  │ SNOMED path: Injury→      │   │
│  │ (m:Member)      │  │  Disorder→BodyStructure   │   │
│  │ return profile  │  │  →Exercise (graph, not    │   │
│  │                 │  │  string match)            │   │
│  └────────┬────────┘  └──────────┬───────────────┘   │
│           │                      │                    │
│  ┌────────▼──────────────────────▼───────────────┐   │
│  │ preference_traversal                          │   │
│  │ Neo4j: member→FeedbackEvent→Exercise          │   │
│  │ → preferred_ids ordered by avg rating         │   │
│  └────────────────────────┬──────────────────────┘   │
│                           │                          │
│  ┌────────────────────────▼──────────────────────┐   │
│  │ vector_search                                 │   │
│  │ sentence-transformers/all-MiniLM-L6-v2        │   │
│  │ embed query → Neo4j vector index similarity   │   │
│  │ → top-K exercise candidates                   │   │
│  └────────────────────────┬──────────────────────┘   │
│                           │                          │
│  ┌────────────────────────▼──────────────────────┐   │
│  │ assemble_context                              │   │
│  │ merge member profile + safe exercises +       │   │
│  │ preferred + vector hits into ContextSlice     │   │
│  │ token budget: 2048 (ADR-001 D3)               │   │
│  └────────────────────────┬──────────────────────┘   │
└───────────────────────────┼───────────────────────────┘
                            │ ContextSlice
                            ▼
┌───────────────────────────────────────────────────────┐
│  Generation Graph  (backend/app/kg/generation_graph.py)│
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ kg_generation_llm_node                          │  │
│  │ ChatAnthropic.with_structured_output(KGResult)  │  │
│  │ system: "choose from safe_exercises only"       │  │
│  │ → recommended exercises with reasoning          │  │
│  └─────────────────────────┬───────────────────────┘  │
│                            │                          │
│  ┌─────────────────────────▼───────────────────────┐  │
│  │ safety_gate_node  ← HARD FILTER                 │  │
│  │ removes any exercise whose ID ∈ contraindicated │  │
│  │ runs AFTER LLM — prompt-injection proof         │  │
│  │ violations_filtered counter in audit_log        │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

### Safety guarantee

Contraindication filtering is enforced **deterministically through SNOMED graph traversal**, not by a prompt instruction. The path `Injury → MAPS_TO_DISORDER → Disorder → FINDING_SITE → BodyStructure → PART_OF*0.. → BodyStructure ← MAPS_TO ← Exercise` runs against Neo4j before the LLM call; the resulting set of contraindicated exercise IDs is passed as a hard exclusion list. A post-LLM safety gate then re-verifies the generated plan and strips any exercise that slipped through. No contraindicated exercise can reach the response regardless of what the model produces.

### Explainability

`POST /kg/explain` accepts `{ member_id, exercise_id }` and traverses the Neo4j graph to explain why an exercise was included or excluded. The explanation traces the actual SNOMED graph path (`Member → HAS_INJURY → Injury → MAPS_TO_DISORDER → Disorder → FINDING_SITE → BodyStructure → PART_OF* → BodyStructure ← MAPS_TO ← Exercise`), not an LLM rationale.

---

## Observability

Every node appends a structured entry to `HubState.audit_log`:

```json
{
  "event": "router",
  "model": "claude-haiku-4-5-20251001",
  "provider": "anthropic",
  "route": "WORKOUT_GENERATE",
  "confidence": 0.95,
  "latency_ms": 1129,
  "tokens_in": 1382,
  "tokens_out": 101,
  "user_id": "c40c2bc5-..."
}
```

The full session audit trail is available at `GET /chat/audit/{session_id}`. The KG layer has its own audit at `GET /kg/audit/{member_id}`.

### Per-session telemetry fields

| Field | Description |
|-------|-------------|
| `event` | Node name (router, generator, coach, workout_log, kg_hub, kg_generation_llm, kg_generation_safety_gate, retrieval_*) |
| `model` | LLM model ID or `"n/a"` for non-LLM nodes |
| `provider` | `"anthropic"` or `"neo4j"` |
| `latency_ms` | Wall-clock time for this node |
| `tokens_in` / `tokens_out` | Token counts (0 for non-LLM nodes) |
| `route` / `confidence` | Router-only fields |

---

## REST API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/healthz` | — | Liveness |
| POST | `/auth/register` | — | Register user |
| POST | `/auth/jwt/login` | — | Get JWT |
| GET | `/auth/me` | JWT | Current user |
| GET | `/exercises/` | — | List/filter exercises |
| GET/POST/PUT/DELETE | `/workouts/` | JWT | Workout CRUD |
| POST | `/chat/` | JWT | Hub entry point |
| GET | `/chat/audit/{session_id}` | JWT | Session audit trail |
| POST | `/kg/recommend` | — | KG recommendation |
| POST | `/kg/explain` | — | Graph-path explanation |
| POST | `/kg/feedback` | — | Write FeedbackEvent to Neo4j |
| GET | `/kg/audit/{member_id}` | — | KG audit trail |

---

## Database Schema

### PostgreSQL (SQLAlchemy async)

```
users               exercises
├─ id (UUID PK)     ├─ id (UUID PK)
├─ email            ├─ name
└─ hashed_password  ├─ muscle_groups (JSON)
                    ├─ equipment_required (JSON)
workouts            ├─ movement_patterns (JSON)
├─ id               ├─ joints_loaded (JSON)
├─ user_id → users  ├─ is_reps / is_duration / supports_weight
├─ started_at       └─ priority_tier
└─ ended_at
                    workout_sets
workout_sequences   ├─ id
├─ id               ├─ sequence_id → workout_sequences
├─ workout_id       ├─ exercise_id → exercises
└─ phase            ├─ set_type (STRENGTH/CARDIO)
                    ├─ reps / weight_kg / duration_s
                    └─ speed / distance / calories
```


```
// SNOMED-grounded safety path
(Member)-[:HAS_INJURY]->(Injury)-[:MAPS_TO_DISORDER]->(Disorder)
(Disorder)-[:FINDING_SITE]->(BodyStructure)-[:PART_OF*0..]->(BodyStructure)
(Exercise)-[:MAPS_TO]->(BodyStructure)

// Legacy fallback (pre-SNOMED data)
(Exercise)-[:CONTRAINDICATED_BY]->(Injury)

// Preference + history
(Member)-[:PERFORMED]->(WorkoutSession)-[:INCLUDED]->(Exercise)
(Member)-[:RATED]->(Exercise)
(Member)-[:HAS_INJURY]->(Injury)

// Vector similarity
(Exercise)-[*vector index: exercise_embeddings, 1536-dim cosine*]->(embedding)
```

#### SNOMED ontology nodes (seeded from NCI EVS via build script)

| Node | Key property | Purpose |
|------|-------------|---------|
| `BodyStructure` | `snomed_code`, `catalog_term` | Anatomical joint roots + sub-structures |
| `Disorder` | `snomed_code`, `label` | Clinical disorders (mapped from injury labels) |

The SNOMED subset (9 catalog joints + 19 disorders) is frozen to `backend/data/snomed_subset.json` at build time; the running application never calls the SNOMED CT API.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `with_structured_output` for routing | Enforces typed `RouteDecision`; eliminates regex fragility |
| Separate sub-graphs per intent | Each intent is a compiled `StateGraph`; hub composes them as nodes |
| SNOMED graph traversal | Contraindication derived from SNOMED `Disorder → FINDING_SITE → BodyStructure → PART_OF* → BodyStructure ← MAPS_TO ← Exercise`; deterministic code, not a prompt instruction |
| Post-LLM safety gate | Hard filter re-checks every recommended exercise against the contraindicated set; prompt-injection proof |
| exercises.json → PostgreSQL at boot | Single source of truth; exercises are query-able with SQL filters |
| In-memory audit log | Fast, no DB writes in the hot path; lost on restart (acceptable for demo) |
| Token budget cap (2048) | Prevents context overflow on long member histories (ADR-001 D3) |

---

## File Layout

```
backend/
  app/
    agents/
      hub.py                # HubState + compiled hub StateGraph
      state.py              # HubState, AuditEntry, RouteDecision
      coach.py              # coach sub-graph
      workout_generator.py  # generator sub-graph + tools
      workout_logger.py     # logger sub-graph
      exercises.py          # search_exercises_tool, build_workout_tool
      audit_persist.py      # audit log persistence helpers
    kg/
      retrieval_graph.py    # retrieval StateGraph (member/injury/vector nodes)
      generation_graph.py   # generation StateGraph (LLM + safety gate)
      context_assembler.py  # ContextSlice assembly + token budgeting
      embeddings.py         # sentence-transformers wrapper
      tools.py              # kg tool definitions
      explainability.py     # graph-path explanation
      feedback_service.py   # FeedbackEvent writer
    routers/
      chat.py               # POST /chat/, GET /chat/audit/{session_id}
      kg.py                 # /kg/* endpoints
      workouts.py           # workout CRUD
      exercises.py          # exercise list/filter
    models/                 # SQLAlchemy ORM models
    schemas/                # Pydantic request/response schemas
    services/               # business logic (workouts, exercises)
    auth.py                 # fastapi-users config
    database.py             # async engine + session factory
    main.py                 # FastAPI app + lifespan + middleware
frontend/
  src/
    components/             # ChatBubble, PhaseTable, RouteBadge, AgentTrace, FeedbackForm
    hooks/                  # useChat, useDraftWorkout
    pages/                  # ChatPage, WorkoutsPage, WorkoutDetailPage
    router.tsx              # TanStack Router
evals/
  golden/                   # 11 golden test cases (gs-001 → gs-011)
  scenarios/                # scenario coverage matrix (5 scenario files)
  replays/fixtures/         # frozen replay fixtures (no API calls)
  run_golden.py             # golden eval runner
  run_scenarios.py          # scenario runner
  stats.py                  # historical trend viewer
```
