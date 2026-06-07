# SNOMED CT Grounding — Methodology

This document records how the Movement/Clinical knowledge graph is grounded in SNOMED CT
(via NCI EVS), which catalog terms map to which canonical concepts, and how the deterministic
safety traversal works. It is the authoritative reference for the SKOS mapping layer and the
PROV-O provenance trace.

---

## Access strategy: API-at-build-time, frozen local snapshot

SNOMED CT is fetched from the **NCI EVS REST API**
(`https://api-evsrest.nci.nih.gov`, terminology `snomedct_us`) once, during a build step,
for a **hand-curated seed list of joints + a label-resolved injury set**. The result is
frozen to `backend/data/snomed_subset.json` and committed. The running application never
calls SNOMED CT — all traversals run against Neo4j using pre-seeded nodes.

**Why not local file processing (PyMedTermino2)?** PyMedTermino2 + Owlready2 can load a
UMLS Metathesaurus zip and call `prune()` to reduce SNOMED CT to a subtree, but it requires
an NLM UMLS account/license and a multi-GB download. For 9 joints and 22 synthetic injuries,
resolving labels against the public NCI EVS API at build time is the right fit. The assessment
rubric explicitly states "a small, well-justified subset used meaningfully beats wiring up
everything shallowly."

**Why not reverse traversal (joint → all disorders)?** You can ask SNOMED "give me every
disorder whose finding site is the knee" via `inverseRoles` on the joint code or via SNOMED
ECL (`< |Clinical finding| : |Finding site| = << <joint>`). Both are rejected for this scope:
`inverseRoles` returns hundreds of disorders per joint (tumors, congenital anomalies, fractures
— overwhelmingly not training injuries), and public ECL endpoints (IHTSDO Snowstorm) return
403 to programmatic calls. Filtering noise would cost more than the label-driven approach
below. Option: switch to ECL if this grows into a real product covering broad injury vocabulary.

**NCI EVS endpoints used** (all public, no auth required):

| Need | Endpoint |
|------|----------|
| Resolve free text → concept | `GET /api/v1/concept/snomedct_us/search?term=...&type=contains&include=minimal&pageSize=n` |
| Concept by code (full record + roles) | `GET /api/v1/concept/snomedct_us/{code}?include=full` |
| Children / parents | `GET /api/v1/concept/snomedct_us/{code}/children` · `/parents` |
| Ancestors (root paths) | `GET /api/v1/concept/snomedct_us/{code}/pathsToRoot` |
| Descendants / subtree | `GET /api/v1/concept/snomedct_us/{code}/descendants?maxLevel=n` |
| Roles (finding site) | Use `include=full` on the concept — NOT `/roles`; post-coordinated codes return `[]` from the `/roles` endpoint but expose roles in the full record |

---

## SKOS concept map: catalog joints → SNOMED CT body structures

The 9 distinct `joints_loaded` values from `exercises.json` map as follows.
All codes verified live against NCI EVS (`snomedct_us`).

| `joints_loaded` catalog term | SNOMED CT code | Concept name | SKOS relation | Notes |
|------------------------------|----------------|--------------|---------------|-------|
| `knee` | `49076000` | Knee joint structure | `skos:exactMatch` | |
| `shoulder` | `182168000` | Shoulder joint structure | `skos:exactMatch` | |
| `hip` | `24136001` | Hip joint structure | `skos:exactMatch` | |
| `elbow` | `76248009` | Elbow joint structure | `skos:exactMatch` | |
| `ankle` | `70258002` | Ankle joint structure | `skos:exactMatch` | |
| `wrist` | `74670003` | Wrist joint structure | `skos:exactMatch` | |
| `lumbar spine` | `122496007` | Lumbar spine structure | `skos:closeMatch` | Catalog uses motion-segment language; SNOMED grains to osseous column |
| `thoracic spine` | `122495006` | Thoracic spine structure | `skos:closeMatch` | Same rationale |
| `cervical spine` | `122494005` | Cervical spine structure | `skos:closeMatch` | Same rationale |

`skos:exactMatch` means the catalog term and SNOMED concept denote the same thing.
`skos:closeMatch` means they are closely related but not fully interchangeable — used for
the spines because the exercise catalog's terminology describes a functional motion segment
while SNOMED describes an osseous column structure. The distinction is documented so future
resolvers can apply the right confidence threshold.

---

## Injury vocabulary: source of truth

`seed.py` contains **23 injury dicts across 13 of the 15 synthetic personas** (2 personas
have no injuries). After deduplication on `(affected_joints[0], snomedct_hint)`, there are
**19 distinct SNOMED resolution targets**.

Each injury dict now carries three fields added in the `seed.py` expansion:

```python
{
    "name": "Left knee tendinopathy",
    "affected_joints": ["knee"],
    "severity": "moderate",
    "status": "active",
    "onset_date": "2025-11-15",
    "region": "left knee",          # explicit laterality + body part
    "notes": "Patellar/quadriceps tendon irritation. Avoid heavy loading and deep knee "
             "flexion under load. Box squats with limited depth and hip-dominant patterns "
             "tolerated.",
    "snomedct_hint": "Patellar tendinopathy",   # ← resolver label used by build script
}
```

`snomedct_hint` is the label the build script searches against NCI EVS. The build script
derives its resolver input **directly from `seed.py`'s PERSONAS** — no separate `INJURY_VOCAB`
constant is needed in the script.

### Deduplication table (19 unique targets)

| Joint | `snomedct_hint` (resolver label) | Code override | Seed.py injury names covered |
|-------|----------------------------------|---------------|------------------------------|
| ankle | Achilles tendinopathy | — | Achilles tendinopathy |
| ankle | Ankle sprain | — | Ankle sprain |
| cervical spine | C5-C6 cervical disc herniation | — | C5-C6 cervical disc herniation |
| cervical spine | Cervical stenosis | — | Cervical stenosis |
| elbow | Elbow strain | — | Elbow strain (resolved) |
| elbow | Lateral epicondylitis | — | Lateral epicondylitis (tennis elbow) |
| hip | Hip flexor strain | — | Hip flexor tear *(normalised; "tear" matches few SNOMED training disorders)* |
| hip | Hip labral tear | — | Hip labral tear |
| knee | Knee osteoarthritis | — | Knee osteoarthritis |
| knee | Knee sprain | — | Knee sprain |
| knee | Patellar tendinopathy | — | Left knee tendinopathy, Patellar tendinopathy |
| knee | Patellofemoral pain syndrome | `430725003` | *(Jordan Rivera / member-context.json; lateralised variant `49631000087103` used at member level)* |
| lumbar spine | Lumbar disc herniation | — | Lumbar disc herniation |
| lumbar spine | Lumbar muscle strain | — | Lower back strain |
| shoulder | Shoulder bursitis | — | Shoulder bursitis |
| shoulder | Shoulder impingement syndrome | — | Left shoulder impingement, Right shoulder impingement ×2, Shoulder impingement (resolved) |
| thoracic spine | Thoracic compression fracture | — | Thoracic compression |
| thoracic spine | Thoracic kyphosis | — | Thoracic kyphosis |
| wrist | Wrist fracture | — | Wrist fracture recovery |
| wrist | Wrist tendinopathy | — | Wrist tendinopathy |

**Deduplication rules applied by the build script:**
- Lateralised names (`Left knee tendinopathy`, `Left/Right shoulder impingement`) collapse to
  the non-lateralised catalog entry. Laterality lives in `Injury.region`, not the Disorder node.
- `(resolved)` status suffix is stripped; `Injury.status` carries that semantic.
- `"Hip flexor tear"` → resolved as "Hip flexor strain" (better SNOMED coverage for training
  injuries). Code override available if the top hit drifts.

---

## Automated resolver approach

`INJURY_CONCEPTS` is **generated by the build script**, not hand-maintained. The input is
derived directly from `seed.py`'s PERSONAS at build time — no separate vocab constant required.

The process:

1. **Derive input** — read PERSONAS, collect `(affected_joints[0], snomedct_hint, code_override)`
   tuples, deduplicate on `(joint, snomedct_hint)`. This produces the 19-entry table above.
2. **Resolve** — for each entry:
   - If a `code` override exists → use it directly (skip search).
   - Otherwise → call `/search?term=<snomedct_hint>&type=contains&pageSize=1`, take the top hit.
3. **Fetch full record** — `GET /{code}?include=full` → extract `Has finding site` role target.
4. **Validate** — walk the finding-site code's `pathsToRoot`; confirm one of the 9 joint SNOMED
   codes appears in the path. If not → `validated: false`, logged as a build warning.
5. **Freeze** — append resolved record to the `injuries` section of `snomed_subset.json`.

The build script emits a validation report:

```
✓ Achilles tendinopathy      → 36185009  | finding-site: 70258002 (Ankle joint)         [validated]
✓ Patellofemoral pain syndrome → 430725003 | finding-site: 49076000 (Knee joint)         [pinned]
✗ Hip flexor tear            → 444798002  | finding-site: 68367000 (Thigh)               [WARN: not a catalog joint]
```

Any `✗` line means the resolver picked a disorder whose anatomy doesn't align with our catalog.
Fix by rewording `snomedct_hint` in `seed.py` or adding a `code` override comment. This makes
mis-resolutions visible at build time rather than silently corrupting the graph.

---

## Knee joint sub-structure hierarchy

Children of `49076000` (Knee joint structure) — captured at build time so the safety filter
can cover sub-structures transitively:

| SNOMED code | Concept name |
|-------------|-------------|
| `182204005` | Entire knee joint |
| `244548003` | Component of knee joint |
| `305019006` | Periarticular bone structure of knee joint |
| `68010000` | Structure of ligament of knee joint |
| `719442003` | Structure of left knee joint |
| `719443008` | Structure of right knee joint |

This seeds the `PART_OF` edges in Neo4j, enabling the Cypher safety query to traverse
`BodyStructure<-[:PART_OF*0..]` and catch exercises that stress *any* sub-structure of the
knee — not only exact name matches.

---

## Neo4j schema additions

Two new node types and three new edge types extend the existing schema in
`knowledge-graph-schema.md`. Existing nodes and edges are unchanged.

### New nodes

| Label | Key properties | Purpose |
|-------|---------------|---------|
| `BodyStructure` | `snomed_code` (unique), `snomed_name`, `catalog_term` (or null), `skos_relation` | Canonical SNOMED joint / body region |
| `Disorder` | `snomed_code` (unique), `snomed_name`, `finding_site_code` | SNOMED clinical disorder (injury category) |

### New edges

| Relationship | From → To | Properties | Purpose |
|-------------|-----------|-----------|---------|
| `MAPS_TO` | `Exercise → BodyStructure` | `catalog_term`, `skos_relation` | Replaces implicit string match on `joints_loaded` |
| `FINDING_SITE` | `Disorder → BodyStructure` | `snomed_role` = `Has finding site` | SNOMED role edge enabling disorder → joint traversal |
| `PART_OF` | `BodyStructure → BodyStructure` | `depth` (int) | Hierarchical containment (child → parent) |

The existing `Injury` node gains one additional edge at ingestion:
`(:Injury)-[:MAPS_TO_DISORDER]->(:Disorder)`, resolved by matching the Injury's `name`
against the labels in `INJURY_VOCAB`.

---

## Deterministic safety traversal

The safety filter in `retrieval_graph.py` uses Cypher graph traversal — not string
comparison, not a prompt instruction:

```cypher
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(inj:Injury)
      -[:MAPS_TO_DISORDER]->(d:Disorder)
      -[:FINDING_SITE]->(bs:BodyStructure)
      -[:PART_OF*0..]->(joint:BodyStructure)
      <-[:MAPS_TO]-(ex:Exercise)
RETURN DISTINCT ex.id AS contraindicated_exercise_id,
       inj.name        AS injury_name,
       d.snomed_code   AS disorder_code,
       bs.snomed_name  AS finding_site_name,
       joint.catalog_term AS matched_joint
```

`PART_OF*0..` traverses **upward** from the finding-site body structure to its parent joints
(child → parent direction, 0-or-more hops). At 0 hops `joint = bs` (when the finding site IS
a catalog joint directly). At 1+ hops it walks through the sub-structure hierarchy to the
catalog joint root, which is the node exercises `MAPS_TO`.

Two types of PART_OF edges are in the graph:
- **Ontology edges** (from `/children` API): e.g. `Structure of ligament of knee joint → Knee joint structure`
- **Bridge edges** (added during ingestion): finding-site nodes matched via keyword (tendons, bursae,
  muscle groups) get a direct `PART_OF` to the catalog joint root, closing the traversal loop for
  structures that sit in a parallel SNOMED hierarchy branch.

The set of `contraindicated_exercise_id` values is passed to the generation graph as a hard
exclusion list before any LLM call.

---

## PROV-O provenance trace

Every recommendation includes a provenance object aligned to PROV-O semantics. Pragmatic JSON
representation, not full RDF/Turtle — the spec allows this.

```json
{
  "prov_type": "prov:wasDerivedFrom",
  "injury_node": "inj_knee_left",
  "disorder_snomed": "430725003",
  "disorder_name": "Patellofemoral stress syndrome",
  "finding_site_snomed": "49076000",
  "finding_site_name": "Knee joint structure",
  "traversal_path": "Member→HAS_INJURY→Injury→MAPS_TO_DISORDER→Disorder→FINDING_SITE→BodyStructure→PART_OF*→BodyStructure←MAPS_TO←Exercise",
  "skos_mapping": {
    "catalog_term": "knee",
    "snomed_code": "49076000",
    "relation": "skos:exactMatch"
  },
  "decision": "CONTRAINDICATED — exercise filtered before generation"
}
```

---

## Build script outline (`scripts/build_snomed_subset.py`)

```python
import json, sys, time
from pathlib import Path
import httpx

BASE = "https://api-evsrest.nci.nih.gov/api/v1/concept/snomedct_us"

# ── 9 catalog joints — hand-verified SKOS map ──────────────────────────────
JOINT_MAP: dict[str, dict] = {
    "knee":          {"code": "49076000",  "skos": "exactMatch"},
    "shoulder":      {"code": "182168000", "skos": "exactMatch"},
    "hip":           {"code": "24136001",  "skos": "exactMatch"},
    "elbow":         {"code": "76248009",  "skos": "exactMatch"},
    "ankle":         {"code": "70258002",  "skos": "exactMatch"},
    "wrist":         {"code": "74670003",  "skos": "exactMatch"},
    "lumbar spine":  {"code": "122496007", "skos": "closeMatch"},
    "thoracic spine":{"code": "122495006", "skos": "closeMatch"},
    "cervical spine":{"code": "122494005", "skos": "closeMatch"},
}

# Overrides for labels where auto-resolution is ambiguous
CODE_OVERRIDES: dict[str, str] = {
    "Patellofemoral pain syndrome": "430725003",
}

# ── derive injury targets from seed.py PERSONAS ────────────────────────────
def _injury_targets() -> list[dict]:
    """Read PERSONAS, deduplicate on (joint, snomedct_hint), return resolver inputs."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.knowledge_graph.seed import PERSONAS
    seen: set[tuple] = set()
    targets = []
    for persona in PERSONAS:
        for inj in persona.get("injuries", []):
            hint = inj.get("snomedct_hint")
            joint = (inj.get("affected_joints") or [None])[0]
            if not hint or not joint:
                continue
            key = (joint, hint)
            if key in seen:
                continue
            seen.add(key)
            targets.append({
                "label": hint,
                "expected_joint": joint,
                "code": CODE_OVERRIDES.get(hint),
            })
    return targets

# ── resolver ───────────────────────────────────────────────────────────────
def resolve_injury(entry: dict) -> dict:
    label, expected_joint, pinned_code = (
        entry["label"], entry["expected_joint"], entry.get("code")
    )
    if pinned_code:
        code = pinned_code
    else:
        r = httpx.get(f"{BASE}/search", params={"term": label, "type": "contains",
                                                  "include": "minimal", "pageSize": 1})
        r.raise_for_status()
        code = r.json()["concepts"][0]["code"]
        time.sleep(0.25)   # stay well under rate limit

    full = httpx.get(f"{BASE}/{code}", params={"include": "full"})
    full.raise_for_status()
    concept = full.json()
    time.sleep(0.25)

    finding_site = next(
        (r for r in concept.get("roles", []) if "finding site" in r.get("type", "").lower()),
        None,
    )
    validated = False
    fs_code = fs_name = None
    if finding_site:
        fs_code = finding_site["relatedCode"]
        fs_name = finding_site["relatedName"]
        paths = httpx.get(f"{BASE}/{fs_code}/pathsToRoot")
        joint_codes = {v["code"] for v in JOINT_MAP.values()}
        validated = any(
            node["code"] in joint_codes
            for path in paths.json()
            for node in path
        )
        time.sleep(0.25)

    mark = "✓" if validated else "✗"
    tag  = "[pinned]" if pinned_code else "[validated]" if validated else "[WARN: not a catalog joint]"
    print(f"  {mark} {label:<40} → {code} | finding-site: {fs_code} ({fs_name}) {tag}")

    return {
        "label": label, "expected_joint": expected_joint,
        "disorder_code": code, "disorder_name": concept["name"],
        "finding_site_code": fs_code, "finding_site_name": fs_name,
        "validated": validated,
    }
```

---

## 3-pass concept resolver (runtime)

At runtime, when a coach types free text ("her left knee is bothering her"), the resolver
maps it to a `BodyStructure` node:

1. **Exact match** — lowercase-normalize input; check `catalog_term` in `BodyStructure` nodes. Confidence 1.0.
2. **Fuzzy match** — token overlap / edit distance against `snomed_name` and `catalog_term`. Confidence = score if ≥ 0.8.
3. **Vector / embedding fallback** — embed the phrase; cosine-search against pre-embedded `snomed_name` + synonyms. Confidence = score if ≥ 0.6.

All three passes fail or confidence < 0.6 → **do not guess**: surface "I couldn't confidently
identify a joint or injury in that description. Can you clarify?" This is the
graceful-degradation requirement from the spec.

---

## Files produced by this work

| File | Status | Purpose |
|------|--------|---------|
| `backend/app/knowledge_graph/seed.py` | ✅ done | All 23 injury dicts have `region`, `notes`, `snomedct_hint` |
| `backend/app/knowledge_graph/ingest_injuries.py` | ✅ done | Passes `region`, `notes`, `snomedct_hint` through Cypher SET and `build_injury_records()` |
| `backend/app/knowledge_graph/init_schema.py` | ✅ done | `BodyStructure` + `Disorder` uniqueness constraints added |
| `backend/scripts/build_snomed_subset.py` | ✅ done | Build-time NCI EVS fetch + resolver; 19/19 validated; bridge `PART_OF` logic documented |
| `backend/data/snomed_subset.json` | ✅ done | Checked-in snapshot: 9 joints + 44 sub-structures + 19 disorders, all validated |
| `backend/app/knowledge_graph/ingest_snomed.py` | ✅ done | Loads snapshot into Neo4j; 124 Exercise→BodyStructure + 23 Injury→Disorder edges live |
| `backend/app/knowledge_graph/traversal.py` | ✅ done | `_CONTRAINDICATED_IDS_QUERY` + `_SAFE_EXERCISES_QUERY` use SNOMED traversal; `get_contraindicated_provenance()` added |
| `backend/app/kg/retrieval_graph.py` | ✅ done | Fetches provenance in parallel; stitches into `ContextSlice` |
| `backend/app/kg/context_assembler.py` | ✅ done | `ContextSlice` carries `contraindicated_provenance` |
| `backend/app/kg/generation_graph.py` | ✅ done | `RecommendedExercise.provenance` field; PROV-O trace emitted per exercise |
| `.docs/knowledge-graph-schema.md` | ✅ done | `BodyStructure`, `Disorder`, 5 new edge types, SNOMED traversal patterns documented |
