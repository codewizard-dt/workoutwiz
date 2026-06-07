# 099 — Seed Rich Member Context for All Personas (not just Jordan Rivera)

> **Depends on**: none
> **Blocks**: [097-coach-member-switcher](097-coach-member-switcher.md)
> **Parallel-safe with**: [100-document-ope-copper-ontologies](100-document-ope-copper-ontologies.md), [101-fix-chatmessage-kg-result-type](101-fix-chatmessage-kg-result-type.md)

## Objective

Give every seeded persona (16 total in `PERSONAS`) a complete Member Context graph — rich Member profile properties plus `LabResult`, `ChatMessage`, and `AssessmentWorkout` nodes — so the coach copilot (`/coach/brief`, `/coach/chat`) is fully functional for any account, not only the assessment demo member Jordan Rivera (Demo).

## Approach

`backend/app/knowledge_graph/seed.py` already seeds `AdherenceWeek`, `CoachBrief`, `BiomarkerSnapshot`, `Goal`, and `Preference` for all personas via `seed_coaching_context_all()`; the gap is that `seed_assessment_member_context()` (gated to `_ASSESSMENT_MEMBER_EMAIL = "jordan.rivera@workoutwiz.demo"`) is the *only* place that writes rich Member profile props, `LabResult`, `ChatMessage`, and `AssessmentWorkout` nodes — which `_fetch_member_context()` in `backend/app/routers/coach.py` queries (`HAS_LAB_RESULT`, `SENT_MESSAGE`, `HAD_WORKOUT`) and finds empty for the other 15 personas. Lift those four block types into a per-persona generator that produces synthetic, varied data deterministically (driver already seeded with `random.seed(42)` / `Faker.seed(42)` in `main()`), while leaving Jordan Rivera (Demo)'s hand-authored values from `member-context.json` byte-for-byte intact.

## Prerequisites

- [ ] Synthetic data ONLY — no real members, no real PHI. Treat the demo `member-context.json` (header: "Synthetic, fictional sample member … No real person or PHI") as the only source of realistic shapes/ranges.
- [ ] Read the current `seed.py` symbols before editing: `seed_coaching_context_all`, `seed_assessment_member_context`, `PERSONAS`, `_GOAL_TEXT`, `main` (use `mcp__serena__get_symbols_overview` then `find_symbol`).
- [ ] Confirm which node types are still single-member by reading `_fetch_member_context` in `backend/app/routers/coach.py` (it `OPTIONAL MATCH`es `LabResult`, `ChatMessage`, `AssessmentWorkout`, etc.).

---

## Steps

### 1. Generalize rich-context seeding into a per-persona function  <!-- agent: general-purpose -->

- [ ] In `backend/app/knowledge_graph/seed.py`, add a new function `seed_rich_member_context_all(driver, member_map, fake)` that loops over every entry in `PERSONAS` and, for each `member_id = str(member_map[persona["email"]])`, writes the node types currently produced ONLY inside `seed_assessment_member_context`: rich Member profile props (`display_name`, `age`, `sex`, `height_cm`, `weight_kg`, `timezone`, `member_since`, `tier`, `coach_id`), two `LabResult` nodes (`blood_panel` + `dexa_scan` via `HAS_LAB_RESULT`), `ChatMessage` nodes (member + coach turns via `SENT_MESSAGE` / `SENT_COACH_MESSAGE`), and `AssessmentWorkout` nodes (via `HAD_WORKOUT`).
- [ ] Reuse the existing idempotent `MERGE`/`SET +=` Cypher patterns and the deterministic id conventions already in `seed_assessment_member_context` (e.g. `f"{member_id}:labs:blood_panel"`, `f"{member_id}:labs:dexa_scan"`, `uuid.uuid5(uuid.NAMESPACE_URL, f"{member_id}:chat:{i}")`, `uuid.uuid5(..., f"{member_id}:workout:{date}:{title}")`) so re-runs stay stable and do not create duplicates.
- [ ] Do NOT re-emit `AdherenceWeek`, `CoachBrief`, `BiomarkerSnapshot`, `Goal`, or `Preference` here — those are already seeded for all personas by `seed_coaching_context_all()`; only fill the remaining gap to avoid double-writing.
- [ ] Wire the new function into `main()` so it runs after `seed_coaching_context_all(...)` and BEFORE `seed_assessment_member_context(...)`, so the demo member's hand-authored values still win as the final override.

### 2. Synthetic data variety per persona  <!-- agent: general-purpose -->

- [ ] Derive each persona's synthetic profile/labs/biomarker-adjacent values from its existing `PERSONAS` fields (`goals`, `equipment`, `sessions_per_week`, `injuries`) plus seeded `random`/`fake`, so personas differ meaningfully: vary `age`/`sex`/`height_cm`/`weight_kg`, `tier`, lab ranges (LDL/HDL/HbA1c/vitamin D, DEXA body-fat/lean-mass), `AssessmentWorkout` titles+exercises (draw exercise names from the persona's `equipment`), and `ChatMessage` content/cadence.
- [ ] Make `ChatMessage` and `AssessmentWorkout` reflect injury/adherence state already present on the persona (e.g. an active-injury persona references recovery/regression; a high `sessions_per_week` persona shows more completed workouts) so the generated narrative is internally consistent with `seed_coaching_context_all`'s churn/adherence logic.
- [ ] Keep Jordan Rivera (Demo) (`jordan.rivera@workoutwiz.demo`) untouched by the new generator — either skip that email in the loop or rely on the later `seed_assessment_member_context()` override; verify its `LabResult`, `ChatMessage`, and `AssessmentWorkout` values still match `member-context.json` exactly after a full seed.

### 3. Tests / seed run  <!-- agent: general-purpose -->

- [ ] Add a seed-coverage test (e.g. `backend/tests/test_seed_member_context.py`) that, after seeding, asserts EVERY persona email in `PERSONAS` has at least one `CoachBrief` (`HAS_COACH_BRIEF`), `AdherenceWeek` (`REPORTED_ADHERENCE`), `BiomarkerSnapshot` (`HAS_BIOMARKER`), `LabResult` (`HAS_LAB_RESULT`), `ChatMessage` (`SENT_MESSAGE`), and `AssessmentWorkout` (`HAD_WORKOUT`) node linked to its Member.
- [ ] Assert idempotency: running the rich-context seeding twice does not increase node counts for any persona (MERGE on stable ids).

### N. Verification  <!-- agent: general-purpose -->

- [ ] Re-run the seed (`python -m backend.app.knowledge_graph.seed`) and confirm `GET /coach/brief` returns populated `member_name`, `goals`, `injuries`, `morning_tasks`, `churn_risk`, and `adherence_weeks` for at least three different persona accounts (not just the demo member).
- [ ] Spot-check via `_fetch_member_context` (or a direct Cypher query) that a non-demo persona now returns non-empty `labs`, `workouts`, and `chat_messages`, and that Jordan Rivera (Demo)'s context is unchanged.

## Acceptance Criteria

- [ ] All 16 personas in `PERSONAS` have the full Member Context graph (Member profile props + Goal + Preference + AdherenceWeek + CoachBrief + BiomarkerSnapshot + LabResult + ChatMessage + AssessmentWorkout); no persona returns empty `labs`/`workouts`/`chat_messages` from `_fetch_member_context`.
- [ ] Generated data is synthetic and varied across personas (no copy of one member's labs/chats onto another) and contains no real personal data or PHI.
- [ ] Jordan Rivera (Demo) (`jordan.rivera@workoutwiz.demo`) context is byte-for-byte unchanged versus `member-context.json` after a full seed.
- [ ] Seeding remains idempotent — a second run produces no duplicate nodes.
