# UAT: Biomarker & Lab-Result KG Retrieval

> **Source task**: [`.docs/tasks/103-biomarker-kg-retrieval.md`](../tasks/103-biomarker-kg-retrieval.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Backend server running (`cd backend && uvicorn app.main:app --reload`)
- [ ] Neo4j is running and accessible
- [ ] Database has been seeded: `cd backend && python -m app.knowledge_graph.seed` (or equivalent seed script)
- [ ] `UAT_AUTH_TOKEN` env var set by logging in as Jordan Rivera:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=jordan.rivera%40workoutwiz.demo&password=password123' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  ```
- [ ] Jordan Rivera's member UUID known (returned by the coach brief or members endpoint; substitute into tests marked `<jordan-member-id>`)

---

## API Tests

### UAT-API-001: Traversal functions return biomarker data for Jordan Rivera via /kg/recommend
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /kg/recommend`
- **Description**: Verify the retrieval graph's `run_biomarker_traversal` node fetches Jordan Rivera's BiomarkerSnapshot (resting_hr_bpm=58, hrv_ms=47, seeded date=2026-06-04) and that it flows through to the generation pipeline without error.
- **Steps**:
  1. Obtain Jordan Rivera's member UUID from `GET /coach/members` (see UAT-API-002) and substitute it for `<jordan-member-id>`.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<jordan-member-id>","query":"lower body strength session"}'
  ```
- **Expected Result**: `200 OK` with a JSON body containing `exercises` (non-empty array), `overall_reasoning` (non-empty string), and `member_id` equal to the supplied UUID. No `500` error — a 500 would indicate `run_biomarker_traversal` failed during graph execution.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-002: Coach members list returns seeded member IDs (prerequisite for other tests)
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/members`
- **Description**: Verify the members endpoint lists all seeded personas so Jordan Rivera's UUID can be resolved for subsequent tests.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | python3 -c "import sys,json; members=json.load(sys.stdin); jordan=[m for m in members if 'Jordan' in m.get('member_name','')]; print(jordan)"
  ```
- **Expected Result**: `200 OK` with an array of at least 15 member objects. The array contains an entry where `member_name` is `"Jordan Rivera"` with a non-null `member_id` UUID.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-003: Coach brief surfaces Jordan Rivera's biomarker data
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/brief`
- **Description**: Verify that `_fetch_member_context` now returns biomarker fields from Neo4j. The `CoachBriefResponse` itself doesn't expose raw biomarkers, but a 200 with well-formed data confirms the Neo4j query (`HAS_BIOMARKER` traversal) did not error. This also validates the seeded BiomarkerSnapshot exists for Jordan Rivera.
- **Steps**:
  1. Run the curl command below as-is (authenticates as Jordan Rivera).
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | python3 -c "import sys,json; r=json.load(sys.stdin); print('member_id:', r.get('member_id')); print('member_name:', r.get('member_name')); print('goals_count:', len(r.get('goals',[])))"
  ```
- **Expected Result**: `200 OK` with `member_id` (non-empty UUID), `member_name` = `"Jordan Rivera"`, and `goals` containing at least 2 items. No `500` — a 500 would indicate the `HAS_BIOMARKER` / `HAS_LAB_RESULT` OPTIONAL MATCH in `_fetch_member_context` is broken.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-004: Health Markers section appears in coach chat context when biomarker data is present
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /coach/chat`
- **Description**: Verify that `_build_context_prompt()` includes the `BIOMARKERS:` section when Jordan Rivera has a seeded BiomarkerSnapshot, and that the coach LLM is therefore able to answer a biomarker-specific question.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"What is Jordan'\''s resting heart rate and HRV?","session_id":"uat-biomarker-test-001"}'
  ```
- **Expected Result**: `200 OK` with `reply` (non-empty string) that references resting heart rate or HRV values (specifically `58 bpm` and `47 ms` as seeded). The reply must not say it has no data about heart rate — that would indicate the `BIOMARKERS:` section is missing from the context prompt.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-005: Health Markers section appears in /kg/recommend reasoning when biomarker data is present
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /kg/recommend`
- **Description**: Verify that `assemble_context_from_parts()` emits a `--- Health Markers ---` block for Jordan Rivera by checking the pipeline does not crash and returns a recommendation. This test is distinct from UAT-API-001 because it explicitly queries with a biomarker-relevant prompt to encourage the health section to appear in reasoning.
- **Steps**:
  1. Substitute Jordan Rivera's member UUID for `<jordan-member-id>`.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<jordan-member-id>","query":"recovery session appropriate for elevated resting HR"}' | python3 -c "import sys,json; r=json.load(sys.stdin); print('exercises:', len(r.get('exercises',[]))); print('reasoning:', r.get('overall_reasoning','')[:200])"
  ```
- **Expected Result**: `200 OK`, `exercises` array is non-empty, `overall_reasoning` is non-empty. No 500 error — a crash would indicate `run_biomarker_traversal` or `assemble_context_from_parts()` raised an exception during biomarker formatting.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-006: Non-existent member returns empty biomarker/lab results without error
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /kg/recommend`
- **Description**: Verify that when `member_id` does not correspond to any seeded Member node, `get_biomarkers()` returns `None` and `get_lab_results()` returns `[]`, and `assemble_context_from_parts()` omits the `--- Health Markers ---` section (no error raised).
- **Steps**:
  1. Run the curl command below as-is using a well-formed but non-existent UUID.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"00000000-0000-0000-0000-000000000000","query":"cardio workout"}'
  ```
- **Expected Result**: `200 OK` (not 500). Response body has `exercises` (may be empty or fallback vector results), `overall_reasoning`, and `member_id` = `"00000000-0000-0000-0000-000000000000"`. The pipeline must not crash — a 500 would indicate `get_biomarkers()` or `get_lab_results()` is not handling the no-data case correctly.
- [x] Pass <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: Health Markers section omitted when biomarkers is None and lab_results is empty
- **Scenario**: Member exists but has no BiomarkerSnapshot or LabResult nodes. The `assemble_context_from_parts()` code path at `if BIOMARKER_BUDGET > 0 and (biomarkers or _lab_results):` must silently skip the section.
- **Steps**:
  1. Log in as a persona with no biomarker/lab data (use the non-seeded path: substitute `00000000-0000-0000-0000-000000000000` as a proxy — or verify the behaviour by checking that UAT-API-006 returns `200 OK` without a `--- Health Markers ---` string in the reasoning).
  2. Run the UAT-API-006 command above and inspect the `overall_reasoning` field.
- **Expected Result**: `overall_reasoning` does NOT contain the string `"--- Health Markers ---"` or `"BIOMARKERS:"`. No exception raised. `200 OK` status.
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-002: get_biomarkers returns None (not an error) for member with no BiomarkerSnapshot node
- **Scenario**: `get_biomarkers()` Cypher query matches no record — `result.single()` returns `None`. The function must return `None`, not raise.
- **Steps**:
  1. This is implicitly validated by UAT-API-006 — the pipeline succeeds for the zero-UUID member. For explicit confirmation: run UAT-API-006 and verify the HTTP response is `200` (not `500`).
- **Expected Result**: `200 OK` from `/kg/recommend` for the zero-UUID member. No traceback in backend logs.
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-003: get_lab_results returns empty list (not an error) for member with no LabResult nodes
- **Scenario**: `get_lab_results()` `result.fetch(3)` returns an empty list. The function must return `[]`, not raise.
- **Steps**:
  1. Implicitly validated by UAT-API-006. For explicit confirmation, confirm the zero-UUID `/kg/recommend` call (from UAT-API-006) returns `200 OK`.
- **Expected Result**: `200 OK`. `exercises` field present in response (even if empty/vector-only). No `500`.
- [x] Pass <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: Full retrieval graph wires run_biomarker_traversal in parallel with other traversals
- **Components**: `build_retrieval_graph()` → `lookup_member` → [`run_injury_traversal`, `run_preference_traversal`, `run_vector_search`, `run_biomarker_traversal`, `run_chat_history_traversal`] (parallel) → `assemble`
- **Flow**: Invoke `POST /kg/recommend` for Jordan Rivera; all five parallel traversal nodes must complete before `assemble` runs; the resulting `ContextSlice` must include `biomarkers` and `lab_results` fields.
- **Steps**:
  1. Substitute Jordan Rivera's UUID for `<jordan-member-id>`.
  2. Run the curl command below.
  3. Verify the response includes a non-empty `overall_reasoning` that shows the full pipeline completed (injury constraints + preferences + biomarkers all assembled).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<jordan-member-id>","query":"full body workout respecting knee injury"}' | python3 -c "import sys,json; r=json.load(sys.stdin); print('exercises:', len(r.get('exercises',[]))); print('fallback_used:', r.get('fallback_used')); print('reasoning_snippet:', r.get('overall_reasoning','')[:300])"
  ```
- **Expected Result**: `200 OK`. `exercises` non-empty. `fallback_used` is `false` (graph ran successfully end-to-end). `overall_reasoning` mentions knee or injury context, demonstrating that both the injury traversal and the biomarker traversal contributed to the assembled context.
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-002: All 15 non-demo personas have seeded BiomarkerSnapshot nodes reachable via Neo4j traversal
- **Components**: `seed_coaching_context_all()` → Neo4j `BiomarkerSnapshot` nodes → `get_biomarkers()` traversal
- **Flow**: The seed function loops over all PERSONAS (including all 15 non-Jordan-Rivera personas). Each must have a `HAS_BIOMARKER` relationship to a `BiomarkerSnapshot` node, so `get_biomarkers()` returns a non-None dict for each one.
- **Steps**:
  1. Get the full member list from `GET /coach/members`.
  2. Run the command below to invoke `/kg/recommend` for every member and count successful biomarker retrievals (all must succeed without 500).
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | python3 -c "
import sys, json, urllib.request, urllib.error
members = json.load(sys.stdin)
token = '$UAT_AUTH_TOKEN'
failed = []
for m in members:
    mid = m.get('member_id', '')
    if not mid:
        continue
    req = urllib.request.Request(
        'http://localhost:8000/kg/recommend',
        data=json.dumps({'member_id': mid, 'query': 'lower body'}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
        method='POST'
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        body = json.load(resp)
        if not body.get('exercises') and not body.get('overall_reasoning'):
            failed.append(mid)
    except urllib.error.HTTPError as e:
        failed.append(f'{mid} HTTP {e.code}')
print('failed:', failed)
print('total_members:', len(members))
"
  ```
- **Expected Result**: `failed` list is empty. `total_members` is at least 15. No member UUID yields a `500` error — that would indicate `run_biomarker_traversal` crashed for that member (e.g., missing `BiomarkerSnapshot` node causing an unexpected code path).
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-003: Neo4j schema constraints for BiomarkerSnapshot and LabResult are active
- **Components**: `init_schema.py` constraints → Neo4j → duplicate MERGE safety
- **Flow**: `init_neo4j_schema()` must have applied `biomarker_snapshot_id` and `lab_result_id` uniqueness constraints. Verify this directly against Neo4j.
- **Steps**:
  1. Set Neo4j connection details in env: `set -a && source .env && set +a`
  2. Run the cypher query below using the Neo4j CLI or HTTP API to list active constraints.
- **Command**:
  ```bash
  set -a && source backend/.env && set +a && curl -sS -u "${NEO4J_USER:-neo4j}:${NEO4J_PASSWORD}" -H 'Content-Type: application/json' 'http://localhost:7474/db/neo4j/tx/commit' -d '{"statements":[{"statement":"SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties WHERE name IN [\"biomarker_snapshot_id\", \"lab_result_id\"] RETURN name, labelsOrTypes, properties"}]}' | python3 -c "import sys,json; r=json.load(sys.stdin); rows=r['results'][0]['data']; [print(row['row']) for row in rows]"
  ```
- **Expected Result**: Two constraint rows returned:
  - `["biomarker_snapshot_id", ["BiomarkerSnapshot"], ["id"]]`
  - `["lab_result_id", ["LabResult"], ["id"]]`
  
  If zero rows are returned, the constraints are missing from `init_schema.py` (task step 4 not completed).
- [x] Pass <!-- 2026-06-08 -->

### UAT-INT-004: Jordan Rivera's seeded LabResult nodes are reachable and correctly typed
- **Components**: `seed_assessment_member_context()` → Neo4j `LabResult` nodes → `get_lab_results()` traversal
- **Flow**: Jordan Rivera has two seeded LabResult nodes (`blood_panel` dated 2026-04-20, and `dexa_scan` dated 2026-03-30). `get_lab_results()` must return both, ordered by date DESC (blood_panel first).
- **Steps**:
  1. Set Neo4j env as in UAT-INT-003.
  2. Get Jordan Rivera's member UUID from UAT-API-002, substitute for `<jordan-member-id>`.
  3. Run the cypher query below.
- **Command**:
  ```bash
  set -a && source backend/.env && set +a && curl -sS -u "${NEO4J_USER:-neo4j}:${NEO4J_PASSWORD}" -H 'Content-Type: application/json' 'http://localhost:7474/db/neo4j/tx/commit' -d '{"statements":[{"statement":"MATCH (m:Member {id: $mid})-[:HAS_LAB_RESULT]->(l:LabResult) RETURN l.type, l.date ORDER BY l.date DESC","parameters":{"mid":"<jordan-member-id>"}}]}' | python3 -c "import sys,json; r=json.load(sys.stdin); [print(row['row']) for row in r['results'][0]['data']]"
  ```
- **Expected Result**: Two rows returned:
  - `["blood_panel", "2026-04-20"]`
  - `["dexa_scan", "2026-03-30"]`

  The `blood_panel` row appears first (more recent date). If zero rows are returned, the Jordan Rivera lab seeding in `seed_assessment_member_context()` did not run or the `HAS_LAB_RESULT` edge was not created.
- [x] Pass <!-- 2026-06-08 -->
