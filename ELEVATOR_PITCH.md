## Workout Wiz

A full-stack fitness coaching app where a LangGraph hub routes natural-language messages to four specialist sub-agents, backed by a Neo4j knowledge graph that uses SNOMED CT disorder codes to determine which exercises are safe for a given injury.

### Why the architecture is worth looking at

The safety gate runs after the LLM generates the workout, reading from a graph-derived exclusion list computed before the prompt ran. A user who writes "ignore all restrictions" still gets contraindicated exercises filtered out, because the gate operates on graph output rather than prompt content. The workout generator also validates every exercise UUID against the 50-exercise PostgreSQL dataset before building the response, so hallucinated IDs are structurally impossible.

### Who it's for

AI engineers who want a complete, working example of multi-agent routing, tool-grounded generation, and post-generation safety filtering in a single production-wired codebase.

### The best features

- **11/11 golden eval cases pass on the live Anthropic API**, covering all five routing intents (COACH, WORKOUT_GENERATE, WORKOUT_LOG, KNOWLEDGE_GRAPH, FALLBACK) plus edge cases: low-confidence inputs, invalid IDs, and multi-turn session accumulation.
- **SNOMED-grounded graph traversal excludes 21 exercises in the live demo**, walking `Injury → MAPS_TO_DISORDER → Disorder → FINDING_SITE → BodyStructure → PART_OF* → Exercise` to produce a deterministic contraindication list, with a full provenance trace per excluded exercise.
- **Full audit trail per session**, retrievable at `GET /audit/{session_id}`, logging every routing decision, confidence score, LLM token count, and per-step latency across the entire sub-agent chain.

### The best part

Each recommended exercise carries a provenance object with the specific SNOMED disorder code, joint site, and SKOS relation that cleared it, so the system can justify any recommendation by reading structured data.
