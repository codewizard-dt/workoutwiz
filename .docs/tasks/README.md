# Tasks

**Last task:** [036-readme-production-eval](completed/036-readme-production-eval.md)
**Next task number:** 037

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 033 | [critical-path-router-test](033-critical-path-router-test.md) | 0/7 | 024, 025 | — | ≥5 mocked tests proving router correctly classifies all 3 intents + fallback |
| 034 | [critical-path-generator-test](034-critical-path-generator-test.md) | 0/5 | 028 | — | ≥3 tests proving workout generator is grounded in exercises.json (no hallucination) |

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
