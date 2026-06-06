# Roadmap 002: LangGraph Fitness Coaching Multi-Agent System

> Build and wire the LangGraph hub + three specialized sub-agent graphs that power the fitness coaching chat interface, satisfying all assessment requirements for public GitHub submission.

- **Status**: done
- **Created**: 2026-06-04
- **Last updated**: 2026-06-05 (tasks 024, 025, 026, 027, 028, 029, 030, 031, 032 completed; Phase 5 tasks 033–036 created; TASK-035, TASK-036 completed)
- **Owner**: David Taylor
- **Linked PRD**: PRD-001
- **Linked ADRs**: —
- **Tags**: multi-agent, langgraph, fitness

## Goal

When complete, the LangGraph multi-agent hub is operational: a typed `StateGraph` routes user messages to three separate sub-agent graphs (coach, workout generator, workout logger) via LLM structured output with confidence-scored fallbacks, a chat interface with full LLM audit trail (tokens, provider, user ID), and ≥2 critical-path tests passing — ready for public GitHub submission.

## Phase 1: Foundation

> Set up the Python project, install dependencies, and define the shared data contracts before any agent code is written.

- [x] [TASK-019: Python Package Setup for 1-multi-agent](../tasks/completed/019-python-package-setup.md)
- [x] [TASK-020: Install Core Dependencies and Environment Config](../tasks/completed/020-install-core-dependencies.md)
- [x] [TASK-021: Shared Typed State and Route Schema](../tasks/completed/021-shared-state-and-route-schema.md)
- [x] [TASK-022: Exercise Data Loader](../tasks/completed/022-exercise-data-loader.md)

## Phase 2: Hub Agent

> Implement the central StateGraph router with structured-output classification and confidence-gated fallback.

- [x] [TASK-023: Hub StateGraph with Typed State and Explicit Edges](../tasks/completed/023-hub-stategraph.md)
- [x] [TASK-024: Router Node with Structured Output](../tasks/completed/024-router-node.md)
- [x] [TASK-025: Conditional Edge Routing Integration Tests](../tasks/completed/025-conditional-edge-routing.md)
- [x] [TASK-026: Clarification Node Finalization](../tasks/completed/026-clarification-node.md)

## Phase 3: Sub-Agents

> Implement all three sub-agent graphs as separate, composable `StateGraph` instances.

- [x] [TASK-027: Coach Sub-Agent Graph](../tasks/completed/027-coach-sub-agent.md)
- [x] [TASK-028: Workout Generator Sub-Agent](../tasks/completed/028-workout-generator-sub-agent.md)
- [x] [TASK-029: Workout Logger Sub-Agent](../tasks/completed/029-workout-logger-sub-agent.md)

## Phase 4: Chat Interface & Audit Trail

> Wire the hub into a chat-capable FastAPI app with full per-call LLM observability.

- [x] [TASK-030: POST /chat Endpoint with Session Support](../tasks/completed/030-chat-endpoint.md)
- [x] [TASK-031: Minimal HTML/JS Web UI](../tasks/completed/031-web-ui.md)
- [x] [TASK-032: Per-Call LLM Audit Log](../tasks/completed/032-llm-audit-log.md)

## Phase 5: Tests, Demo & Docs

> Prove the system works with tests and a runnable demo, then document production thinking in the README.

- [x] [TASK-033: Critical-Path Test A — Router Intent Classification](../tasks/completed/033-critical-path-router-test.md)
- [x] [TASK-034: Critical-Path Test B — Workout Generator Grounding](../tasks/completed/034-critical-path-generator-test.md)
- [x] [TASK-035: End-to-End Smoke Test (Golden Path per Route)](../tasks/completed/035-e2e-smoke-test.md)
- [x] [TASK-036: README Production Evaluation Section](../tasks/completed/036-readme-production-eval.md)

## Notes

### Low-Confidence Routing Decision (2026-06-04)

When the router's `confidence` field is below 0.6, the hub routes to the clarification node instead of dispatching to a sub-agent. The clarification node returns a natural-language message asking the user to rephrase — no sub-agent is invoked, no silent misroute occurs. This satisfies the assessment requirement for explicit fallback handling and is visible to assessors in the routing audit log.

### Demo Format Decision (2026-06-04)

Runnable demo is a FastAPI-served HTML/JS chat page (`1-multi-agent/demo/`). Assessors can start the system with one command and interact with all three routes in a browser. A static transcript (copy-pasted terminal output or screenshot) is included in the README as a fallback for readers who don't run the demo locally.
