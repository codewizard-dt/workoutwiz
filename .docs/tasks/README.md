# Tasks

**Last task:** [082-test-routing-trace-coverage](082-test-routing-trace-coverage.md)
**Next task number:** 083

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 060 | [generation-agent-subgraph](060-generation-agent-subgraph.md) | 6/6 ✓ | 059 | 061,062,063 | Generation sub-graph: ContextSlice → WorkoutRecommendation via LLM |
| 071 | [feedback-submission-ui](071-feedback-submission-ui.md) | 5/5 ✓ | 065 | — | FeedbackForm component: star rating + text, POST /kg/feedback |
| 074 | [observability-adr](074-observability-adr.md) | 8/8 ✓ | none | 075,076,077,078 | Write Observability Stack ADR — document in-process audit_log extension to all agent nodes and KG layers |
| 075 | [instrument-kg-hub-node](075-instrument-kg-hub-node.md) | 0/5 | 074 | 076,077,078,079 | Instrument KG hub node routing trace with audit entries for intent, confidence, and latency |
| 076 | [instrument-retrieval-nodes](076-instrument-retrieval-nodes.md) | 0/5 | 074,075 | 081 | Instrument all 5 retrieval sub-graph nodes with timing and result-count audit entries |
| 077 | [instrument-generation-nodes](077-instrument-generation-nodes.md) | 0/5 | 074 | 081 | Instrument 3 generation sub-graph nodes (safety gate, generation, fallback) with exercise-count audit entries |
| 078 | [instrument-explainability-tool](078-instrument-explainability-tool.md) | 0/5 | 074 | 080 | Instrument explainability tool with Neo4j query latency and traversal-depth audit entries |
| 079 | [add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md) | 0/5 | 074,075,076,077 | 081 | Add source_type/source_id fields to RecommendedExercise model, populate during recommendation assembly |
| 080 | [add-explainability-confidence-score](080-add-explainability-confidence-score.md) | 0/4 | 078 | 082 | Add explainability confidence score to explain_skipped_exercise() based on Neo4j path depth/strength |
| 081 | [add-kg-audit-endpoint](081-add-kg-audit-endpoint.md) | 0/5 | 074,075,076,077,079 | — | Create GET /kg/audit/{session_id} endpoint to expose KG-specific audit log entries |
| 082 | [test-routing-trace-coverage](082-test-routing-trace-coverage.md) | 0/5 | 074,075,076,077 | — | Write integration tests verifying complete audit_log trace coverage for all hub and KG nodes |

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
