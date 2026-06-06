# LangGraph Fitness Coaching Multi-Agent System

> Auto-generated from `.docs/roadmaps/002-langgraph-multi-agent-system.md` by `/mermaid-flowchart`.

```mermaid
flowchart TD
    User((User))
    ChatAPI[/"POST /chat\n+ Session Support"\]
    AuditLog[(LLM Audit Log\ntokens · provider · user_id)]
    ExerciseDB[(Exercise DB\n50 exercises)]

    subgraph Hub["Hub StateGraph"]
        direction TD
        Router(Router Node\nwith_structured_output)
        Conf{confidence\n≥ 0.6?}
        Clarify([Clarification Node\nask user to rephrase])
        Router --> Conf
        Conf -->|"low confidence / FALLBACK"| Clarify
    end

    subgraph SubAgents["Sub-Agent Graphs"]
        direction LR
        Coach(Coach\nSub-Agent)
        WorkoutGen(Workout Generator\nSub-Agent)
        WorkoutLog(Workout Logger\nSub-Agent)
    end

    User -->|HTTP| ChatAPI
    ChatAPI --> Router
    Router -.->|"per-call audit"| AuditLog

    Conf -->|"COACH"| Coach
    Conf -->|"WORKOUT_GENERATE"| WorkoutGen
    Conf -->|"WORKOUT_LOG"| WorkoutLog

    WorkoutGen -->|"search_exercises\nbuild_workout"| ExerciseDB
    WorkoutLog -->|"fuzzy match"| ExerciseDB

    Coach --> ChatAPI
    WorkoutGen --> ChatAPI
    WorkoutLog --> ChatAPI
    Clarify --> ChatAPI
    ChatAPI -->|response| User

    classDef db fill:#fef3c7,stroke:#b45309,color:#111;
    classDef agent fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef api fill:#dcfce7,stroke:#15803d,color:#111;
    classDef actor fill:#f3e8ff,stroke:#7e22ce,color:#111;

    class ExerciseDB,AuditLog db;
    class Coach,WorkoutGen,WorkoutLog agent;
    class ChatAPI api;
    class User actor;
```

## Notes

- The `confidence ≥ 0.6` threshold and FALLBACK intent are documented in the roadmap's Notes section; the exact field name (`confidence`) comes from the router's structured-output schema.
- Both `WorkoutGen` and `WorkoutLog` access `ExerciseDB` — `WorkoutGen` via `search_exercises`/`build_workout` tools, `WorkoutLog` via fuzzy exercise matching to produce structured JSON.
- Return arrows from sub-agents flow back through `ChatAPI` for simplicity; in the actual graph, responses pass back through Hub state before FastAPI serialises them.
- `AuditLog` is drawn as a dotted edge from `Router` because audit entries are written per LLM call (all three sub-agents also write audit rows, but those edges are omitted to avoid clutter).
