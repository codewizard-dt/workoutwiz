# Tasks

**Last task:** [101-fix-chatmessage-kg-result-type](101-fix-chatmessage-kg-result-type.md)
**Next task number:** 102

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 060 | [generation-agent-subgraph](060-generation-agent-subgraph.md) | 6/6 ✓ | 059 | 061,062,063 | Generation sub-graph: ContextSlice → WorkoutRecommendation via LLM |
| 071 | [feedback-submission-ui](071-feedback-submission-ui.md) | 5/5 ✓ | 065 | — | FeedbackForm component: star rating + text, POST /kg/feedback |
| 084 | [test-source-type-population](084-test-source-type-population.md) | 0/5 | 079 | — | Write tests asserting every exercise in KG recommendation has source_type set to valid enum |
| 090 | [concept-resolver-3pass](090-concept-resolver-3pass.md) | 0/20 | — | — | Implement a runtime 3-pass concept resolver (exact → fuzzy → embedding) with confidence thresholds and graceful degradation. |
| 091 | [kg-muscle-equipment-pattern-nodes](091-kg-muscle-equipment-pattern-nodes.md) | 0/13 | — | — | Promote Muscle/MovementPattern/Equipment to first-class Neo4j nodes with typed TARGETS/REQUIRES/HAS_PATTERN edges. |
| 092 | [fix-retrieval-double-traversal](092-fix-retrieval-double-traversal.md) | 0/17 | — | — | Eliminate redundant double-traversal in retrieval_graph.assemble by threading pre-fetched state into context assembly. |
| 093 | [neo4j-driver-singleton](093-neo4j-driver-singleton.md) | 0/11 | — | — | Replace per-request Neo4j driver instantiation with a shared connection-pooled driver via lifespan + dependency. |
| 094 | [workout-exclusion-filter-ui](094-workout-exclusion-filter-ui.md) | 0/10 | — | — | Add interactive exercise-exclusion and equipment-filter controls to the New Workout page. |
| 095 | [coach-chat-image-support](095-coach-chat-image-support.md) | 0/10 | — | — | Let a coach attach and view images in the Coach Copilot chat (client-side MVP). |
| 096 | [coach-message-charts](096-coach-message-charts.md) | 0/14 | — | — | Add message-pattern and 4-week comparison charts to the Coach dashboard using Recharts. |
| 097 | [coach-member-switcher](097-coach-member-switcher.md) | 0/14 | 099 | — | Add a member list/switcher so the coach dashboard is not hardcoded to one member. |
| 098 | [workout-duration-field](098-workout-duration-field.md) | 0/6 | — | — | Add a structured session-duration/time-window control to the New Workout page. |
| 099 | [seed-multi-persona-context](099-seed-multi-persona-context.md) | 0/11 | — | 097 | Seed rich member context (labs, chat, workouts, profile) for all personas, not just Jordan Rivera. |
| 100 | [document-ope-copper-ontologies](100-document-ope-copper-ontologies.md) | 0/14 | — | — | Document OPE & COPPER ontology decisions (used vs omitted, with rationale) in the methodology doc. |
| 101 | [fix-chatmessage-kg-result-type](101-fix-chatmessage-kg-result-type.md) | 0/7 | — | — | Add the kg_result field (and KGResult type) to the exported ChatMessage TypeScript interface. |

---

## File Format Reference

Task files live in `.docs/tasks/NNN-slug.md`. Each file must contain:

```markdown
# NNN — Task Title

> **Depends on**: [NNN-slug](NNN-slug.md) or none
> **Blocks**: [NNN-slug](NNN-slug.md) or none
> **Parallel-safe with**: [NNN-slug](NNN-slug.md) or none

## Objective

One or two sentences. What gets built and why.

## Approach

Key decisions and rationale.

## Steps

### 1. Step Name  <!-- agent: general-purpose -->

Detailed implementation instructions with specific file paths, function names, and code snippets.

- [ ] Acceptance checkbox

## Acceptance Criteria

- [ ] Top-level pass/fail criteria
```

See `.docs/guides/task-lifecycle.md` for lifecycle commands and file movement rules.
