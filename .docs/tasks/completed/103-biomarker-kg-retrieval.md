# 103 — Expose Biomarker & Lab-Result KG Nodes to Coach AI Retrieval

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [071-feedback-submission-ui](071-feedback-submission-ui.md), [084-test-source-type-population](084-test-source-type-population.md), [102-visual-architecture-diagrams](102-visual-architecture-diagrams.md)

## Objective

`BiomarkerSnapshot` and `LabResult` nodes already exist in Neo4j (seeded via `seed_coaching_context_all()` and `seed_rich_member_context_all()`), but are not surfaced to the Coach AI — `ContextSlice` in `context_assembler.py` has no biomarker or lab-result fields. This task wires the existing nodes into the retrieval graph so the Coach AI Copilot can reason over resting HR, HRV, sleep, blood panel markers, and DEXA body composition.

## Approach

1. Add `get_biomarkers()` and `get_lab_results()` to `traversal.py` — Cypher queries returning the most recent `BiomarkerSnapshot` and up to 3 `LabResult` nodes per member.
2. Extend `ContextSlice` in `context_assembler.py` to include `biomarkers` and `lab_results` fields.
3. Add a `run_biomarker_traversal()` node in `retrieval_graph.py` and wire it into the graph before `assemble`.
4. Extend `assemble_context_from_parts()` to format and include biomarker/lab data within the existing 2048-token budget (lower priority than exercise data — truncate if needed).
5. Verify that `init_schema.py` has uniqueness constraints for `BiomarkerSnapshot` and `LabResult`; add them if missing.
6. Verify seed coverage: `seed_coaching_context_all()` must call biomarker/lab seeding for all 15 personas, not only Jordan Rivera.

## Steps

### 1. Add traversal functions for biomarkers and lab results  <!-- agent: general-purpose -->

File: `backend/app/knowledge_graph/traversal.py`

Add two new async functions after the existing `get_performed_exercises()`:

```python
async def get_biomarkers(driver, member_id: str) -> dict | None:
    """Return the most recent BiomarkerSnapshot for a member, or None."""
    query = """
    MATCH (m:Member {id: $member_id})-[:HAS_BIOMARKER]->(b:BiomarkerSnapshot)
    RETURN b ORDER BY b.date DESC LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, member_id=member_id)
        record = await result.single()
        return dict(record["b"]) if record else None

async def get_lab_results(driver, member_id: str) -> list[dict]:
    """Return up to 3 most recent LabResult nodes for a member."""
    query = """
    MATCH (m:Member {id: $member_id})-[:HAS_LAB_RESULT]->(l:LabResult)
    RETURN l ORDER BY l.date DESC LIMIT 3
    """
    async with driver.session() as session:
        result = await session.run(query, member_id=member_id)
        records = await result.fetch(3)
        return [dict(r["l"]) for r in records]
```

- [ ] `get_biomarkers(driver, member_id)` added — returns latest `BiomarkerSnapshot` dict or `None`
- [ ] `get_lab_results(driver, member_id)` added — returns list of up to 3 `LabResult` dicts
- [ ] Both functions use `async with driver.session()` consistent with existing traversal patterns

### 2. Extend ContextSlice and assemble_context_from_parts  <!-- agent: general-purpose -->

File: `backend/app/kg/context_assembler.py`

2a. Add `biomarkers` and `lab_results` to the `ContextSlice` TypedDict:

```python
class ContextSlice(TypedDict):
    # ... existing fields ...
    biomarkers: dict | None          # latest BiomarkerSnapshot or None
    lab_results: list[dict]          # up to 3 LabResult nodes
```

2b. In `assemble_context_from_parts()`, format biomarker data as a compact text block and append it to the assembled context string — after exercise data, within the 2048-token budget. If the budget is exhausted before reaching biomarker data, omit it silently (do not raise).

Example format:
```
--- Health Markers ---
Biomarkers (2024-11-01): resting_hr=58bpm, hrv=62ms, sleep=7.2h/night
Lab Results:
  Blood panel (2024-10-15): LDL=98, HDL=62, HbA1c=5.1%, Vit-D=42, CRP=0.8
  DEXA (2024-09-01): body_fat=18.2%, lean_mass=71.4kg, bone_density_z=+0.3
```

- [ ] `ContextSlice` has `biomarkers: dict | None` and `lab_results: list[dict]` fields
- [ ] `assemble_context_from_parts()` formats and appends biomarker block after exercise data
- [ ] Biomarker block is omitted (not an error) when token budget is exhausted
- [ ] When `biomarkers` is `None` and `lab_results` is empty, no `--- Health Markers ---` section is emitted

### 3. Add run_biomarker_traversal node to the retrieval graph  <!-- agent: general-purpose -->

File: `backend/app/kg/retrieval_graph.py`

3a. Extend `RetrievalState` TypedDict with `biomarkers` and `lab_results` fields:

```python
class RetrievalState(TypedDict):
    # ... existing fields ...
    biomarkers: dict | None
    lab_results: list[dict]
```

3b. In `_make_nodes()`, add a `run_biomarker_traversal` async function:

```python
async def run_biomarker_traversal(state: RetrievalState) -> dict:
    member_id = state["member_id"]
    biomarkers = await get_biomarkers(driver, member_id)
    lab_results = await get_lab_results(driver, member_id)
    return {"biomarkers": biomarkers, "lab_results": lab_results}
```

3c. In `build_retrieval_graph()`, add the node and edge:
- `graph.add_node("run_biomarker_traversal", run_biomarker_traversal)`
- Wire it to run in parallel with existing traversal nodes (before `assemble`):
  - Add edge from `lookup_member` → `run_biomarker_traversal`
  - Add edge from `run_biomarker_traversal` → `assemble`

3d. Import `get_biomarkers` and `get_lab_results` from `traversal`.

- [ ] `RetrievalState` has `biomarkers` and `lab_results` fields
- [ ] `run_biomarker_traversal` node added and registered in the graph
- [ ] Node runs after `lookup_member`, before `assemble` (parallel with injury/preference traversals)
- [ ] Imports updated

### 4. Verify schema constraints for BiomarkerSnapshot and LabResult  <!-- agent: general-purpose -->

File: `backend/app/knowledge_graph/init_schema.py`

Check whether uniqueness constraints exist for `BiomarkerSnapshot` and `LabResult` node types. If missing, add:

```cypher
CREATE CONSTRAINT biomarker_snapshot_id IF NOT EXISTS
  FOR (b:BiomarkerSnapshot) REQUIRE b.id IS UNIQUE;

CREATE CONSTRAINT lab_result_id IF NOT EXISTS
  FOR (l:LabResult) REQUIRE l.id IS UNIQUE;
```

Also verify the seed adds an `id` property to each `BiomarkerSnapshot` and `LabResult` node in `seed.py`. If not, add `id: str(uuid4())` to each MERGE/CREATE.

- [ ] `BiomarkerSnapshot` uniqueness constraint present in `init_schema.py` (add if missing)
- [ ] `LabResult` uniqueness constraint present in `init_schema.py` (add if missing)
- [ ] Both node types have an `id` property in seed data (add `str(uuid4())` if missing)

### 5. Verify seed coverage for all 15 personas  <!-- agent: general-purpose -->

File: `backend/app/knowledge_graph/seed.py`

Inspect `seed_coaching_context_all()` (line ~477) and `seed_rich_member_context_all()` (line ~1046). Confirm both functions iterate over all entries in `PERSONAS` (15 personas), not just Jordan Rivera.

If any biomarker or lab-result seeding block is scoped only to Jordan Rivera (by email or index check), generalize it to loop over all PERSONAS — using varied but realistic values (vary HR ±10bpm, HRV ±15ms, sleep ±0.5h between personas).

- [ ] `seed_coaching_context_all()` seeds `BiomarkerSnapshot` for all 15 personas
- [ ] `seed_rich_member_context_all()` seeds at least one `LabResult` per persona
- [ ] No persona-specific guard (e.g. `if persona["email"] == "jordan@..."`) gates biomarker seeding

## Acceptance Criteria

- [ ] `get_biomarkers()` and `get_lab_results()` exist in `traversal.py` and return correct data from Neo4j
- [ ] `ContextSlice` includes `biomarkers` and `lab_results` fields
- [ ] `run_biomarker_traversal` node is wired into the retrieval graph
- [ ] Coach AI context string includes a `--- Health Markers ---` section when biomarker data is present
- [ ] Schema constraints for `BiomarkerSnapshot` and `LabResult` exist in `init_schema.py`
- [ ] All 15 personas have seeded biomarker and lab result nodes

---
**UAT**: [`.docs/uat/103-biomarker-kg-retrieval.uat.md`](../uat/103-biomarker-kg-retrieval.uat.md)
