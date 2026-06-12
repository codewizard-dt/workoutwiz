---
marp: true
paginate: true
size: 16:9
style: |
  :root {
    --bg: #0d1117;
    --fg: #c9d1d9;
    --muted: #8b949e;
    --accent: #58a6ff;
    --amber: #d29922;
    --success: #3fb950;
    --danger: #f85149;
    --border: #30363d;
    --surface: #161b22;
  }
  section {
    background: var(--bg);
    color: var(--fg);
    font-family: 'DM Sans', -apple-system, system-ui, sans-serif;
    padding: 48px 56px;
  }
  h1 { color: #ffffff; font-size: 2.2rem; letter-spacing: -0.02em; margin: 0 0 0.5rem; }
  h2 { color: #ffffff; font-size: 1.5rem; letter-spacing: -0.01em; margin: 0 0 0.4rem; }
  h3 { color: var(--accent); font-size: 1rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 1rem; }
  p, li { color: var(--fg); font-size: 0.95rem; line-height: 1.65; }
  code { background: var(--surface); color: var(--accent); padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
  ul { padding-left: 1.4rem; }
  li { margin-bottom: 0.35rem; }
  .dim { color: var(--muted); font-size: 0.8rem; }
  strong { color: #ffffff; }
  hr { border: none; border-top: 1px solid var(--border); margin: 1.2rem 0; }
  section.lead h1 { font-size: 3rem; }
  section.lead p { font-size: 1.1rem; color: var(--muted); }
  table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
  th { color: var(--muted); border-bottom: 1px solid var(--border); padding: 6px 10px; text-align: left; font-weight: 600; }
  td { padding: 5px 10px; border-bottom: 1px solid var(--border); }
---

<!-- _class: lead -->

# Workout Wiz

**UI Walkthrough** — Every page, every requirement

LangGraph multi-agent · Neo4j knowledge graph · FastAPI · React

<!--
"This is Workout Wiz — three fitness workflows in one interface: ask coaching questions, generate injury-aware workout plans, and log sessions conversationally. A single AI hub decides which agent handles each message using LLM structured output, never a regex. Let me walk through every screen."
-->

---

## The Problem

> Most fitness apps make you **pick a mode** before you type.

Workout Wiz skips that entirely — one natural-language message, one hub that routes automatically.

| Workflow | What you say | Agent |
|----------|-------------|-------|
| Ask a question | "How do I improve squat depth?" | COACH |
| Log a session | "3×10 bench press at 185 lbs" | WORKOUT_LOG |
| Build a plan | "45 min upper body, dumbbells" | WORKOUT_GENERATE_KG |
| Out of scope | "Best banana bread recipe?" | FALLBACK |

<!--
"The hub uses with_structured_output — not regex, not keyword matching. The LLM returns a typed RouteDecision object. Let's see it in the UI."
-->

---

## Landing Page `/`

**Hero** — full-bleed image, bottom-anchored copy, glass nav

Feature grid highlights the three capabilities:
- Multi-agent routing
- Injury-aware recommendations
- Conversational logging

CTAs: **Find Your Coach** → `/register` · **Sign in** → `/login`

Authenticated users auto-redirect to `/chat`

*Extra feature — not a PRD requirement; sets product context for the assessor*

<!--
"The landing page establishes the product context. In production this would be the public marketing surface."
-->

---

## Login `/login`

Email + password form → JWT via `fastapi-users`

- Inline error state (no page reload)
- Gradient submit button disabled while pending
- "Need an account? Register" link → `/register`
- **On success**: navigates directly to `/chat`

*REQ-AUTH: JWT authentication — production requirement*

<!--
"Standard JWT auth. Successful login drops the user straight into the AI Coach chat."
-->

---

## AI Coach `/chat` — One Page, All Three Routes

The chat page is the member's **primary interface**.

**Prompt chips** — always-visible, one-tap queries:

- "What exercises suit my injuries?"
- "Log 3×10 decline bench press at 185"
- "Bench press form tips"
- "How do I improve my squat depth?"

**Right sidebar** — recent workouts with quick-navigate links

**Composer** — auto-growing textarea, `Enter` to send, `✕` to clear

<!--
"The chat page is where all three routing paths converge. Prompt chips let users one-tap common queries."
-->

---

## COACH Route

**Prompt**: *"Bench press form tips"*

**RouteBadge** `COACH · 97%` (green)

- Dispatched to the coaching sub-graph
- Response rendered as **Markdown** — never raw JSON
- **AgentTrace** accordion → "Show reasoning"
  - Per step: agent name · confidence · latency ms

---

**REQ-01** Hub routes via `with_structured_output` ✓
**REQ-02** Coaching answer grounded in dataset ✓
**REQ-03** Human-readable markdown response ✓

<!--
"The RouteBadge shows COACH at 97% confidence. Click 'Show reasoning' to expand the agent trace — each node name, its confidence, and latency in milliseconds."
-->

---

## WORKOUT_LOG Route

**Prompt**: *"Log 3×10 decline bench press at 185"*

**RouteBadge** `Logged · 94%` (blue)

- Logger sub-agent fuzzy-matches "decline bench press" → correct dataset entry
- Returns structured log: exercise name · sets · reps · weight · resolved exercise ID
- Low-confidence match → explicit indicator, not silent acceptance

---

**REQ-07** Structured JSON log with fuzzy-matched ID ✓
**REQ-08** Uncertain match surfaces confidence indicator ✓

<!--
"The WORKOUT_LOG agent fuzzy-matches the natural language exercise name to the 50-exercise dataset."
-->

---

## WORKOUT_GENERATE_KG + Injury Safety

**Prompt**: *"Build me a 30-min upper body session — I have a shoulder injury"*

**RouteBadge** `Injury-Screened · 99%` (amber)

Amber provenance banner:
> Injury-screened — Medical knowledge graph · SNOMED CT contraindication gate

- Neo4j traversal builds a hard exclusion list of exercise IDs
- Safety gate filters LLM output **in code** — not a prompt instruction
- Each exercise card: name · sets×reps · reasoning text · inline FeedbackForm

---

**REQ-KG-01/02/05** Member context · no contraindicated exercises · structured plan ✓

<!--
"Contraindicated exercises are blocked by a code-level safety gate after LLM generation — not by a prompt instruction."
-->

---

## FALLBACK Route

**Prompt**: *"What's the best recipe for banana bread?"*

**RouteBadge** `Clarifying · 99%` (red)

- Out-of-scope → polite clarification message
- No crash, no exception, no silent misroute

---

**REQ-09** Ambiguous/out-of-scope → user-facing message ✓
**REQ-10** Edge cases → message, not unhandled exception ✓

<!--
"FALLBACK fires for anything outside fitness scope. 99% confidence. Polite deflection. No crash."
-->

---

## New Workout Builder `/workouts/new`

**Setup card** chips auto-compose the chat textarea:

| Control | Options |
|---------|---------|
| Duration | 15 / 30 / 45 / 60 min |
| Intensity | Challenging / Easy |
| Focus | Upper body / Lower body |
| Equipment | Searchable multi-select picker |
| Exclude | Searchable exercise exclusion picker |

**Dual-pane**: AI chat (left) · live sequence editor (right)

AI returns draft → **"Use this workout"** → PhaseTable fills → **"Save workout"**

<!--
"The setup chips compose a natural-language request you can still edit. The sequence panel shows the live draft. Save commits to Postgres."
-->

---

## Workout Builder Requirements

**REQ-04** Warmup / main / cooldown structure → PhaseTable renders each phase ✓

**REQ-05** Every exercise traceable to exercises.json by ID → `exercise_id` on each set ✓

**REQ-06** Equipment/time constraints reflected → chips compose the constraint text ✓

---

**Extra features beyond PRD:**
- Duration / intensity / focus / equipment / exclude chips
- Auto-composing textarea (mirrors setup state in real time)
- Draft persisted in `localStorage` — survives navigation
- Dual-pane split layout with independent scroll

<!--
"All three WORKOUT_GENERATE requirements are visible here."
-->

---

## Workout Detail `/workouts/:id`

**PhaseTable** — warmup / main / cooldown with exercise, sets, reps, weight

**Feels (enjoyment):**
- 1–5 emoji scale (frown → smile)
- Auto-saves on change with **300 ms debounce** — no submit button needed

**Note** textarea — same debounced auto-save → shows "✓ Saved"

**FeedbackForm** — compact inline on each set row → ratings write back to Neo4j as preference edges

*Extra features: debounced auto-save, emoji rating, per-exercise inline feedback, KG preference feedback loop*

<!--
"The detail page is where athletes review their session. The auto-save means nothing is lost even if they close the tab mid-thought."
-->

---

## Workouts List `/workouts`

Table: **Date · Sets · Type · Feels · Actions**

- `STRENGTH` badge · `CARDIO` badge
- Emoji face icon from the enjoyment rating
- **Delete** → `DeleteConfirmModal`: confirms permanent removal
- Empty state → "New Workout" + "Ask the coach" CTAs

*Extra features: type badge, enjoyment icon in list, modal-guarded delete, contextual empty state*

<!--
"The workouts list. Delete is protected by a confirmation modal."
-->

---

## Exercise Library `/exercises`

**Stat tiles**: 50 exercises · N muscle groups · N equipment types

**Filter rail** — multi-select chips: muscle groups · movement patterns · equipment

**"Safe for me" toggle:**
- Activates SNOMED-grounded safety lens
- Injury banner: "Personalized for your N active injuries"
- Flagged exercises show red shield indicator
- "Flagged for you" stat tile appears

**Exercise detail drawer** → bilateral pair · muscle groups · equipment · feedback form

**REQ-KG-01/02** Contraindications surfaced in the UI ✓

<!--
"The safety lens wires the same Neo4j knowledge graph that powers the chat."
-->

---

## Coach View `/coach`

Separate surface for the professional coach — own auth + subdomain in production.

**Member switcher** — pill buttons, auto-selects first member

**Sticky member header**: name · age · tier · goals · churn risk pill

**Morning brief** — alert/celebrate task cards from Neo4j

**Adherence chart** — 4 weeks + trend arrow (improving / declining)

**Injury + Equipment cards** — pulled from member's graph nodes

<!--
"The coach view is a completely different AI system from the member hub."
-->

---

## Coach View — Copilot + Analytics

**Action items** · **Message pattern chart** · **Weekly comparison chart**

**Coach copilot chat** (bottom):
- Quick-prompt chips: "How's adherence trending?" · "Draft a nudge"
- **Image attachment** — attach a photo to a message
- Grounded replies carry amber **grounded_facts** pills — graph-cited facts

---

**REQ-KG-03** Member context surfaced ✓
**REQ-KG-06** Graph-traceable explanations via grounded_facts ✓

<!--
"Every copilot reply is grounded only in this member's Neo4j context. The grounded_facts pills make that explicit."
-->

---

## Architecture

![Architecture](.docs/demo/architecture.svg)

<!--
"The hub is a LangGraph StateGraph. The router node calls with_structured_output. Each intent dispatches to its own sub-graph. The KG pipeline runs Neo4j traversal then a code-level safety gate post-LLM."
-->

---

## Requirements Coverage

| Requirement | UI Evidence | Status |
|-------------|------------|--------|
| COACH routing via `with_structured_output` | RouteBadge green · AgentTrace | ✓ |
| WORKOUT_LOG → structured JSON + fuzzy match | Logged badge · structured reply | ✓ |
| WORKOUT_GENERATE → warmup/main/cooldown | PhaseTable in builder + detail page | ✓ |
| Equipment/time constraints reflected | Setup chips + constraint text | ✓ |
| Ambiguous input → FALLBACK, not crash | Clarifying badge · message | ✓ |
| Injury-aware generation (SNOMED gate) | Amber provenance banner | ✓ |
| Graph-traceable explanations | Per-exercise reasoning text | ✓ |
| Member context (injuries, adherence, goals) | CoachPage brief + injuries card | ✓ |
| `docker compose up` starts full stack | docker-compose.yml at repo root | ✓ |

**Gaps**: None against PRD-001 or PRD-002 core acceptance criteria.

<!--
"All core requirements are visible in the UI. Zero gaps."
-->

---

<!-- _class: lead -->

## What makes this production-ready

- **Safety in code** — SNOMED contraindication gate is a `filter()`, not a prompt
- **Observable by design** — route · confidence · latency_ms on every response
- **Preference learning loop** — FeedbackForm → Neo4j preference edges → future recommendations
- **Grounded, auditable** — grounded_facts pills; audit log per session
- **One command** — `docker compose up` starts the entire stack

*Full production eval strategy in README: metrics, failure modes, health signals*

<!--
"These aren't features bolted on for the demo — they're the architecture."
-->

---

<!-- _class: lead -->

# Demo complete

**Repo**: `github.com/gauntlet/workout-wiz`
**README**: Architecture · Eval suite · Production evaluation section
**Run it**: `docker compose up`

Questions?

<!--
"That's the full UI walkthrough. Questions welcome."
-->
