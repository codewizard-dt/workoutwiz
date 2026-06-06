# Tasks

**Last task:** [036-readme-production-eval](036-readme-production-eval.md)
**Next task number:** 037

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 026 | [clarification-node](026-clarification-node.md) | 0/8 | 024 | — | Finalize clarification node with reasoning, capability list, and audit entry |
| 030 | [chat-endpoint](030-chat-endpoint.md) | 0/12 | 024, 027, 028, 029 | — | POST /chat endpoint with session/thread ID for multi-turn conversation |
| 031 | [web-ui](031-web-ui.md) | 0/7 | 030 | — | Minimal HTML/JS web UI served by FastAPI |
| 032 | [llm-audit-log](032-llm-audit-log.md) | 0/11 | 030 | — | Per-call LLM audit log with tokens, model, provider, user ID, route, latency |
| 033 | [critical-path-router-test](033-critical-path-router-test.md) | 0/7 | 024, 025 | — | ≥5 mocked tests proving router correctly classifies all 3 intents + fallback |
| 034 | [critical-path-generator-test](034-critical-path-generator-test.md) | 0/5 | 028 | — | ≥3 tests proving workout generator is grounded in exercises.json (no hallucination) |
| 035 | [e2e-smoke-test](035-e2e-smoke-test.md) | 0/5 | 030, 031 | — | 5 golden-path smoke tests via FastAPI TestClient (mocked hub) |
| 036 | [readme-production-eval](036-readme-production-eval.md) | 0/3 | 030 | — | Production Evaluation section in README: metrics, failure modes, health signals, demo |

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
