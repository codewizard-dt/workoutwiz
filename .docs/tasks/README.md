# Tasks

**Last task:** [112-hitl-approval-tests](completed/112-hitl-approval-tests.md)
**Next task number:** 113

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 071 | [feedback-submission-ui](071-feedback-submission-ui.md) | 5/5 ✓ | 065 | — | FeedbackForm component: star rating + text, POST /kg/feedback |

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
