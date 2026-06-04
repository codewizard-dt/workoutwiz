# PRD 001: Fitness Coaching Multi-Agent System

> A conversational hub that routes fitness questions, workout generation requests, and activity log entries to specialized sub-agents — unifying three distinct workflows behind a single natural-language interface.

- **Status**: draft
- **Created**: 2026-06-03
- **Last updated**: 2026-06-03
- **Owner**: David Taylor
- **Stakeholders**: Recruiting engineer / assessor
- **Tags**: multi-agent, fitness, llm-routing

## Problem Statement

Users currently have no single conversational interface to ask coaching questions, auto-generate workouts, AND log activity in structured form — they juggle separate apps or manual tracking. The system unifies these three workflows behind a natural-language hub, routing each request to the correct specialized agent without the user having to select a mode or structure their input.

## Goals

| # | Goal | Linked Success Metric |
|---|------|-----------------------|
| 1 | Morgan can reach all three coaching workflows through one conversational interface without mode-switching | SM-1 |
| 2 | Generated workouts are grounded exclusively in the provided exercise dataset | SM-2 |
| 3 | Logged exercises are reliably matched to structured dataset entries from natural-language input | SM-3 |
| 4 | The system handles ambiguous, empty, and malformed inputs without crashing | SM-4 |

## Non-Goals (explicit out-of-scope)

| # | Non-Goal | Why excluded |
|---|----------|--------------|
| 1 | Exercises outside the provided 50-exercise dataset | Integrating external exercise APIs or custom exercise creation is out of scope; the demo relies solely on exercises.json |

## Personas

| Persona | Context | Primary goal in this PRD |
|---------|---------|--------------------------|
| **Morgan, the intermediate self-trainer** | Self-directed gym-goer with clear goals and known equipment; works out alone | Seamlessly ask fitness questions, get instant workout plans, and log sessions conversationally without switching apps or reformatting inputs |
| **The recruiting engineer / assessor** | Reviews the submitted public repo to evaluate multi-agent AI engineering skills | Quickly assess routing correctness, LangGraph architecture quality, resilience design, and the candidate's production-readiness thinking |

## User Stories

### US-1. Ask a coaching question

> As **Morgan**, I want to ask a free-text fitness question (e.g. "What muscles does a deadlift work?") so that I receive an accurate, grounded coaching answer without leaving my workout context.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | The hub classifies the input as `COACH` using LLM structured output and dispatches to the coaching sub-agent |
| 2 | The coaching response directly addresses the question without hallucinating exercises or muscle groups not substantiated by the dataset |
| 3 | The response is returned as a human-readable message, not a raw JSON object |

### US-2. Generate a structured workout

> As **Morgan**, I want to describe my available equipment and time budget (e.g. "Build me a 30 min upper body session with dumbbells") so that the system assembles a complete warmup / main / cooldown workout plan using only exercises in the dataset.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | The hub classifies the input as `WORKOUT_GENERATE` using LLM structured output and dispatches to the workout generator sub-agent |
| 2 | The plan is structured into warmup, main, and cooldown sections with sets, reps, and rest periods |
| 3 | Every exercise in the plan can be traced to an entry in exercises.json by ID; no hallucinated exercises appear |
| 4 | Equipment and time constraints stated in the input are reflected in the plan (e.g. dumbbell-only, 30 minutes) |

### US-3. Log a workout conversationally

> As **Morgan**, I want to say "I just did 3x10 bench press at 185 lbs" so that the system parses exercise name, sets, reps, and weight into a structured JSON log entry with a fuzzy-matched exercise ID.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | The hub classifies the input as `WORKOUT_LOG` using LLM structured output and dispatches to the workout logger sub-agent |
| 2 | The output is a structured JSON object containing exercise name, sets, reps, weight, and a resolved exercise ID from exercises.json |
| 3 | The exercise name from natural language (e.g. "bench press") fuzzy-matches to the correct dataset entry (e.g. "Barbell Flat Bench Press") |
| 4 | When fuzzy-matching is uncertain, the system returns a best-match with an explicit confidence indicator rather than silently accepting a wrong match |

### US-4. Graceful handling of ambiguous input and assessor production section

> As **Morgan**, I want ambiguous or unclear inputs to produce an explicit fallback or clarification request so that I am never silently misrouted to the wrong sub-agent.
> As **the recruiting engineer**, I want to read a "How I would evaluate this system in production" section in the README so that I can assess the candidate's operational thinking without a live interview.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| 1 | Inputs with no clear intent (e.g. "Bench press" with no context) trigger an explicit fallback route or a clarification prompt rather than a silent dispatch |
| 2 | Edge-case inputs — empty search results, invalid tool call schemas, and ambiguous intent — produce user-facing messages rather than unhandled exceptions |
| 3 | The submitted README contains a production evaluation section covering at minimum: key metrics to monitor, known failure modes, and signals that the system is healthy |

## Success Metrics

| ID | Signal | Threshold | When measured |
|----|--------|-----------|---------------|
| SM-1 | Routing intent accuracy across COACH / WORKOUT_GENERATE / WORKOUT_LOG / fallback routes | ≥ 90% correct classification on the test suite | At submission |
| SM-2 | Workout exercise grounding rate | 100% of exercises in generated plans traceable to exercises.json | Demo transcript review at submission |
| SM-3 | Fuzzy-match hit rate for exercise logging | ≥ 80% of exercise names in test inputs resolve to a valid exercises.json ID | At submission |
| SM-4 | Edge-case resilience rate | 100% of documented edge cases (empty results, bad schema, ambiguous intent) return a user-facing message with no unhandled exception | At submission |

## Constraints

| # | Constraint | Source |
|---|------------|--------|
| 1 | Implementation stack is Python, LangGraph, and LangChain | Business — assessment specification |
| 2 | Hub routing must use LLM structured output (e.g. `with_structured_output()`), not regex or keyword matching | Technical — assessment specification |

## Assumptions

| # | Assumption | If false, impact |
|---|------------|------------------|
| 1 | An LLM provider API key is available and funded throughout development and demo | Entire system is blocked; no LLM calls can be made |
| 2 | The 50-exercise dataset in exercises.json is representative enough for a complete demo | COACH and WORKOUT_GENERATE responses may have visible gaps; dataset expansion would be required before real-world use |
| 3 | Assessors weight architectural correctness and resilience over feature completeness | The scope tradeoff (a small system that works end-to-end) would need to be reversed |

## Open Questions

_(none at time of authoring)_

## Linked ADRs

> Filled in by `/prd-extract-decisions`. Each row tracks one Architecturally Significant Requirement that became (or will become) an ADR.

| ASR | ADR | Status |
|-----|-----|--------|
| — | — | — |

## Linked Tasks

> Filled in as `/task-add --prd PRD-001` runs. The PRD is delivered when all linked tasks complete.

| Task | Status |
|------|--------|
| — | — |

## Amendments

<!-- Amendments appear here as `## Amendment 1`, `## Amendment 2`, etc. -->
