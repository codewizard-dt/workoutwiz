# Agents ↔ KG Architecture

> See `backend/app/agents/GRAPH_STRUCTURE.md` for the full node/edge/state reference.

---

## 1 — High-Level Request Flow

How a message travels from the user through the hub, into the appropriate sub-agent, and returns a response.

```mermaid
flowchart TD
    User((User))
    Hub(Hub StateGraph)
    Coach(coach_graph\nfitness Q&A)
    WorkoutLog(workout_logger_graph\nlog completed workout)
    KGPipeline(knowledge_graph node\nretrieval → generation)
    Clarification[clarification\nstatic prompt]
    Neo4j[(Neo4j\ntraversal + vector)]

    User -->|POST /chat/| Hub
    Hub -->|COACH| Coach
    Hub -->|WORKOUT_LOG| WorkoutLog
    Hub -->|KNOWLEDGE_GRAPH\nall workout generation| KGPipeline
    Hub -->|FALLBACK or conf < 0.6| Clarification
    KGPipeline <-->|queries + context| Neo4j
    Coach -->|reply| User
    WorkoutLog -->|reply| User
    KGPipeline -->|reply + kg_result| User
    Clarification -->|reply| User

    classDef agent fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef store fill:#fef3c7,stroke:#b45309,color:#111;
    classDef actor fill:#f3e8ff,stroke:#7c3aed,color:#111;
    classDef static fill:#f1f5f9,stroke:#64748b,color:#111;

    class Hub,Coach,WorkoutLog,KGPipeline agent;
    class Neo4j store;
    class User actor;
    class Clarification static;
```

---

## 2 — Hub Internals

Routing logic: the router LLM classifies intent into `RouteDecision{intent, confidence, reasoning}`. `_route_selector()` maps that to a node key; confidence < 0.6 always diverts to clarification regardless of intent.

```mermaid
flowchart LR
    State[[AgentState\nmessages · route_decision\nuser_id · audit_log · kg_result]]
    Router{router node\nChatAnthropic\nwith_structured_output}
    Coach(coach_graph\nsync sub-graph)
    WorkoutLog(workout_logger_graph\nsync sub-graph)
    KGNode(knowledge_graph node\nasync inline)
    Clarification[clarification node\nstatic — no LLM]

    State -->|last HumanMessage| Router
    Router -->|Intent.COACH\nconf ≥ 0.6| Coach
    Router -->|Intent.WORKOUT_LOG\nconf ≥ 0.6| WorkoutLog
    Router -->|Intent.KNOWLEDGE_GRAPH\nconf ≥ 0.6| KGNode
    Router -->|Intent.FALLBACK\nor conf < 0.6| Clarification
    Coach & WorkoutLog & KGNode & Clarification -->|messages + audit_log| State

    classDef subagent fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef decision fill:#fef9c3,stroke:#ca8a04,color:#111;
    classDef statenode fill:#f0fdf4,stroke:#16a34a,color:#111;
    classDef static fill:#f1f5f9,stroke:#64748b,color:#111;

    class Coach,WorkoutLog,KGNode subagent;
    class Router decision;
    class State statenode;
    class Clarification static;
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
