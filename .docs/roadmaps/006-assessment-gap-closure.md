# Roadmap 006: Assessment Gap Closure

> Close every gap identified in the 2026-06-07 assessment audit so the repo is submission-ready for all three assessments.

- **Status**: active
- **Created**: 2026-06-07
- **Last updated**: 2026-06-07 (task 089 completed)
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

- [ ] [TASK-090: Runtime 3-Pass Concept Resolver (exact → fuzzy → embedding)](../tasks/090-concept-resolver-3pass.md)
- [ ] [TASK-091: Promote Muscle / MovementPattern / Equipment to First-Class KG Nodes with Typed Edges](../tasks/091-kg-muscle-equipment-pattern-nodes.md)
- [ ] [TASK-092: Eliminate Double-Traversal in retrieval_graph.assemble](../tasks/092-fix-retrieval-double-traversal.md)
- [ ] [TASK-093: Shared Neo4j Driver Singleton (connection pooling)](../tasks/093-neo4j-driver-singleton.md)

## Phase 3: Frontend Completion

> Missing UI surfaces required by the candidate-assessment-main dashboard spec.

- [ ] [TASK-094: Interactive Exercise-Exclusion & Equipment-Filter Controls (New Workout)](../tasks/094-workout-exclusion-filter-ui.md)
- [ ] [TASK-095: Image Upload & Display in Coach Copilot Chat](../tasks/095-coach-chat-image-support.md)
- [ ] [TASK-096: Message-Pattern & 4-Week Comparison Charts (Coach Dashboard)](../tasks/096-coach-message-charts.md)
- [ ] [TASK-097: Coach Member List & Switcher](../tasks/097-coach-member-switcher.md)
- [ ] [TASK-098: Session Duration / Time-Window Field (New Workout)](../tasks/098-workout-duration-field.md)

## Phase 4: Polish

> Data coverage, documentation, and type hygiene. Finish these before final submission.

- [ ] [TASK-099: Seed Rich Member Context for All Personas (not just Jordan Rivera)](../tasks/099-seed-multi-persona-context.md)
- [ ] [TASK-100: Document OPE & COPPER Ontology Decisions (used vs omitted, with rationale)](../tasks/100-document-ope-copper-ontologies.md)
- [ ] [TASK-101: Add kg_result to Exported ChatMessage Type](../tasks/101-fix-chatmessage-kg-result-type.md)

## Notes

Gap assessment source: `/Users/davidtaylor/.claude/plans/atomic-wishing-biscuit.md` (produced by `/now` on 2026-06-07). All 16 items were materialized into task files 086–101 via `/task-add` on 2026-06-07.
