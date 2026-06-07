# 100 — Document OPE & COPPER Ontology Decisions (used vs omitted, with rationale)

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [099-seed-multi-persona-context](099-seed-multi-persona-context.md), [101-fix-chatmessage-kg-result-type](101-fix-chatmessage-kg-result-type.md)

## Objective

Write a legible decision record explaining what was evaluated from the OPE and COPPER ontologies, what was deliberately used versus omitted, and why — so assessors can see the scoping reasoning the assessment explicitly asks for ("part of the task is deciding what to actually use").

## Approach

Extend the existing `backend/app/knowledge_graph/SNOMED_METHODOLOGY.md` with two new ontology sections (OPE, COPPER) plus a short cross-ontology coverage note, rather than creating a sibling doc. Rationale: `SNOMED_METHODOLOGY.md` already frames itself as the authoritative ontology-grounding writeup (it owns SKOS and PROV-O), so co-locating OPE/COPPER there keeps all five spec ontologies discoverable in one place and matches the existing voice (decision-record tone, "Why not X?" subsections, used-vs-omitted tables). This is a documentation-only deliverable — no code, schema, or seed changes.

## Prerequisites

- [ ] Read `.docs/guides/candidate-assessment-main/ASSESSMENT.md` lines 78–94 — the ontology table and the explicit "what to pull / what to leave out / why" prompt this doc answers.
- [ ] Read `backend/app/knowledge_graph/SNOMED_METHODOLOGY.md` in full — mirror its structure (intro paragraph, `---` section breaks, comparison tables, "Why not X?" rationale subsections).
- [ ] Confirm current coverage: OPE and COPPER are referenced **only** in the assessment spec and one roadmap line; they appear nowhere in code or methodology docs. SNOMED CT (anatomy/injuries), SKOS (concept mapping), and PROV-O (provenance) are already grounded and documented. The new sections must contrast accurately against this.

---

## Steps

### 1. OPE (Ontology of Physical Exercises) section  <!-- agent: general-purpose -->

- [ ] Add a new `## OPE — Ontology of Physical Exercises` section to `SNOMED_METHODOLOGY.md` opening with a one-paragraph statement of what OPE is (a BioPortal ontology modelling physical exercises, the musculoskeletal system, exercise equipment, and exercise-related injuries) and what part of our domain it overlaps with (the Exercise / muscle / joint / equipment / injury nodes already in the Movement-Clinical KG).
- [ ] Add a **used vs omitted** table mapping OPE's concept areas onto our catalog: for each area (exercises, musculoskeletal systems/muscles, equipment, injuries) state the catalog field it corresponds to (`exercises.json` muscle_groups / joints_loaded / equipment_required / movement_patterns, and the seed `Injury` dicts), and mark **used**, **partially used**, or **omitted**.
- [ ] Write the rationale prose: explain that the catalog already ships a clean, internally-consistent exercise taxonomy (19 muscle groups, 9 joints, 36 movement patterns, 32 equipment types) with UUID keys, so OPE's *exercise/equipment/muscle* layer was **not** ingested as an external vocabulary — the hand-rolled catalog taxonomy is the source of truth (the spec explicitly permits "a clean hand-rolled ontology aligned to these concepts"). State what OPE contributed instead: validation/cross-check of the catalog's anatomical vocabulary and confirmation that the clinical-grounding effort was better spent on SNOMED CT (which gives codeable anatomy + the `part-of` hierarchy + finding-site edges OPE does not model at clinical depth).
- [ ] Add a `**Why not ingest OPE wholesale?**`-style subsection (mirroring the SNOMED doc's "Why not …?" subsections): note OPE concept-level overlap is shallow for our injury-safety use case versus SNOMED CT, parsing full OWL was out of scope per the spec, and pulling a second exercise vocabulary would duplicate the catalog without adding traversal power.

### 2. COPPER (personalization / behaviour-change) section  <!-- agent: general-purpose -->

- [ ] Add a new `## COPPER — Personalisation & Behaviour-Change` section opening with a one-paragraph statement of what COPPER is (a BioPortal ontology for contextualised & personalised physical-activity/exercise recommendations, modelling personalization context and behaviour-change concepts) and where it is relevant to this product (adherence, churn-risk, preferences, and the morning-brief / copilot personalization surface).
- [ ] Add a **used vs omitted** table mapping COPPER's concept areas (personalization context, preferences, behaviour-change/adherence, goals) onto what the system actually implements: the member-context preference signals, the `FeedbackEvent` / `RATED` preference-weighting layer (cross-reference `FEEDBACK_METHODOLOGY.md`), and the adherence/churn signals seeded into the Member Context graph. Mark each **used**, **partially used (concept reused, vocabulary not ingested)**, or **omitted**.
- [ ] Write the rationale prose: COPPER's *ideas* (personalization context, preference-driven ranking, behaviour-change/adherence signals) are realised functionally through the feedback preference layer and the seeded churn/adherence data, but COPPER's formal vocabulary was **not** ingested — explain why (behaviour-change modelling is a personalization/ranking concern, not a safety-traversal concern; the safety layer is the assessment's hard requirement and was prioritised; a hand-rolled preference model already covers the demoable surface). Be explicit that this is a deliberate scope cut, not an oversight.
- [ ] Add a forward-looking note: if personalization were to deepen (e.g. structured behaviour-change staging, intervention modelling), COPPER would be the ontology to formalise the preference/adherence vocabulary against — stating this shows the omission was evaluated, not unknown.

### 3. Cross-link & coverage-map note  <!-- agent: general-purpose -->

- [ ] Add a short `## Ontology coverage at a glance` table (or paragraph) summarising all five spec ontologies in one place: **SNOMED CT** = grounded (anatomy, injuries, part-of, finding-site), **SKOS** = grounded (catalog↔SNOMED concept map, see existing section), **PROV-O** = grounded (provenance traces, see existing section), **OPE** = evaluated, catalog-aligned, not ingested (see §OPE), **COPPER** = evaluated, concepts reused via feedback layer, vocabulary not ingested (see §COPPER).
- [ ] Cross-link to `FEEDBACK_METHODOLOGY.md` (preference/adherence ↔ COPPER) and keep the existing SKOS/PROV-O sections authoritative — the new content should reference them, not restate them.
- [ ] Add one sentence relating the chosen subset to the implemented graph: the used concepts all land as nodes/edges already in `knowledge-graph-schema.md` (no new schema introduced by this scoping decision).

### N. Verification  <!-- agent: general-purpose -->

- [ ] Doc renders as valid Markdown (tables aligned, headings nested correctly, links resolve to existing files).
- [ ] Both OPE and COPPER are covered, each with an explicit **used vs omitted** breakdown and a stated **rationale** for the omission.
- [ ] No code, schema, seed, or other docs were modified — only `SNOMED_METHODOLOGY.md` changed.

## Acceptance Criteria

- [ ] `backend/app/knowledge_graph/SNOMED_METHODOLOGY.md` contains a dedicated OPE section and a dedicated COPPER section, plus an at-a-glance coverage note covering all five spec ontologies.
- [ ] Each ontology section states **what was evaluated**, **what was used vs deliberately omitted**, and **why** — directly answering the assessment's "what to pull / what to leave out / why" prompt.
- [ ] The doc accurately reflects current implementation: SNOMED/SKOS/PROV-O grounded; OPE catalog-aligned but not ingested; COPPER concepts reused via the feedback layer but vocabulary not ingested.
- [ ] Tone, structure, and table style match the existing methodology docs; this remains a documentation-only deliverable (no implementation).
