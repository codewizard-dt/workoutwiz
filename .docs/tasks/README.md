# Tasks

**Last task:** [073-readme-production-eval](073-readme-production-eval.md)
**Next task number:** 074

---

## Active Tasks

| # | Task | Progress | Depends on | Blocks | Objective |
|---|------|----------|------------|--------|-----------|
| 060 | [generation-agent-subgraph](060-generation-agent-subgraph.md) | 0/6 | 059 | 061,062,063 | Generation sub-graph: ContextSlice → WorkoutRecommendation via LLM |
| 061 | [injury-safety-gate](061-injury-safety-gate.md) | 0/4 | 060 | 063,065 | Post-generation gate: remove contraindicated exercises from output |
| 062 | [explainability-tool](062-explainability-tool.md) | 0/4 | 060 | 065 | explain_skipped_exercise() traverses graph for human-readable reason |
| 063 | [fallback-handler](063-fallback-handler.md) | 0/3 | 060,061 | 065 | Fallback node: use safe_exercises[:3] when too few options after gate |
| 064 | [feedback-writeback](064-feedback-writeback.md) | 0/5 | 053 | 065 | write_feedback() service + FeedbackPayload schema |
| 065 | [kg-fastapi-router](065-kg-fastapi-router.md) | 0/6 | 060,061,062,063,064 | 066,067,070,071 | POST /kg/recommend, /kg/explain, /kg/feedback endpoints |
| 066 | [tool-call-seam](066-tool-call-seam.md) | 0/3 | 065 | 067 | LangChain tools: kg_recommend_tool, kg_explain_tool |
| 067 | [hub-integration](067-hub-integration.md) | 0/4 | 066 | — | Update _knowledge_graph_node to run full recommendation pipeline |
| 068 | [critical-path-test-injury-filtering](068-critical-path-test-injury-filtering.md) | 0/3 | 060,061 | — | 5-case parameterized test: contraindicated exercises never in output |
| 069 | [critical-path-test-graph-retrieval](069-critical-path-test-graph-retrieval.md) | 0/3 | 059 | — | 5 tests: feedback + history surfaced in ContextSlice |
| 070 | [kg-chat-dashboard](070-kg-chat-dashboard.md) | 0/6 | 065 | — | /knowledge-graph React page with recommendation display |
| 071 | [feedback-submission-ui](071-feedback-submission-ui.md) | 0/5 | 065 | — | FeedbackForm component: star rating + text, POST /kg/feedback |
| 072 | [docker-compose-verification](072-docker-compose-verification.md) | 0/6 | 065 | — | docker compose up --build starts all services clean |
| 073 | [readme-production-eval](073-readme-production-eval.md) | 0/4 | — | — | README section: retrieval quality, safety, latency, token efficiency |

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
