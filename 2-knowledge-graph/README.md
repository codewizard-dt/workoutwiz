# Knowledge Graph Coaching Platform — Take-Home

**Time:** 1–2 days · **Stack:** Python, TypeScript, LangChain/LangGraph, a graph database (Neo4j preferred), any LLM provider

Build an AI coaching assistant that ingests a member's context into a **knowledge graph**, retrieves the relevant slice via **GraphRAG** (graph traversal + vector search), and generates **injury-aware, explainable** workout and coaching recommendations.

The differentiator is reasoning over relationships — the graph is what lets the system explain *why* a recommendation was made.

## Files

- **[`KNOWLEDGE_GRAPH_ASSESSMENT.md`](./KNOWLEDGE_GRAPH_ASSESSMENT.md)** — the full prompt: task, requirements, stretch goals
- **[`exercises.json`](./exercises.json)** — the exercise dataset (50 exercises)

> Use synthetic members, injuries, and context signals — **do not use any real member or personal data.**

## Submitting

Build in a **public** GitHub repo. Include the Dockerized setup, a runnable demo or recorded walkthrough, and a clear README. See [`KNOWLEDGE_GRAPH_ASSESSMENT.md`](./KNOWLEDGE_GRAPH_ASSESSMENT.md) for the complete requirements.
