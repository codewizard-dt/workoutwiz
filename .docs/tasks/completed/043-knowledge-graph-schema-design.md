# 043 — Design and document the knowledge graph schema

> **Depends on**: none
> **Blocks**: [044-neo4j-schema-init-script](044-neo4j-schema-init-script.md)
> **Parallel-safe with**: [041-neo4j-docker-compose](041-neo4j-docker-compose.md), [042-neo4j-python-dependencies](042-neo4j-python-dependencies.md)

## Objective

Create a design document at `.docs/knowledge-graph-schema.md` that precisely defines every node label, property, relationship type, and key traversal pattern for the Neo4j coaching graph. This document is the authoritative reference for all subsequent ingestion, retrieval, and generation tasks.

## Approach

Write a structured Markdown document covering node types (Member, Exercise, Injury, Preference, FeedbackEvent, WorkoutSession), relationship types with direction and meaning, and example Cypher traversal patterns for the two primary use-cases: injury-aware exercise filtering and preference/feedback surfacing.

## Steps

### 1. Create .docs/knowledge-graph-schema.md  <!-- agent: general-purpose -->

Write the schema document covering:

- **Node labels** with all properties and types
- **Relationship types** with direction, cardinality, and property payloads
- **Key traversal patterns** (Cypher examples)
- **Vector index** specification for exercise embeddings

- [ ] `.docs/knowledge-graph-schema.md` exists
- [ ] All 6 node labels are documented with properties
- [ ] All relationship types are documented with direction and semantics
- [ ] At least 2 Cypher traversal examples are included
- [ ] Vector index specification is present

## Acceptance Criteria

- [ ] File exists at `.docs/knowledge-graph-schema.md`
- [ ] Document covers Member, Exercise, Injury, Preference, FeedbackEvent, WorkoutSession nodes
- [ ] Document covers HAS_INJURY, PERFORMED, INCLUDED, RATED, CONTRAINDICATED_BY, LOADS_JOINT, AFFECTS_JOINT relationships
- [ ] Injury-aware filtering traversal pattern is shown in Cypher
- [ ] Preference/feedback lookup traversal pattern is shown in Cypher
