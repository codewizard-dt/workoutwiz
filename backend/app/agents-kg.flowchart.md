# Agents ↔ KG Architecture

> Auto-generated from `backend/app/agents/` and `backend/app/kg/` by `/mermaid-flowchart`.

---

## 1 — High-Level Request Flow

How a message travels from the user through the hub, into the KG pipeline, hits the data layer, and returns a response.

```mermaid
flowchart TD
    User((User))
    Hub(Hub StateGraph)
    Coach(Coach Agent)
    Workout(Workout Agents)
    KGPipeline(KG Pipeline\nretrieval → generation)
    Neo4j[(Neo4j\ntraversal + vector)]

    User -->|chat message| Hub
    Hub -->|COACH| Coach
    Hub -->|WORKOUT_GENERATE\nWORKOUT_LOG| Workout
    Hub -->|KNOWLEDGE_GRAPH| KGPipeline
    KGPipeline <-->|queries + context| Neo4j
    Coach -->|response| User
    Workout -->|response| User
    KGPipeline -->|response| User

    classDef agent fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef store fill:#fef3c7,stroke:#b45309,color:#111;
    classDef actor fill:#f3e8ff,stroke:#7c3aed,color:#111;

    class Hub,Coach,Workout,KGPipeline agent;
    class Neo4j store;
    class User actor;
```

---

## 2 — Hub Internals

How the hub StateGraph routes a message to the right sub-agent. All nodes share `AgentState`.

```mermaid
flowchart LR
    State[[AgentState]]
    Router{Router\nLLM structured output}
    Coach(coach_graph)
    WorkoutGen(workout_generator_graph)
    WorkoutLog(workout_logger_graph)
    KGNode(kg_node\n→ retrieval_graph)
    Fallback[fallback response]

    State -->|supplies context| Router
    Router -->|COACH| Coach
    Router -->|WORKOUT_GENERATE| WorkoutGen
    Router -->|WORKOUT_LOG| WorkoutLog
    Router -->|KNOWLEDGE_GRAPH| KGNode
    Router -->|FALLBACK| Fallback
    Coach & WorkoutGen & WorkoutLog & KGNode & Fallback -->|writes messages| State

    classDef subagent fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef decision fill:#fef9c3,stroke:#ca8a04,color:#111;
    classDef statenode fill:#f0fdf4,stroke:#16a34a,color:#111;

    class Coach,WorkoutGen,WorkoutLog,KGNode subagent;
    class Router decision;
    class State,Fallback statenode;
```

---

## 3 — KG Internals

How the KG package works on its own. Two entry points: the hub's `kg_node` (direct) and `KGTools` (via API router).

```mermaid
flowchart LR
    KGTools(KGTools\nkg_recommend · kg_explain)
    Retrieval(retrieval_graph\nlookup → traverse → search → assemble)
    Generation(generation_graph\nsafety gate → LLM → format)
    CtxAssembler[[context_assembler\ntoken-budgeted slice]]
    Embeddings[[embeddings\nNeo4jVector]]
    Explainability[[explainability]]
    DataStore[(knowledge_graph\nNeo4j traversal + vector index)]

    KGTools -->|build_retrieval_graph| Retrieval
    KGTools -->|build_generation_graph| Generation
    KGTools -->|explain_skipped_exercise| Explainability
    Retrieval -->|assemble_context| CtxAssembler
    Retrieval -->|vector search| Embeddings
    CtxAssembler <-->|traversal queries| DataStore
    Embeddings <-->|similarity index| DataStore
    Retrieval -->|ContextSlice| Generation
    Explainability <-->|Cypher query| DataStore

    classDef subgraph_ fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef module fill:#f0fdf4,stroke:#16a34a,color:#111;
    classDef store fill:#fef3c7,stroke:#b45309,color:#111;

    class KGTools,Retrieval,Generation subgraph_;
    class CtxAssembler,Embeddings,Explainability module;
    class DataStore store;
```

---

## Notes

- **Single agents→KG touchpoint**: `hub.kg_node` calls `build_retrieval_graph(driver)` directly — it is the only import crossing the package boundary from `app/agents` into `app/kg`.
- **KGTools is a parallel entry point**: `app/kg/tools.py` exposes `kg_recommend_tool` and `kg_explain_tool` as LangChain tools callable from the FastAPI router, but the hub does not bind them.
- **FeedbackService is router-only**: `feedback_service.write_feedback` is called from the `/kg/feedback` FastAPI endpoint, not from any LangGraph node — omitted from chart 3 for clarity.
- **GenerationGraph receives context via state**: `retrieval_graph` assembles a `ContextSlice` and passes it through `RetrievalState`; `generation_graph` reads it from there — no direct function call between the two graphs.
