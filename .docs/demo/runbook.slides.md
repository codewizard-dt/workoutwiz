---
marp: true
paginate: true
size: 16:9
style: |
  section {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    padding: 48px 64px;
  }
  h1 { color: #f0f6fc; font-size: 2.2em; margin-bottom: 0.2em; }
  h2 { color: #58a6ff; font-size: 1.4em; border-bottom: 1px solid #21262d; padding-bottom: 0.3em; }
  h3 { color: #79c0ff; font-size: 1.1em; }
  a { color: #58a6ff; }
  code { background: #161b22; color: #e6edf3; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
  pre { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
  pre code { background: transparent; padding: 0; }
  table { border-collapse: collapse; width: 100%; font-size: 0.85em; }
  th { background: #161b22; color: #79c0ff; padding: 8px 12px; border: 1px solid #30363d; text-align: left; }
  td { padding: 8px 12px; border: 1px solid #30363d; color: #c9d1d9; }
  tr:nth-child(even) td { background: #0d1117; }
  tr:nth-child(odd) td { background: #161b22; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
  .coach { background: #1f4e2b; color: #3fb950; }
  .gen { background: #1c3461; color: #58a6ff; }
  .log { background: #4b2a06; color: #e3b341; }
  .kg { background: #3a1c61; color: #bc8cff; }
  .fallback { background: #2d1717; color: #f85149; }
  footer { color: #484f58; font-size: 0.7em; }
---

<!-- _class: lead -->

# Workout Wiz

### One conversational interface. Five routing paths. Zero mode-switching.

**FastAPI · LangGraph · Neo4j · React**

<!--
"Most fitness apps force you to pick a mode before you type. Workout Wiz removes that entirely — you send one natural-language message and the system decides what kind of request it is. The routing decision is made by a language model using structured output, not a regex."
-->

---

## The Problem

Most fitness apps force users to pick a mode:

> *"Are you asking a question? Generating a workout? Logging a session?"*

Workout Wiz removes that decision entirely.

**You type. The system decides.**

Routing is done by a language model using `with_structured_output` — not a regex, not a keyword list.

<!--
"One conversational interface handles coaching questions, workout generation, activity logging, and injury-aware recommendations. The system figures out which one you need."
-->

---

## Architecture

![Architecture](architecture.svg)

Every message flows through a typed `StateGraph` hub. Sub-agents are **separate graphs** composed into the hub — not inlined functions.

<!--
"The hub is a LangGraph StateGraph with typed state and conditional edges. Each sub-agent — coach, generator, logger, knowledge graph — is a separate compiled graph composed into the hub. That's the assessment spec requirement: not inlined lambdas, actual separate graphs."
-->

---

## Five Routing Paths

| Route | Example input |
|-------|---------------|
| `COACH` | "How many rest days for hypertrophy?" |
| `WORKOUT_GENERATE` | "30-min upper-body session with dumbbells" |
| `WORKOUT_LOG` | "I just did 3×10 bench press at 135 lbs" |
| `KNOWLEDGE_GRAPH` | "Avoid my knee and shoulder injuries" |
| `FALLBACK` | "What's the capital of France?" |

The router emits a `RouteDecision` (intent + confidence). Confidence < 0.6 → **clarification node** asks the user to rephrase — no silent misroute.

<!--
"Five paths. The router node calls the LLM with a structured output schema — RouteDecision with intent and confidence fields. If confidence is below 0.6, a clarification node fires instead of guessing."
-->

---

## COACH

**Prompt**: *"How many rest days should I take per week for hypertrophy?"*

<span class="badge coach">COACH · 0.97</span>

The coaching sub-graph generates a grounded answer using only the 50-exercise dataset. No hallucinated muscle groups or exercises.

**What the assessor sees:**
- Correct route classification using `with_structured_output`
- RouteBadge in the UI shows intent + confidence
- Response addresses the question without fabricating content

<!--
"Routed to COACH, confidence 0.97. The coaching sub-graph generates a substantive answer grounded entirely in the exercise dataset. No hallucinated exercises. Notice the RouteBadge in the UI: green for COACH."
-->

---

## WORKOUT_GENERATE — Equipment Constraint

**Prompt**: *"I only have resistance bands at home. Build me a 30-minute full-body workout."*

<span class="badge gen">WORKOUT_GENERATE · 0.95</span>

Two tools called in sequence:

1. `search_exercises_tool` → filters the dataset to bands + bodyweight only
2. `build_workout_tool` → assembles warmup / main / cooldown, validates every ID

`invalid_ids_skipped: []` — zero hallucinated UUIDs.

The equipment constraint is enforced through **data filtering**, not prompt instruction.

<!--
"Routed to WORKOUT_GENERATE, confidence 0.95. The generator calls two tools: search_exercises_tool filters the 50-exercise Postgres dataset to band and bodyweight exercises only — constraint enforced through data, not prompt instruction. Then build_workout_tool assembles the plan and validates every exercise ID. invalid_ids_skipped is empty — no hallucinated UUIDs."
-->

---

## WORKOUT_LOG — Fuzzy Matching

**Prompt**: *"I just did 3 sets of 10 bench press at 135 lbs and a 20-minute run."*

<span class="badge log">WORKOUT_LOG · 0.93</span>

The logger sub-agent:
- Fuzzy-matches "bench press" → `Barbell Flat Bench Press` (dataset entry)
- Extracts sets, reps, and weight into structured JSON
- Returns a resolved `exercise_id` from exercises.json
- Reports low-confidence matches explicitly — no silent wrong match

<!--
"Routed to WORKOUT_LOG. The logger fuzzy-matches 'bench press' to the dataset entry, extracts sets, reps, and weight, and returns a structured JSON log with the resolved exercise ID. If match confidence is low it reports it rather than silently accepting the wrong exercise."
-->

---

## KNOWLEDGE_GRAPH — Injury-Aware

**Prompt**: *"I have a bad knee and a bad shoulder. Build me a workout that avoids aggravating either."*

<span class="badge kg">KNOWLEDGE_GRAPH · 0.99</span>

The retrieval sub-graph traverses Neo4j via SNOMED CT:

```
Injury("Left knee tendinopathy")
  → MAPS_TO_DISORDER → Disorder (SNOMED 15637231000119107)
  → FINDING_SITE → BodyStructure("Structure of left patellar tendon")
  → PART_OF → BodyStructure("Knee joint structure")
  ← CONTRAINDICATED ← Exercise("Barbell Back Squat")
```

21 exercises excluded. Every decision is **graph-traceable**, not an LLM rationale.

<!--
"Routed to KNOWLEDGE_GRAPH, confidence 0.99. The retrieval sub-graph traverses Neo4j — member profile, then injury nodes through SNOMED CT codes. That produces a hard exclusion list: 21 exercises excluded in this run. Each contraindicated decision carries a full SNOMED-grounded provenance trace."
-->

---

## The Safety Gate

The injury filter runs **after** LLM generation — not as a prompt instruction.

```
LLM generates draft workout
         ↓
safety_gate_node: hard-filter any exercise_id in contraindicated_ids
         ↓
violations_filtered = 0  ← always, in production
```

Even if the model ignores an instruction, **no contraindicated exercise reaches the response.**

This resists prompt-injection bypasses — a deliberate architectural choice.

<!--
"Two injuries, one message. The safety gate runs after the LLM — hard code, not a prompt. Even if the model ignores an explicit instruction, the gate catches it. The response states how many exercises were excluded."
-->

---

## FALLBACK + Observability

**Prompt**: *"What's the best recipe for banana bread?"*

<span class="badge fallback">FALLBACK · 0.99</span> — polite deflection, no crash

**Every message produces a per-node audit entry:**

```json
{
  "event": "router",
  "route": "KNOWLEDGE_GRAPH",
  "confidence": 0.99,
  "latency_ms": 1259,
  "tokens_in": 1376,
  "tokens_out": 113
}
```

```bash
curl http://localhost:8000/chat/audit/{session_id}
```

<!--
"FALLBACK, confidence 0.99. No crash, polite deflection. And every message in this session is in the audit log — event name, model, route, confidence, latency in milliseconds, token counts. This is the data you'd ship to a metrics store to monitor routing accuracy and flag drift."
-->

---

## Eval Suite

| Suite | Cases | Latest | Trend |
|-------|-------|--------|-------|
| **Golden** (critical paths, live API) | 11 | **11/11 (100%)** | 91% → 100% |
| **Scenarios** (coverage matrix, live API) | 41 | 27/41 (66%) | 66% |
| **Replays** (frozen fixtures, no API key) | 5 | **5/5 (100%)** | 100% |

Golden is the hard gate. Scenarios at 66% is an honest number — failing cases require the full Neo4j stack or test known LLM-dependent edge cases. Documented gaps, not regressions.

<!--
"Three suites. Golden is the hard gate — 11 cases covering every routing path and edge case, 100% across nine recorded runs. Scenarios at 66% is honest: those test known gaps in the knowledge graph layer. Replay suite runs in CI without an API key."
-->

---

## Summary

One interface. Five LangGraph sub-agents. One hard safety rule.

| What | How |
|------|-----|
| Routing | `with_structured_output` — never regex |
| Grounding | Every exercise ID validated against exercises.json |
| Safety | Post-LLM hard filter, not a prompt instruction |
| Observability | Per-node audit trail with latency + token counts |
| Honesty | Eval results, known gaps, productionization plan in README |

> `make dev` — full stack in one command.

<!--
"One conversational interface, five routing paths — each a separate LangGraph sub-agent. LLM structured output does the routing. The injury safety gate is a hard code filter, not a prompt instruction. Full audit trail available per session. The README covers production scaling, failure modes, and evaluation strategy."
-->

---

<!-- _class: lead -->

# Questions?

**Repo**: github.com/gauntlet/workout-wiz  
**Demo video**: README → Demo Video  
**Swagger**: `http://localhost:8000/docs`  
**Audit**: `GET /chat/audit/{session_id}`
