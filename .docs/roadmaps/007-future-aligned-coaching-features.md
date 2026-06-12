# Roadmap 007: Future-Aligned Coaching Features

> Turn the Coach Copilot's computed signals into actionable accountability, and gate every AI output behind a human-coach review — aligning the system with Future's "people move people" thesis.

- **Status**: active
- **Created**: 2026-06-11
- **Last updated**: 2026-06-11 <!-- task 108 completed -->
- **Owner**: David Taylor
- **Linked PRD**: —
- **Linked ADRs**: —
- **Tags**: coaching, accountability, hitl

## Goal

When every box is checked, the `/coach` Copilot no longer just *displays* adherence and churn-risk — it generates ranked, actionable coach tasks with ready-to-send draft nudge messages grounded in member context, and every AI-generated recommendation or message passes through a human coach review/edit/approve gate before it can reach a member. This bridges Future's accountability-first thesis and their human-coach trust model ("90% prefer human coaches") with the existing multi-agent + knowledge-graph substrate. Derived from the gap-assess + company-align analysis (sections D.1 and D.2).

## Phase 1: Accountability Engine (end-to-end)

> Make the already-computed adherence / churn-risk signals *do* something a coach can act on.

- [x] [TASK-105: accountability_service: rank coach action items from adherence + churn-risk signals](../tasks/completed/105-accountability-service.md)
- [x] [TASK-106: POST /coach/nudge: draft context-grounded nudge message for a flagged member](../tasks/completed/106-coach-nudge-endpoint.md)
- [x] [TASK-107: Surface ranked action items + draft nudges in CoachPage morning-brief cards](../tasks/completed/107-coach-page-action-items.md)
- [x] [TASK-108: Critical test: low-adherence member yields a ranked action item + Playwright /coach path](../tasks/completed/108-accountability-engine-tests.md)

## Phase 2: HITL Approval (end-to-end)

> Insert a human review/edit/approve gate so AI augments the coach rather than replacing them.

- [x] [TASK-109: coach_draft persistence: draft | approved | sent status on AI-generated recommendations](../tasks/completed/109-coach-draft-persistence.md)
- [x] [TASK-110: PATCH /coach/draft/{id}: approve / edit / send lifecycle endpoint](../tasks/completed/110-coach-draft-lifecycle-endpoint.md)
- [x] [TASK-111: CoachPage draft review UI: edit and approve before output reaches a member](../tasks/completed/111-coach-draft-review-ui.md)
- [x] [TASK-112: Critical test: draft cannot reach a member without approved status + Playwright path](../tasks/completed/112-hitl-approval-tests.md)

## Notes

Both features intentionally reuse existing seams: `routers/coach.py` (adherence/churn computation, grounded-chat prompt assembly), the audit log (`models/audit_log.py`) for the approval trail, and the image-attachment composer already in `CoachPage.tsx`. All Phase items are inline placeholders — run `/roadmap-next` to create task files before tackling them.
