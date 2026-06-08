# Tasks

**Last task:** [104-chat-history-kg-retrieval](104-chat-history-kg-retrieval.md)
**Next task number:** 105

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 071 | [feedback-submission-ui](071-feedback-submission-ui.md) | 5/5 ✓ | 065 | — | FeedbackForm component: star rating + text, POST /kg/feedback |
| 084 | [test-source-type-population](084-test-source-type-population.md) | 0/5 | 079 | — | Write tests asserting every exercise in KG recommendation has source_type set to valid enum |

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
