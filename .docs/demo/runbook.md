# Workout Wiz — Demo Run Book

**Audience**: Recruiting engineers / AI engineering assessors  
**Duration**: 2–3 minutes  
**Format**: Narrated walkthrough of a running local stack  
**Stack**: FastAPI + LangGraph + Neo4j + Vite/React  

> **Scope note**: This project covers both assessments. Assessment 1 (multi-agent hub) is fully implemented — typed `StateGraph`, separate sub-graphs, structured-output routing, clarification node, fuzzy logger. Assessment 2 (knowledge graph) is partially implemented — the Neo4j GraphRAG pipeline, injury safety gate, vector similarity search, and preference feedback loop are all wired and running; the richer member-context ingestion (biomarkers, HRV, adherence signals) is the main gap. The demo covers both layers.

---

## Hub Architecture

```mermaid
flowchart TD
    User([User / Chat UI]) -->|natural language| HUB

    subgraph HUB["Hub StateGraph"]
        ROUTER["router node\nChatAnthropic.with_structured_output\nRouteDecision → intent + confidence"]
        ROUTER -->|COACH| COACH["coach sub-graph\nFitness Q&A\ngrounded coaching"]
        ROUTER -->|WORKOUT_GENERATE| GEN["workout_gen sub-graph\nsearch_exercises_tool\nbuild_workout_tool"]
        ROUTER -->|WORKOUT_LOG| LOG["workout_log sub-graph\nfuzzy exercise matching\nstructured JSON log"]
        ROUTER -->|KNOWLEDGE_GRAPH| KG["knowledge_graph node\nNeo4j GraphRAG\ninjury-aware recs"]
        ROUTER -->|confidence < 0.6| CLARIFY["clarification node\nask user to rephrase"]
        ROUTER -->|FALLBACK| FB["fallback node\nout-of-scope reply"]
    end

    COACH --> AUDIT
    GEN --> AUDIT
    LOG --> AUDIT
    KG --> AUDIT
    CLARIFY --> AUDIT
    FB --> AUDIT

    subgraph OBS["Observability"]
        AUDIT["audit_log\nper-node: event, model, route\nlatency_ms, tokens_in, tokens_out\nGET /chat/audit/{session_id}"]
    end

    subgraph KGSTACK["Knowledge Graph Stack (Neo4j)"]
        RETRIEVAL["retrieval sub-graph\nmember profile · injury traversal\nvector similarity · preference feedback"]
        SAFETY["safety gate node\nhard-filter contraindicated IDs\nnever overrideable by LLM"]
        EXPLAIN["explainability tool\ngraph-path citation\n'why was X skipped?'"]
        RETRIEVAL --> SAFETY --> EXPLAIN
    end

    KG --> RETRIEVAL
```

---

## Pre-Flight Checklist

Before starting the demo, verify the following:

- [ ] `.env` at repo root contains a valid `ANTHROPIC_API_KEY`
- [ ] Docker is running
- [ ] `make dev` has been run; all three services are up (frontend :5173, backend :8000, postgres :5433)
- [ ] Neo4j is running (if demonstrating the KG path): `docker compose up -d neo4j`
- [ ] Browser is open at `http://localhost:5173`
- [ ] The chat page is visible (log in first if needed — any email/password)
- [ ] Terminal window showing backend logs is ready for showing audit output

**Fallback**: If the full stack is unavailable, the multi-agent demo can be run against the backend alone at `http://localhost:8000` (interactive Swagger UI at `/docs`).

---

## Demo Script

### Hook (15 seconds)

**Spoken line:**  
> "Most fitness apps force you to pick a mode before you type. You open a workout tab, or a log tab, or a Q&A tab. Workout Wiz removes that entirely — you send one natural-language message and the system decides what kind of request it is. The routing decision is made by a language model using structured output, not a regex or keyword list. Let me show you."

**Action:** Browser is on the chat page. Nothing typed yet. Audience can see the prompt chips at the bottom of the input area.

---

### Step 1 — Coaching route (30 seconds)

**Spoken line:**  
> "I'll start with a coaching question."

**Action:** Click the chip "Bench press form tips" — or type manually:

```
How many rest days should I take per week for hypertrophy?
```

**Wait for response (~400–800 ms).**

**Spoken line:**  
> "The hub routed this to the COACH sub-agent. You can see the route badge above the response — COACH, confidence 0.97. The coach graph generates a substantive answer. No hallucinated exercises; all grounding comes from the dataset. Every turn appends an entry to an in-memory audit log — I'll show that at the end."

**What to show:** The response bubble with the route badge. The session ID in the footer.

---

### Step 2 — Workout generation route (45 seconds)

**Spoken line:**  
> "Now workout generation — this is where the tool-call layer runs."

**Type or click chip:**

```
30 min dumbbell workout
```

**Wait for response (~1,500–2,500 ms).**

**Spoken line:**  
> "Routed to WORKOUT_GENERATE, confidence 0.95. The generator sub-agent calls two tools: `search_exercises_tool` queries the 50-exercise Postgres dataset by muscle group and equipment, then `build_workout_tool` assembles the plan into warmup / main / cooldown phases. Every exercise ID in the plan is validated against the dataset — hallucinated UUIDs would land in `invalid_ids_skipped` in the audit log. Notice the response is a structured workout — sets, reps, rest — not a raw JSON blob."

**What to show:** The workout plan in the chat bubble. Phase structure (warmup / main / cooldown).

---

### Step 2b — Equipment constraint (30 seconds)

**Spoken line:**
> "Now let me show the same generator sub-graph with an equipment constraint."

**Type:**

```
I only have resistance bands at home — no barbells, no dumbbells. Build me a 30-minute full-body workout.
```

**Wait for response (~2,000–3,000 ms).**

**Spoken line:**
> "Still WORKOUT_GENERATE, confidence 0.95. The generator passed the equipment constraint to search_exercises_tool, which filtered the 50-exercise dataset down to bands and bodyweight movements only. Every exercise ID in the plan is validated against the DB — invalid_ids_skipped is empty, which means zero hallucinated UUIDs."

**What to show:** The workout plan in the chat bubble. The `invalid_ids_skipped: []` field in the audit log if showing JSON.

---

### Step 3 — Workout log route (30 seconds)

**Spoken line:**  
> "Workout logging — free-form natural language, parsed to structured JSON."

**Type or click chip:**

```
Log 3x10 bench at 185
```

**Wait for response (~1,500–2,500 ms).**

**Spoken line:**  
> "Routed to WORKOUT_LOG. The logger sub-agent fuzzy-matches 'bench' to 'Barbell Flat Bench Press' in the dataset, extracts sets, reps, and weight, and returns a structured JSON log entry with the resolved exercise ID. If the match confidence is low, the system says so rather than silently accepting the wrong exercise."

**What to show:** The log confirmation in the response bubble.

---

### Step 4 — Knowledge Graph / injury-aware route (45 seconds)

**Spoken line:**  
> "This is the power feature — injury-aware, graph-traced recommendations."

**Type:**

```
What exercises suit my injuries?
```

**Wait for response (~2,000–4,000 ms).**

**Spoken line:**  
> "Routed to KNOWLEDGE_GRAPH. The retrieval sub-graph queries Neo4j — member profile, injury nodes, joint/muscle contraindications, workout history, and preference feedback from past sessions. A safety gate node then hard-filters any exercise whose ID appears in `contraindicated_ids`. This filter runs after the LLM generation step, so even if the model ignores the instruction, no contraindicated exercise can reach the response. Each recommended exercise shows the reasoning — a sentence that traces back to the graph path, not a generic LLM rationale."

**What to show:** The exercise cards with reasoning text. If `fallback_used` is true, the yellow warning banner. The FeedbackForm at the bottom of each card (1–5 rating).

---

### Step 4b — Injury trace (45 seconds)

**Spoken line:**
> "Let me show a more pointed example — a user with two injuries."

**Type:**

```
I have a bad knee and a bad shoulder. Build me a workout that avoids aggravating either injury.
```

**Wait for response (~8,000–10,000 ms).**

**Spoken line:**
> "Route is KNOWLEDGE_GRAPH, confidence 0.99. The retrieval sub-graph ran the injury traversal node — you can see that in the audit log at retrieval_injury_traversal, 2 milliseconds. The LLM was given only a safe exercise list and selected movements that minimise joint stress. Then the safety gate ran after the LLM — hard code, not a prompt — and the response explicitly states how many exercises were excluded: five in this case."

**What to show:** The response text that ends with "Note: 5 exercise(s) excluded due to injury constraints." The audit log entries for `retrieval_injury_traversal` and `kg_generation_safety_gate`.

**Key point to call out:** The router chose `KNOWLEDGE_GRAPH` (not `WORKOUT_GENERATE`) because it detected the injury context — that is the structured-output router working correctly.

---

### Step 5 — Fallback route (15 seconds)

**Spoken line:**  
> "And here's what happens when someone goes off-script."

**Type:**

```
What's the best recipe for banana bread?
```

**Wait for response (~300–500 ms).**

**Spoken line:**  
> "FALLBACK, confidence 0.99. The hub recognises this is out of scope and returns a polite deflection — no crash, no silent misroute."

---

### Step 6 — Audit trail (20 seconds)

**Spoken line:**  
> "Every message in this session is captured in the audit log. Let me pull it."

**Action:** Copy the session ID from the chat footer. Run in terminal (or show in Swagger UI):

```bash
curl http://localhost:8000/chat/audit/<SESSION_ID> | python3 -m json.tool
```

**Spoken line:**  
> "Each entry records the event name, model, route, confidence, latency in milliseconds, and token counts. Router p95 target is under 800 ms; sub-agents under 3 seconds. This is the data you'd ship to a metrics store — Prometheus, Datadog, whatever — to monitor routing accuracy and flag when something drifts."

**What to show:** The JSON audit log with multiple entries — one `router` event and one sub-agent event per turn.

---

### Step 6b — Eval stats (20 seconds)

**Spoken line:**
> "The system has an eval suite that runs against the live API. Let me show the trend."

**Action:** Run in terminal:

```bash
make eval-stats
```

**Spoken line:**
> "Three suites. Golden is the hard gate — 11 cases covering every routing path and edge case; 100% across nine recorded runs, trend from 91% up to 100% as the system was tuned. The scenario suite has 41 cases and sits at 66% — that's an honest number; it's testing known gaps in the knowledge graph layer. The replay suite is five frozen fixtures that run without an API key and have been 100% since they were added — those are what run in CI."

**What to show:** The sparkline table in the terminal output.

---

### Close (15 seconds)

**Spoken line:**  
> "To summarise: one conversational interface, five distinct routing paths — COACH, WORKOUT_GENERATE, WORKOUT_LOG, KNOWLEDGE_GRAPH, and FALLBACK — each handled by a separate LangGraph sub-agent. LLM structured output does the routing, not regex. The injury safety gate is a hard code filter, not a prompt instruction. And the full audit trail is available per session for production observability. The README covers production scaling, failure modes, and evaluation strategy for anyone who wants to go deeper."

---

## Timing Summary

| Step | Action | Target time |
|------|--------|-------------|
| Hook | Intro sentence | 15 s |
| 1 | COACH route | 30 s |
| 2 | WORKOUT_GENERATE route | 45 s |
| 2b | Equipment constraint example | 30 s |
| 3 | WORKOUT_LOG route | 30 s |
| 4 | KNOWLEDGE_GRAPH route | 45 s |
| 4b | Injury trace (knee + shoulder) | 45 s |
| 5 | FALLBACK route | 15 s |
| 6 | Audit trail | 20 s |
| 6b | Eval stats (`make eval-stats`) | 20 s |
| Close | Summary | 15 s |
| **Full run** | | **~5 min 10 s** |
| **Trim (drop 2b, 4b, 6b)** | | **~3 min 35 s** |

Steps 2b, 4b, and 6b are the new additions; drop them to hit the original 3-minute mark.

---

## Fallback Prompts (if LLM response is slow or off)

| Intent | Backup prompt |
|--------|---------------|
| COACH | "How many sets per muscle group for hypertrophy?" |
| WORKOUT_GENERATE | "Give me a 45-minute full-body strength workout with dumbbells." |
| WORKOUT_LOG | "I just did 3 sets of 10 squat at 225 lbs." |
| KNOWLEDGE_GRAPH | "Build a lower body session that avoids knee stress." |
| FALLBACK | "What's the capital of France?" |

---

## Key URLs

| Resource | URL |
|----------|-----|
| Chat UI | http://localhost:5173 |
| Backend Swagger | http://localhost:8000/docs |
| Health check | http://localhost:8000/healthz |
| Audit log | http://localhost:8000/chat/audit/{session_id} |
| KG recommend | POST http://localhost:8000/kg/recommend |
| KG explain | POST http://localhost:8000/kg/explain |
| KG audit | GET http://localhost:8000/kg/audit/{member_id} |

---

## Requirements Coverage

| Requirement | Source | Status |
|-------------|--------|--------|
| Hub routes via LLM structured output (not regex) | PRD-001 AC-1.1, CLAUDE.md | Covered — `with_structured_output(RouteDecision)` |
| COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK intents | PRD-001 US-1–4 | Covered |
| KNOWLEDGE_GRAPH intent | PRD-002 US-1 | Covered |
| Workout grounded in exercises.json only | PRD-001 AC-2.3 | Covered — `search_exercises_tool` + `build_workout_tool` |
| Fuzzy exercise matching in logger | PRD-001 AC-3.3 | Covered — logger sub-agent |
| Injury contraindication filtering (hard gate) | PRD-002 AC-1.2 | Covered — `_safety_gate_node` post-LLM filter |
| Graph-traceable explainability | PRD-002 AC-2.1 | Covered — `explain_skipped_exercise` + `/kg/explain` endpoint |
| Edge case resilience (no crash on bad input) | PRD-001 AC-4.2 | Covered — clarification node + global exception handler |
| Per-session audit log with latency + tokens | README production eval | Covered — `audit_log` in hub state, `/chat/audit/{session_id}` |
| Production evaluation README section | PRD-001 AC-4.3 | Covered — README.md "How I Would Productionize This" |
| Preference feedback writeback | PRD-002 US-4 | Covered — FeedbackForm → POST /kg/feedback → Neo4j |
| Single-command stack start | PRD-002 SM-5 | Covered — `make dev` |

**Gaps**: None against PRD-001 or PRD-002 core acceptance criteria.

**Undocumented features** (implemented but not in a PRD):
- AgentTrace component (frontend) — shows per-step tool call breakdown
- RouteBadge component — colour-coded route badge on each chat bubble
- EnjoymentScale + FeedbackForm — 1–5 rating written back to Neo4j
- PhaseTable — warmup/main/cooldown structured table in chat
- `/kg/audit/{member_id}` endpoint — KG-layer audit log separate from hub audit
