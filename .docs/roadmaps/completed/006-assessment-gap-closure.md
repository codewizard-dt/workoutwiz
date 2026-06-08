# Roadmap 006: Assessment Gap Closure

> Close every gap identified in the 2026-06-07 assessment audit so the repo is submission-ready for all three assessments.

- **Status**: done
- **Created**: 2026-06-07
- **Last updated**: 2026-06-08 (103 completed)
- **Owner**: David Taylor
- **Linked PRD**: —
- **Linked ADRs**: —
- **Tags**: kg, agents, frontend

## Goal

Close every gap identified in the 2026-06-07 audit of the app against the multi-agent (Assessment 1), knowledge-graph coaching (Assessment 2), and candidate-assessment-main requirements. When every box is checked, the system will have: a complete README production-evaluation section for the KG system, a runtime 3-pass concept resolver, first-class graph nodes for Muscle/MovementPattern/Equipment, rich member context for all personas, and all missing frontend surfaces — making the repo credibly submission-ready.

## Phase 1: Quick Wins

> High-impact items that each take under one hour. Clear these first to improve the baseline score before tackling larger work.

- [x] [TASK-086: README: KG System Production Evaluation Section](../tasks/completed/086-readme-kg-production-eval.md)
- [x] [TASK-087: Fix Stale test_intent_values Assertion (add KNOWLEDGE_GRAPH)](../tasks/completed/087-fix-stale-intent-values-test.md)
- [x] [TASK-088: Populate Cooldown Phase in build_workout Tool](../tasks/completed/088-build-workout-cooldown-phase.md)
- [x] [TASK-089: Graceful LLM Error Handling in Coach & Generator Sub-Agents](../tasks/completed/089-subagent-llm-error-handling.md)

## Phase 2: KG Depth

> Core knowledge graph modeling gaps. These are the highest-weight items for the candidate-assessment-main scoring rubric.

- [x] [TASK-090: Runtime 3-Pass Concept Resolver (exact → fuzzy → embedding)](../tasks/completed/090-concept-resolver-3pass.md)
- [x] [TASK-091: Promote Muscle / MovementPattern / Equipment to First-Class KG Nodes with Typed Edges](../tasks/completed/091-kg-muscle-equipment-pattern-nodes.md)
- [x] [TASK-092: Eliminate Double-Traversal in retrieval_graph.assemble](../tasks/completed/092-fix-retrieval-double-traversal.md)
- [x] [TASK-093: Shared Neo4j Driver Singleton (connection pooling)](../tasks/completed/093-neo4j-driver-singleton.md)

## Phase 3: Frontend Completion

> Missing UI surfaces required by the candidate-assessment-main dashboard spec.

- [x] [TASK-094: Interactive Exercise-Exclusion & Equipment-Filter Controls (New Workout)](../tasks/completed/094-workout-exclusion-filter-ui.md)
- [x] [TASK-095: Image Upload & Display in Coach Copilot Chat](../tasks/completed/095-coach-chat-image-support.md)
- [x] [TASK-096: Message-Pattern & 4-Week Comparison Charts (Coach Dashboard)](../tasks/completed/096-coach-message-charts.md)
- [x] [TASK-097: Coach Member List & Switcher](../tasks/completed/097-coach-member-switcher.md)
- [x] [TASK-098: Session Duration / Time-Window Field (New Workout)](../tasks/completed/098-workout-duration-field.md)

## Phase 4: Polish

> Data coverage, documentation, and type hygiene. Finish these before final submission.

- [x] [TASK-099: Seed Rich Member Context for All Personas (not just Jordan Rivera)](../tasks/completed/099-seed-multi-persona-context.md)
- [x] [TASK-101: Add kg_result to Exported ChatMessage Type](../tasks/completed/101-fix-chatmessage-kg-result-type.md)
- [x] [TASK-102: Visual Architecture Diagrams (Layered Mermaid, ≤7 nodes each)](../tasks/completed/102-visual-architecture-diagrams.md)
- [x] [TASK-103: Expose Biomarker & Lab-Result KG Nodes to Coach AI Retrieval](../tasks/completed/103-biomarker-kg-retrieval.md)
- [x] [TASK-104: Expose Coach–Member Chat History KG Nodes to Coach AI Retrieval](../tasks/completed/104-chat-history-kg-retrieval.md)

## Notes

Gap assessment source: `/Users/davidtaylor/.claude/plans/atomic-wishing-biscuit.md` (produced by `/now` on 2026-06-07). All 16 items were materialized into task files 086–101 via `/task-add` on 2026-06-07.
Updated 2026-06-08: 3 additional gaps added (visual diagram, biomarkers/labs KG schema, chat history as KG nodes) from second gap audit.
