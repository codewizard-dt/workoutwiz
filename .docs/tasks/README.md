# Tasks

**Last task:** [085-test-kg-audit-endpoint](085-test-kg-audit-endpoint.md)
**Next task number:** 086

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 060 | [generation-agent-subgraph](060-generation-agent-subgraph.md) | 6/6 ✓ | 059 | 061,062,063 | Generation sub-graph: ContextSlice → WorkoutRecommendation via LLM |
| 071 | [feedback-submission-ui](071-feedback-submission-ui.md) | 5/5 ✓ | 065 | — | FeedbackForm component: star rating + text, POST /kg/feedback |
| 079 | [add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md) | 0/5 | 074,075,076,077 | 081 | Add source_type/source_id fields to RecommendedExercise model, populate during recommendation assembly |
| 081 | [add-kg-audit-endpoint](081-add-kg-audit-endpoint.md) | 0/5 | 074,075,076,077,079 | — | Create GET /kg/audit/{session_id} endpoint to expose KG-specific audit log entries |
| 082 | [test-routing-trace-coverage](082-test-routing-trace-coverage.md) | 0/5 | 074,075,076,077 | — | Write integration tests verifying complete audit_log trace coverage for all hub and KG nodes |
| 084 | [test-source-type-population](084-test-source-type-population.md) | 0/5 | 079 | — | Write tests asserting every exercise in KG recommendation has source_type set to valid enum |
| 085 | [test-kg-audit-endpoint](085-test-kg-audit-endpoint.md) | 0/6 | 081 | — | Write integration tests verifying GET /kg/audit/{session_id} returns expected KG event keys |

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
