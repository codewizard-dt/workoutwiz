# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Context

This is an **AI engineering take-home assessment** being built as a public GitHub repo. The deliverable is Assessment 1 from `1-multi-agent/ASSESSMENT.md`: a fitness coaching multi-agent system. The full product spec lives in `.docs/prd/001-fitness-coaching-multi-agent.md`.

**Assessors judge**: routing correctness (LLM structured output, not regex), LangGraph architecture quality (typed `StateGraph`, separate sub-agent graphs), resilience (edge cases handled without exceptions), and a production-readiness README section.

---

## Repository Layout

```
1-multi-agent/        Assessment spec and exercises.json dataset (50 exercises)
2-knowledge-graph/    Second assessment (not being implemented)
legacy/               Reference-only: old Node/Express/Mongoose/React app
  client/             Legacy React frontend (CRA + Redux + Semantic UI)
  src/                Legacy Express backend (Mongoose schemas, JWT auth)
.docs/                Planning and spec documents
  prd/                PRD-001: product requirements
  roadmaps/           ROADMAP-001: execution plan
  legacy.md           Full inventory of legacy system (schema, APIs, components)
  guides/             MCP tool rules, task lifecycle, deployment strategy
```

The app itself **does not exist yet** — all application code will be created during implementation.

---

## Planned Stack (from ROADMAP-001 Phase 0 decisions)

**Backend**: FastAPI + SQLAlchemy (async) + Alembic + PostgreSQL  
**Auth**: `fastapi-users` library (JWT)  
**AI/Agents**: LangGraph (`StateGraph`) + LangChain + Python  
**Frontend**: Vite + React + TypeScript + Tailwind CSS + shadcn/ui  
**State**: React Query (TanStack Query) + local `useState` (no Redux)  
**API Client**: Axios  

---

## The Exercise Dataset

`1-multi-agent/exercises.json` — 50 exercises, UUID primary keys. This is the **sole data source** for exercises; no external APIs. Key fields for agents:

- `muscle_groups`, `movement_patterns`, `equipment_required` — used by `WORKOUT_GENERATE` sub-agent for `search_exercises` tool
- `is_reps`, `is_duration`, `supports_weight` — determine valid tracking fields per exercise
- `priority_tier` — programming quality signal (1 = highest priority)
- `is_bilateral`, `bilateral_pair_id` — exercise pairing (left/right sides)

Exercises load once via an Alembic data migration (seed script), not at runtime.

---

## LangGraph Architecture (required by assessment)

The hub agent is a `StateGraph` with **typed state** and **explicit edges** — not a single function. Sub-agents are **separate graphs** composed into the hub (not inlined).

```
Hub StateGraph
  ├── router node       → LLM with_structured_output() → intent: COACH | WORKOUT_GENERATE | WORKOUT_LOG | FALLBACK
  ├── coach node        → coaching sub-agent graph
  ├── workout_gen node  → generator sub-agent graph (tools: search_exercises, build_workout)
  └── workout_log node  → logger sub-agent graph (fuzzy exercise matching → structured JSON)
```

Tools must have **Pydantic input schemas with field descriptions**. Routing must use `with_structured_output()` — never regex or keyword matching.

---

## Database Schema (planned)

Three entities beyond exercises:

| Table | Key columns |
|-------|-------------|
| `users` | `id`, `email`, `hashed_password` (managed by fastapi-users) |
| `workouts` | `id`, `user_id`, `started_at`, `ended_at` |
| `workout_sequences` | `id`, `workout_id`, `phase` (warmup/main/cooldown), `position` |
| `workout_sets` | `id`, `sequence_id`, `exercise_id`, `set_type` (STRENGTH/CARDIO), `reps`, `weight_kg`, `duration_s`, `speed`, `distance`, `calories` |

Not porting from legacy: `gifUrl`, `barWeight`, `weightAssist`.

---

## Design Principles

**YAGNI** — Build what the assessment and PRD require. Don't add configuration flags, extension points, or abstraction layers for hypothetical future needs. Three similar lines are better than a premature abstraction.

**DRY** — Single source of truth for exercise data (PostgreSQL, seeded from `exercises.json`), for schema types (Pydantic models shared between FastAPI validation and LangGraph tool schemas), and for agent logic (sub-agents are graphs composed into the hub — not duplicated inline).

**SOLID** — Each sub-agent graph does one thing (coach, generate, log). Each FastAPI router owns one resource. SQLAlchemy models are persistence-only; business logic lives in service layers, not routes or schemas.

---

## MCP Tool Rules (mandatory — see `.docs/guides/mcp-tools.md`)

| Operation | Required tool | Forbidden |
|-----------|--------------|-----------|
| List directories | `mcp__serena__list_dir` | `ls`, `find`, `tree` via bash |
| Find files | `mcp__serena__find_file` | `find -name`, bash |
| Search code | `mcp__serena__search_for_pattern` | `grep`, `rg` via bash |
| Read code files | `mcp__serena__get_symbols_overview` then `find_symbol` | `Read` on `.py`/`.ts`/`.tsx` etc. |
| Edit code files | Serena symbolic tools or `replace_content` | `Edit` on code files, `sed`, `awk` |
| Read markdown/config | `Read` tool | `cat` via bash |
| Edit markdown/config | `Edit` / `Write` tools | `sed`, `echo >>` |
| Library docs | `mcp__context7__query-docs` | WebSearch/WebFetch |
| Web research | `mcp__brave-search__brave_web_search` (1 req/sec, sequential) | parallel searches |

The shell (`Bash` tool) is for **running programs** only — not for reading or modifying files.

---

## CI / Deployment

`build.yml` — builds and pushes a Docker image to GHCR on every push to `main`. The job is **skipped automatically** until a root-level `Dockerfile` exists. No deploy step is wired yet.

`security.yml` — runs Gitleaks secret scanning.

---

## Planning Documents

All planning lives in `.docs/`. Do not skip these — they contain decisions that would otherwise require re-deriving:

| File | Contains |
|------|----------|
| `.docs/prd/001-fitness-coaching-multi-agent.md` | User stories, acceptance criteria, success metrics |
| `.docs/roadmaps/001-port-legacy-to-modern-stack.md` | Execution plan + all Phase 0 design decisions (auth, DB schema, state management, etc.) |
| `.docs/legacy.md` | Complete inventory of the legacy system: every API endpoint, schema, Redux slice, component |
| `.docs/guides/mcp-tools.md` | MCP tool rules — read before touching any file |
| `.docs/guides/task-lifecycle.md` | How tasks and UAT files move through `.docs/tasks/` |
| `.docs/guides/evals-framework.md` | Evaluation framework for AI systems (5-stage model) |

Use `/primer` at the start of any session to reload Serena memories before doing code work.
