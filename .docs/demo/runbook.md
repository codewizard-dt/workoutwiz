# Demo Run Book — Workout Wiz

**Audience**: Recruiting engineers / AI engineering assessors  
**Duration**: 2–3 minutes  
**Last updated**: 2026-06-11

---

## Hub Architecture

```mermaid
flowchart LR
    User([User / Chat UI])

    subgraph HUB["Hub StateGraph"]
        direction TB
        ROUTER{{"router\nwith_structured_output\nintent + confidence"}}
        COACH["coach\nfitness Q&A"]
        LOG["workout_log\nfuzzy matching"]
        KG["knowledge_graph\nNeo4j GraphRAG"]
        CLARIFY["clarification\nFALLBACK / conf < 0.6"]
        ROUTER -->|COACH| COACH
        ROUTER -->|WORKOUT_LOG| LOG
        ROUTER -->|KNOWLEDGE_GRAPH| KG
        ROUTER -->|FALLBACK / low conf| CLARIFY
    end

    subgraph KGP["KG Pipeline · Neo4j"]
        direction TB
        RETRIEVAL["retrieval\ninjury SNOMED · vector · prefs"]
        GEN["generation\nwith_structured_output"]
        SAFETY["safety gate\nhard-filter contraindicated\npost-LLM"]
        RETRIEVAL -->|ContextSlice| GEN --> SAFETY
    end

    AUDIT[["audit_log\nevent · route · latency · tokens\nGET /chat/audit/{session_id}"]]

    User -->|POST /chat/| ROUTER
    KG --> RETRIEVAL
    HUB -.->|per-node audit| AUDIT
    KGP -.-> AUDIT
```

---

## Knowledge Graph Schema

Node types and relationships in the Neo4j coaching graph. The SNOMED-grounded nodes (`Disorder`, `BodyStructure`) are frozen at build time from `backend/data/snomed_subset.json`.

```mermaid
flowchart LR
    Member["Member\nid · goals\nequipment_available"]
    Injury["Injury\nname · severity\naffected_joints · status"]
    Disorder["Disorder\nsnomed_code · label"]
    BS["BodyStructure\nsnomed_code\ncatalog_term"]
    Exercise["Exercise\nid · joints_loaded\npriority_tier · embedding"]
    WS["WorkoutSession\nstarted_at · phase"]

    Member -->|HAS_INJURY| Injury
    Member -->|RATED| Exercise
    Member -->|PERFORMED| WS
    Injury -->|MAPS_TO_DISORDER| Disorder
    Disorder -->|FINDING_SITE| BS
    BS -->|"PART_OF*0.."| BS
    Exercise -->|MAPS_TO| BS
    WS -->|INCLUDED| Exercise
```

---

## SNOMED Safety Traversal

The contraindication filter follows this path deterministically through graph structure — no string comparison, no prompt instruction. A post-LLM `safety_gate_node` hard-filters any exercise whose ID appears at the end of this traversal.

```mermaid
flowchart LR
    M["Member"] -->|HAS_INJURY| I["Injury\nleft knee tendinopathy"]
    I -->|MAPS_TO_DISORDER| D["Disorder\nSNOMED 15637231000119107"]
    D -->|FINDING_SITE| BS1["BodyStructure\npatellar tendon"]
    BS1 -->|PART_OF| BS2["BodyStructure\nknee joint"]
    E["Exercise\nBarbell Squat"] -->|MAPS_TO| BS2
    E -.->|excluded by safety gate| GATE(["⛔ filtered from response"])
```

---

## Coach Copilot Pipeline

A second, **coach-facing** surface at `/coach` (separate from the member hub). It assembles the full member context from Neo4j and answers the human coach's questions grounded in that context only — every answer carries graph-cited `grounded_facts` pills. Endpoints: `/coach/members`, `/coach/brief`, `/coach/chat`.

```mermaid
flowchart LR
    UI["Coach View (/coach)\nmember switcher · brief · copilot"]
    BRIEF["GET /coach/brief\nchurn · adherence · goals · injuries"]
    CHAT["POST /coach/chat\ngrounded copilot"]
    NEO["Neo4j member context\ngoals · injuries · adherence\nbiomarkers · labs · workouts · messages"]
    LLM["ChatAnthropic (Haiku)\nsystem: answer from context ONLY"]
    OUT["reply + grounded_facts\ngraph-cited pills"]

    UI --> BRIEF --> NEO
    UI --> CHAT --> NEO
    NEO --> LLM --> OUT --> UI
```

---

## Setup (pre-demo, do not narrate)

- [ ] Valid `ANTHROPIC_API_KEY` in root `.env`
- [ ] `make dev` — frontend :5173, backend :8000, postgres :5433
- [ ] Neo4j running if demonstrating KG path: `docker compose up -d neo4j`
- [ ] Browser open at `http://localhost:5173`, chat page visible (log in first)
- [ ] Coach Copilot needs Neo4j seeded with member context (Jordan Rivera demo member)
- [ ] Terminal ready for `curl` audit command

**Fallback**: If stack is down, use Swagger at `http://localhost:8000/docs`

---

## Script

### Hook *(~15 s)*

> "Most fitness apps make you pick a mode before you type. Workout Wiz skips that entirely — you send one natural-language message and a language model decides what kind of request it is using structured output, not a regex."

---

### Step 1 — COACH route *(~25 s)*

**Prompt**: `How many rest days should I take per week for hypertrophy?`

**Action**: Type the prompt in the chat UI and submit.

> "Routed to COACH, confidence 0.97. The coaching sub-graph generates a grounded answer — it can only reference exercises in the 50-exercise dataset. Notice the RouteBadge in the UI: green for COACH."

**Expected result**: A substantive coaching answer; RouteBadge shows `COACH · 0.97`

---

### Step 2 — WORKOUT_LOG *(~25 s)*

**Prompt**: `I just did 3 sets of 10 bench press at 135 lbs and a 20-minute run.`

**Action**: Type and submit.

> "Routed to WORKOUT_LOG. The logger fuzzy-matches 'bench press' to the dataset entry, extracts sets, reps, and weight, and returns a structured JSON log. If match confidence is low it reports it explicitly rather than silently accepting the wrong exercise."

**Expected result**: Structured JSON log with resolved exercise ID, sets, reps, weight

---

### Step 3 — KNOWLEDGE_GRAPH workout generation + injury safety *(~30 s)*

**Prompt**: `I have a bad knee and a bad shoulder. Build me a workout that avoids aggravating either injury.`

**Action**: Type and submit.

> "Routed to KNOWLEDGE_GRAPH, confidence 0.99 — every 'build me a workout' request lands here, and the router picks it over COACH on injury context alone. The retrieval sub-graph traverses Neo4j: member profile (including available equipment), then injury nodes via SNOMED CT codes through MAPS_TO_DISORDER → FINDING_SITE → PART_OF edges. That produces a hard exclusion list of exercise IDs — 21 exercises in this run. The generation graph assembles a warmup/main/cooldown plan, then a safety gate node hard-filters the LLM output against that exclusion list after generation. The filter is code, not a prompt. Each recommended exercise carries a SNOMED-grounded provenance trace you can read: disorder code, finding site, graph path."

**Expected result**: Warmup/main/cooldown plan avoiding knee and shoulder loading; provenance objects on each recommendation; N exercises excluded stated in response

---

### Step 4 — FALLBACK *(~15 s)*

**Prompt**: `What's the best recipe for banana bread?`

**Action**: Type and submit.

> "FALLBACK, confidence 0.99. Out-of-scope, no crash, polite deflection."

**Expected result**: RouteBadge shows `FALLBACK · 0.99`; message says system handles fitness only

---

### Step 5 — Coach Copilot (coach-facing) *(~25 s)*

**Action**: Navigate to `/coach`. Pick a member in the switcher, then click the **"How's adherence trending?"** quick-prompt.

> "Switch personas. This is the coach-facing copilot — separate from the member hub. The morning brief pulls from Neo4j: churn risk, adherence, goals, injuries. When I ask about adherence the copilot answers grounded *only* in this member's graph context. The grounded-facts pills you see are facts pulled from the graph — the coach can trust and repeat them."

**Expected result**: Brief dashboard (churn risk badge, adherence bars, goals, injuries); chat reply citing actual adherence numbers; `grounded_facts` pills rendered beneath the reply

---

### Step 5b — HITL Draft Review *(~25 s)*

**Action**: Still on `/coach`. Trigger a nudge via the nudge button for the selected member. The **Pending Drafts** panel should appear with the new draft at `status: draft`.

1. Edit the body text (the "Save Edit" button appears).
2. Save the edit — draft resets to `draft`.
3. Click **Approve** — `status` flips to `approved`.
4. Click **Send** — `status` becomes `sent` and the card disappears.

> "Before any AI-generated nudge reaches a member, it goes through this HITL gate. The coach sees the draft body and the grounded-on facts that triggered it, can rewrite the text, and must explicitly approve before Send becomes active. Try to send without approving — the API returns 409. Editing an already-approved draft resets it to draft so re-approval is required. This state machine is enforced in the API, not just the UI."

**Expected result**: Draft card cycles through `draft → approved → sent`; Send button disabled until approved; card disappears after sending; panel hidden when no pending drafts remain

---

### Step 6 — Audit trail *(~20 s)*

**Action**: Run in terminal:
```bash
curl http://localhost:8000/chat/audit/<SESSION_ID> | python3 -m json.tool
```

> "Every message in this session is in the audit log — event name, model, route, confidence, latency in milliseconds, token counts. This is the data you'd ship to Prometheus or Datadog to monitor routing accuracy and detect drift."

**Expected result**: JSON array with one entry per agent node per message; latency_ms and tokens_in/out populated

---

### Wrap *(~15 s)*

> "One conversational interface, four routing paths — each a separate LangGraph sub-graph. LLM structured output does the routing. The injury safety gate is code, not a prompt. A coach-facing copilot answers grounded only in the member's graph. And every AI nudge goes through a HITL gate enforced in the API. Full audit trail per session. The README covers production scaling, failure modes, and evaluation strategy."

---

## Timing Guide

| Section | Target |
|---------|--------|
| Hook | 15 s |
| Step 1 — COACH | 25 s |
| Step 2 — WORKOUT_LOG | 25 s |
| Step 3 — KNOWLEDGE_GRAPH | 30 s |
| Step 4 — FALLBACK | 15 s |
| Step 5 — Coach Copilot | 25 s |
| Step 5b — HITL Draft Review | 25 s |
| Step 6 — Audit | 20 s |
| Wrap | 15 s |
| **Total** | **~2 min 55 s** |

---

## Contingency Notes

- **If LLM is slow**: Use fallback prompts below; the demo transcript in the README shows expected output verbatim
- **If Neo4j is down**: Skip Step 3; substitute "KNOWLEDGE_GRAPH is also implemented — the README shows a live trace with 21 exercises excluded via SNOMED traversal"
- **If asked about the 66% scenario-suite pass rate**: Honest answer — those test cases require the full Neo4j stack or exercise the LLM-dependent no-results recovery path; they are documented known gaps, not regressions
- **If asked about Assessment 2**: GraphRAG pipeline (retrieval sub-graph, vector similarity, SNOMED traversal, safety gate, preference feedback) is implemented; richer member-context ingestion (biomarkers, HRV) is the main gap
- **If draft doesn't appear after nudge**: Nudge may not have Neo4j member context; use the smoke-test `curl` from task 110 to create a draft manually, then demo the approval flow in the UI

---

## Fallback Prompts

| Route | Backup prompt |
|-------|---------------|
| COACH | "How many sets per muscle group for hypertrophy?" |
| WORKOUT_LOG | "I just did 3 sets of 10 squat at 225 lbs." |
| KNOWLEDGE_GRAPH | "Give me a 45-minute full-body strength workout with dumbbells." |
| KNOWLEDGE_GRAPH (injury) | "Build a lower body session that avoids knee stress." |
| FALLBACK | "What's the capital of France?" |

---

## Key URLs

| Resource | URL |
|----------|-----|
| Chat UI (member hub) | http://localhost:5173/chat |
| Coach Copilot | http://localhost:5173/coach |
| Backend Swagger | http://localhost:8000/docs |
| Health check | http://localhost:8000/healthz |
| Audit log | http://localhost:8000/chat/audit/{session_id} |
| KG recommend | POST http://localhost:8000/kg/recommend |
| KG explain | POST http://localhost:8000/kg/explain |
| Coach brief / chat | GET /coach/brief · POST /coach/chat |
| Coach drafts | GET /coach/draft · POST /coach/draft · PATCH /coach/draft/{id} |

---

## Requirements Coverage

| # | Requirement | Source | Status |
|---|-------------|--------|--------|
| REQ-01 | Hub routes via `with_structured_output`, not regex | PRD-001 AC-1.1 | **Covered** — `RouteDecision` structured output |
| REQ-02 | COACH intent → coaching sub-agent, grounded answer | PRD-001 US-1 | **Covered** — Step 1 |
| REQ-03 | Workout generation produces warmup/main/cooldown plan | PRD-001 AC-2.2 | **Covered** — KNOWLEDGE_GRAPH generation path (Step 3) |
| REQ-04 | All exercises traceable to exercises.json | PRD-001 AC-2.3 | **Covered** — generation chooses from `safe_exercises` only; safety gate validates IDs |
| REQ-05 | Equipment/time constraints reflected in plan | PRD-001 AC-2.4 | **Covered** — KG retrieval scopes candidates to `Member.equipment_available` (Step 3) |
| REQ-06 | WORKOUT_LOG → structured JSON with fuzzy-matched ID | PRD-001 AC-3.2–3.3 | **Covered** — Step 2 |
| REQ-07 | Low-confidence inputs → clarification, not misroute | PRD-001 AC-4.1 | **Covered** — clarification node at confidence < 0.6 |
| REQ-08 | Edge cases → user-facing message, no crash | PRD-001 AC-4.2 | **Covered** — Step 4 FALLBACK + global handler |
| REQ-09 | README production evaluation section | PRD-001 AC-4.3 | **Covered** — README "Production Evaluation" |
| REQ-10 | Injury contraindication hard-filter (not prompt) | PRD-002 AC-1.2 | **Covered** — Step 3 safety gate |
| REQ-11 | Graph-traceable explainability per recommendation | PRD-002 AC-2.1 | **Covered** — SNOMED provenance objects |
| REQ-12 | Preference feedback writeback | PRD-002 US-4 | **Covered** — FeedbackForm → POST /kg/feedback |
| REQ-13 | Coach-facing copilot surfaces member context (injuries, adherence, goals) grounded in the graph | PRD-002 US-3 | **Covered** — Step 5 `/coach` brief + grounded chat |
| REQ-14 | Copilot distinguishes graph-grounded facts from inferred context | PRD-002 US-3 AC-3 | **Covered** — `grounded_facts` pills + "answer from context ONLY" system prompt |
| REQ-15 | AI-generated nudges require human approval before reaching a member (HITL gate) | Task 110/111 | **Covered** — `draft → approved → sent` state machine enforced in API (409 on unapproved send); Step 5b |

**Gaps**: None against PRD-001 or PRD-002 core acceptance criteria.

**Undocumented features** (implemented but without a PRD requirement):
- AgentTrace UI component — per-step tool call breakdown in the chat UI
- RouteBadge — colour-coded route + confidence badge on each chat bubble
- EnjoymentScale / FeedbackForm — 1–5 star rating written back to Neo4j
- PhaseTable — warmup/main/cooldown structured table rendered in chat
- `/kg/audit/{member_id}` — KG-layer audit log separate from hub audit
- Eval suite (golden 11/11, scenarios 27/41, replays 5/5) with `make eval-stats` trend tracking
- PendingDraftsPanel — in-UI draft review with edit / approve / send flow; polls every 10 s for new drafts
