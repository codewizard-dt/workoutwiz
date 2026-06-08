# UAT: Seed Rich Member Context for All Personas

> **Source task**: [`.docs/tasks/099-seed-multi-persona-context.md`](../tasks/099-seed-multi-persona-context.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Backend and Neo4j are running (`make dev` or equivalent)
- [ ] PostgreSQL is running and migrations are applied
- [ ] The seed has been run: `cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.seed`
- [ ] Obtain a token for **Alex Chen** (non-demo, with active injury): `export UAT_TOKEN_ALEX=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=alex@example.com&password=password123' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")`
- [ ] Obtain a token for **Morgan Lee** (non-demo, no injuries): `export UAT_TOKEN_MORGAN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=morgan@example.com&password=password123' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")`
- [ ] Obtain a token for **Drew Robinson** (non-demo, no injuries, max equipment): `export UAT_TOKEN_DREW=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=drew@example.com&password=password123' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")`
- [ ] Obtain a token for **Jordan Rivera (Demo)**: `export UAT_TOKEN_DEMO=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=jordan.rivera@workoutwiz.demo&password=password123' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")`

---

## API Tests

### UAT-API-001: `/coach/brief` returns full context for non-demo persona with active injury (Alex Chen)

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/brief`
- **Description**: Verifies that a non-demo persona with an active injury returns a populated `CoachBriefResponse` including `member_name`, `goals`, `injuries`, `morning_tasks`, `churn_risk`, and `adherence_weeks` — proving the new seed function filled in rich context for this account.
- **Steps**:
  1. Ensure the seed has been run (see Prerequisites)
  2. Run the curl command below as-is (using Alex Chen's token)
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_ALEX" | jq '{member_name, member_age, tier, goals: (.goals | length), injuries: (.injuries | length), morning_tasks: (.morning_tasks | length), churn_risk_level: .churn_risk.level, adherence_weeks: (.adherence_weeks | length)}'
  ```
- **Expected Result**: `200 OK` with JSON object where:
  - `member_name` is `"Alex Chen"` (non-empty string)
  - `member_age` is a non-null integer
  - `tier` is a non-null string (one of `"Self-Guided"`, `"Group Coaching"`, `"1:1 Coaching"`)
  - `goals` count ≥ 1
  - `injuries` count ≥ 1 (Alex has left knee tendinopathy active)
  - `morning_tasks` count ≥ 1
  - `churn_risk_level` is one of `"low"`, `"moderate"`, `"elevated"`
  - `adherence_weeks` count = 4
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-002: `/coach/brief` returns full context for non-demo persona with no injuries (Morgan Lee)

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/brief`
- **Description**: Verifies that a non-demo persona with no injuries (Morgan Lee) also gets a fully populated brief — no empty `labs`/`workouts`/`chat_messages` in the underlying context fetch.
- **Steps**:
  1. Run the curl command below as-is (using Morgan Lee's token)
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_MORGAN" | jq '{member_name, member_age, tier, goals: (.goals | length), injuries: (.injuries | length), morning_tasks: (.morning_tasks | length), adherence_weeks: (.adherence_weeks | length)}'
  ```
- **Expected Result**: `200 OK` with:
  - `member_name` = `"Morgan Lee"`
  - `member_age` non-null integer
  - `goals` count ≥ 1
  - `injuries` count = 0 (no injuries for Morgan)
  - `morning_tasks` count ≥ 1
  - `adherence_weeks` count = 4
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-003: `/coach/brief` returns full context for high-volume non-demo persona (Drew Robinson)

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/brief`
- **Description**: Verifies that Drew Robinson (5 sessions/week, no injuries, full commercial gym) gets a brief including the expected high-frequency workout context.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_DREW" | jq '{member_name, tier, goals: (.goals | length), adherence_weeks: (.adherence_weeks | length), churn_risk_level: .churn_risk.level}'
  ```
- **Expected Result**: `200 OK` with:
  - `member_name` = `"Drew Robinson"`
  - `goals` count ≥ 1
  - `adherence_weeks` count = 4
  - `churn_risk_level` non-empty string
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-004: Jordan Rivera (Demo) brief is unchanged — hand-authored values preserved

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/brief`
- **Description**: Verifies that the demo member's hand-authored values from `member-context.json` are preserved byte-for-byte after running the seed, specifically: `member_name = "Jordan Rivera"`, `tier = "1:1 Coaching"`, `member_age = 41`.
- **Steps**:
  1. Run the curl command below as-is (using demo member's token)
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_DEMO" | jq '{member_name, member_age, tier, churn_risk_level: .churn_risk.level, adherence_weeks: (.adherence_weeks | map(.pct))}'
  ```
- **Expected Result**: `200 OK` with:
  - `member_name` = `"Jordan Rivera"`
  - `member_age` = `41`
  - `tier` = `"1:1 Coaching"`
  - `churn_risk_level` = `"elevated"` (hand-authored value)
  - `adherence_weeks` pcts = `[100, 100, 75, 50]` (hand-authored declining trend)
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-005: Non-demo personas have non-empty labs in underlying context

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/brief`
- **Description**: The `GET /coach/brief` response currently does not directly surface `labs`/`workouts`/`chat_messages` at the top level; verify indirectly via `/coach/chat` that the context prompt built from these nodes contains lab data for a non-demo persona. This confirms `_fetch_member_context` finds LabResult nodes for Alex Chen.
- **Steps**:
  1. Send a coach chat message asking about Alex's lab results
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_TOKEN_ALEX" -d '{"message":"What are my latest lab results and body composition?"}'  | jq '{reply: .reply[:300], grounded_facts}'
  ```
- **Expected Result**: `200 OK` with a `reply` that references lab values (LDL, HDL, body fat, or similar) or explicitly states what data is available. The `grounded_facts` array is non-empty. The reply must NOT say "no lab data available" or equivalent — the seeded LabResult nodes must be present in context.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-006: Non-demo persona chat references workout history

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /coach/chat`
- **Description**: Verifies that AssessmentWorkout nodes seeded for Morgan Lee (no injuries, general fitness) are picked up by `_fetch_member_context` and surfaced in a coach chat about recent workouts.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_TOKEN_MORGAN" -d '{"message":"What workouts have I done recently?"}' | jq '{reply: .reply[:400], grounded_facts}'
  ```
- **Expected Result**: `200 OK` with a `reply` that mentions at least one workout session or date. The reply must NOT say "no workout history available" — the seeded AssessmentWorkout nodes must be present. `grounded_facts` is non-empty.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-007: Injury-aware persona's chat references active injury

- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /coach/chat`
- **Description**: Verifies that an injured persona (Alex Chen, left knee tendinopathy active) has injury context in chat — confirming that ChatMessage nodes plus injury-aware content were seeded.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/chat' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_TOKEN_ALEX" -d '{"message":"What should I keep in mind for my injury this week?"}' | jq '{reply: .reply[:400], grounded_facts}'
  ```
- **Expected Result**: `200 OK` with:
  - `reply` references the injury (knee, tendinopathy, or restriction language) — the seeded injury data must be present in context
  - `grounded_facts` includes an entry matching `"Active injury: Left knee tendinopathy (active)"` or similar
- [x] Pass <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: Second seed run does not duplicate nodes (idempotency)

- **Scenario**: Running `seed_rich_member_context_all` a second time must not create duplicate LabResult, ChatMessage, or AssessmentWorkout nodes (MERGE on stable IDs).
- **Steps**:
  1. Note the current `/coach/brief` `adherence_weeks` count for Alex Chen (expected: 4)
  2. Re-run the seed: `cd backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.seed`
  3. Re-run the curl command from UAT-API-001
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_ALEX" | jq '{adherence_weeks: (.adherence_weeks | length), goals: (.goals | length)}'
  ```
- **Expected Result**: `200 OK` with identical counts as before the second run — `adherence_weeks` = 4, `goals` ≥ 1. No count should increase (no duplicates).
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-002: Demo member context unchanged after second seed run

- **Scenario**: A second seed run must not alter Jordan Rivera (Demo)'s hand-authored values.
- **Steps**:
  1. After running seed a second time (UAT-EDGE-001), re-check the demo member's brief
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_DEMO" | jq '{member_name, member_age, tier, churn_risk_level: .churn_risk.level}'
  ```
- **Expected Result**: Identical to UAT-API-004: `member_name = "Jordan Rivera"`, `member_age = 41`, `tier = "1:1 Coaching"`, `churn_risk_level = "elevated"`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-EDGE-003: Non-demo personas produce varied data (no copy-paste across accounts)

- **Scenario**: Data must be synthetic and varied — Alex Chen and Morgan Lee must have different member profile values.
- **Steps**:
  1. Fetch Alex Chen's age and Drew Robinson's age from their briefs
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_ALEX" | jq '{member: "alex", member_age, tier}' && curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_DREW" | jq '{member: "drew", member_age, tier}'
  ```
- **Expected Result**: Both calls return `200 OK`. The two `member_age` values are **different** (persona data is varied, not a single value copied to all). Both ages are integers in range 24–58.
- [x] Pass <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: Full seed pipeline produces complete Member Context for all 16 personas

- **Components**: `seed.py` → Neo4j → `_fetch_member_context` → `/coach/brief`
- **Flow**: Run the full seed, then verify that three representative accounts (one injured non-demo, one injury-free non-demo, one demo) each return a complete `/coach/brief` with all required fields populated.
- **Steps**:
  1. Ensure the seed ran (see Prerequisites)
  2. Run brief checks for all three representative personas in sequence
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_ALEX" | jq '{persona:"alex", ok: (.member_name != "" and .member_age != null and (.goals | length) > 0 and (.adherence_weeks | length) == 4)}'
  ```
  Then:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_MORGAN" | jq '{persona:"morgan", ok: (.member_name != "" and .member_age != null and (.goals | length) > 0 and (.adherence_weeks | length) == 4)}'
  ```
  Then:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_TOKEN_DEMO" | jq '{persona:"demo", ok: (.member_name == "Jordan Rivera" and .member_age == 41 and .tier == "1:1 Coaching")}'
  ```
- **Expected Result**: All three calls return `200 OK` with `ok: true`. Any `ok: false` is a failure.
- [x] Pass <!-- 2026-06-08 -->
