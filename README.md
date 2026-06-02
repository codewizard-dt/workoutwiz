# AI Engineer Take-Home

Take-home projects for AI engineering candidates, built around a fitness coaching domain. We'll tell you which assessment to complete — you don't need to do both.

## Assessments

The two are listed by scope. Each folder is self-contained and includes the `exercises.json` dataset.

| # | Assessment | Focus | Time |
|---|------------|-------|------|
| 1 | [`1-multi-agent/`](./1-multi-agent/ASSESSMENT.md) | **Multi-agent system** — a LangGraph hub agent routing requests to specialized sub-agents | 2–3 hours |
| 2 | [`2-knowledge-graph/`](./2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md) | **Knowledge graph coaching platform** — GraphRAG over a member's context for safe, explainable recommendations | 1–2 days |

### 1 · Multi-agent system — at a glance

- **Stack:** Python, LangGraph, LangChain, any LLM provider
- **Goal:** A small system that works end-to-end. Correctness over completeness.

Build a hub agent that routes user input across three intents:

| Route | Example |
|-------|---------|
| `COACH` | "What muscles does a deadlift work?" |
| `WORKOUT_GENERATE` | "Build me a 30 min upper body session with dumbbells" |
| `WORKOUT_LOG` | "I just did 3x10 bench press at 185 lbs" |

See [`1-multi-agent/ASSESSMENT.md`](./1-multi-agent/ASSESSMENT.md) for the full spec.

### 2 · Knowledge graph coaching platform — at a glance

- **Stack:** Python, TypeScript, LangChain/LangGraph, a graph database (Neo4j preferred), any LLM provider
- **Goal:** Ingest member context into a knowledge graph, retrieve the relevant slice via GraphRAG, and generate **injury-aware, explainable** recommendations.

See [`2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md`](./2-knowledge-graph/KNOWLEDGE_GRAPH_ASSESSMENT.md) for the full spec.

## The dataset

`exercises.json` contains 50 exercises. Key fields:

| Field | Meaning |
|-------|---------|
| `muscle_groups` | Primary muscles worked |
| `joints_loaded` | Joints under load (useful for injury avoidance) |
| `movement_patterns` | e.g. `upper push - horizontal` |
| `equipment_required` | Equipment needed |
| `priority_tier` | Programming priority (1 = highest) |
| `is_bilateral` / `bilateral_pair_id` | Single-side exercises and their paired side |

## How to submit

1. Build in a **public** GitHub repo.
2. Include a runnable demo or transcript, and a README covering setup and **how you'd evaluate the system in production**.
3. Send us the link.

If anything in the spec is ambiguous, make a reasonable decision and document it — we value clear tradeoff reasoning.
