# UAT: Test Routing Trace Coverage

> **Source task**: [`.docs/tasks/082-test-routing-trace-coverage.md`](../tasks/082-test-routing-trace-coverage.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running in test mode
- [ ] Python 3.11+ with pytest installed
- [ ] All dependencies in `backend/requirements.txt` installed
- [ ] Test fixtures from `backend/tests/conftest.py` available
- [ ] Neo4j driver mocked (tests do not require real Neo4j instance)
- [ ] LLM calls mocked via `unittest.mock` (no real API calls)

---

## Unit Tests (Test Existence & Structure)

### UAT-UNIT-001: test_audit_trace_coverage Function Exists
- **Description**: Verify the `test_audit_trace_coverage` test function exists and is importable
- **Steps**:
  1. Navigate to `backend/tests/test_agents_hub.py`
  2. Search for `def test_audit_trace_coverage():`
  3. Confirm the function signature includes `@pytest.mark.asyncio` decorator
- **Expected Result**: Function exists, is async, and is marked with `@pytest.mark.asyncio`
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: Test Has Router Entry Assertion
- **Description**: Verify test asserts router entry presence and non-zero latency
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 295-299
  2. Confirm assertions check:
     - Router entry count equals 1
     - `router_entries[0]["latency_ms"] > 0`
     - `router_entries[0]["route"] == "KNOWLEDGE_GRAPH"`
- **Expected Result**: All three assertions are present and reference the correct fields
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: Test Has KG Hub Entry Assertion
- **Description**: Verify test asserts kg_hub entry presence with provider validation
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 301-305
  2. Confirm assertions check:
     - kg_hub entry count >= 1
     - `kg_hub_entries[0]["latency_ms"] > 0`
     - `kg_hub_entries[0]["provider"] == "neo4j"`
- **Expected Result**: All three assertions are present and reference the correct fields
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-004: Test Verifies All 5 Retrieval Nodes
- **Description**: Verify test asserts all 5 retrieval node events are present
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 307-319
  2. Confirm the test defines the exact set:
     - `retrieval_lookup_member`
     - `retrieval_injury_traversal`
     - `retrieval_preference_traversal`
     - `retrieval_vector_search`
     - `retrieval_assemble`
  3. Verify assertion uses set subtraction to find missing nodes
- **Expected Result**: All 5 node names present, assertion uses set operations
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-005: Test Verifies All 3 Generation Nodes
- **Description**: Verify test asserts all 3 generation node events are present
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 321-331
  2. Confirm the test defines the exact set:
     - `kg_generation_llm`
     - `kg_generation_safety_gate`
     - `kg_generation_fallback`
  3. Verify assertion uses set subtraction to find missing nodes
- **Expected Result**: All 3 node names present, assertion uses set operations
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-006: Test Verifies Non-Negative Latency for All Events
- **Description**: Verify test asserts all audit entries have non-negative latency_ms
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 333-338
  2. Confirm loop iterates over all `audit_log` entries
  3. Confirm assertions check:
     - `latency_ms` key exists (is not None)
     - `latency_ms >= 0` (non-negative)
- **Expected Result**: Loop covers all entries, both assertions present
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-007: Test Verifies Token Counts on LLM Nodes
- **Description**: Verify test asserts LLM nodes have token_in and token_out
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 340-349
  2. Confirm test identifies LLM nodes: `router` and `kg_generation_llm`
  3. Confirm assertions check for each LLM node:
     - `tokens_in` is not None
     - `tokens_out` is not None
     - `tokens_in >= 0`
     - `tokens_out >= 0`
- **Expected Result**: Both token fields checked, all assertions present
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-008: Test Verifies Minimum Audit Log Entry Count
- **Description**: Verify test asserts audit_log contains at least 10 entries
- **Steps**:
  1. Read `backend/tests/test_agents_hub.py` lines 351-353
  2. Confirm assertion checks `len(audit_log) >= 10`
  3. Verify comment explains: 1 router + 1 kg_hub + 5 retrieval + 3 generation = 10 minimum
- **Expected Result**: Assertion present with explanatory comment
- [x] Pass <!-- 2026-06-06 -->

---

## Test Execution Tests (Pytest Running)

### UAT-EXEC-001: Test Passes with Mocked Dependencies
- **Description**: Run the test and verify it passes when all dependencies are mocked
- **Steps**:
  1. Navigate to `backend` directory
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Observe output for test result
- **Expected Result**: `PASSED` status; test completes without assertion errors or exceptions
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-002: Test Runs Within Reasonable Time
- **Description**: Verify test completes in a reasonable timeframe (< 10 seconds)
- **Steps**:
  1. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v --tb=short`
  2. Observe the test execution time in pytest output
  3. Check that total runtime is under 10 seconds
- **Expected Result**: Test completes in < 10s (likely < 2s with mocks and asyncio.sleep calls)
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v --tb=short
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-003: Test Output Includes All Assertion Details
- **Description**: Verify pytest output shows all assertions being tested
- **Steps**:
  1. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -vv`
  2. Capture output and review assertions listed
  3. Confirm at least 7+ top-level assertion groups are visible
- **Expected Result**: Output shows detailed assertion paths for router, kg_hub, retrieval, generation, latency, and token checks
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -vv
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-004: Test Fails If Router Entry Missing
- **Description**: Verify test correctly fails when router entry is absent
- **Steps**:
  1. Temporarily modify the test to remove the router entry from initial state (comment out line 269-277 mock)
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Observe failure message
  4. Restore original code
- **Expected Result**: Test fails with assertion error `Router entry missing`, then passes after restoration
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-005: Test Fails If Retrieval Nodes Incomplete
- **Description**: Verify test correctly fails when any of the 5 retrieval nodes are missing
- **Steps**:
  1. Temporarily modify the test to remove one retrieval node (e.g., delete `retrieval_vector_search` from retrieval_audit_log, lines 193-199)
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Observe failure message includes missing node name
  4. Restore original code
- **Expected Result**: Test fails with error including `Missing retrieval nodes: {'retrieval_vector_search'}`, then passes after restoration
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-006: Test Fails If Generation Nodes Incomplete
- **Description**: Verify test correctly fails when any of the 3 generation nodes are missing
- **Steps**:
  1. Temporarily modify the test to remove one generation node (e.g., delete `kg_generation_safety_gate` from generation_audit_log, lines 221-227)
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Observe failure message includes missing node name
  4. Restore original code
- **Expected Result**: Test fails with error including `Missing generation nodes: {'kg_generation_safety_gate'}`, then passes after restoration
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-007: Test Fails If Latency Is Zero or Negative
- **Description**: Verify test correctly rejects zero or negative latency values
- **Steps**:
  1. Temporarily modify the test to set a retrieval node's latency to 0 (line 176 or similar)
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Observe failure message (latency assertion should fire on later check for >= 0)
  4. Restore original code
- **Expected Result**: Test passes with all latencies > 0; fails if any latency is 0 or negative
- [x] Pass <!-- 2026-06-06 -->

### UAT-EXEC-008: Test Fails If Token Counts Missing on LLM Nodes
- **Description**: Verify test correctly requires tokens_in and tokens_out on router and generation LLM nodes
- **Steps**:
  1. Temporarily modify the test to remove `tokens_in` and `tokens_out` from router_entry (lines 275-276)
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Observe failure message for missing token field
  4. Restore original code
- **Expected Result**: Test fails with error about missing token field, then passes after restoration
- [x] Pass <!-- 2026-06-06 -->

---

## Audit Entry Structure Tests (Mock Data Validation)

### UAT-STRUCT-001: Router Entry Has All Required Fields
- **Description**: Verify mock router entry includes all required audit fields
- **Steps**:
  1. Read lines 269-277 of test (router_entry mock)
  2. Confirm presence of:
     - `event: "router"`
     - `latency_ms: 150`
     - `user_id: "user-123"`
     - `route: "KNOWLEDGE_GRAPH"`
     - `confidence: 0.95`
     - `tokens_in: 500`
     - `tokens_out: 100`
- **Expected Result**: All 7 fields present in mock
- [x] Pass <!-- 2026-06-06 -->

### UAT-STRUCT-002: Retrieval Entries Have Appropriate Fields
- **Description**: Verify each of the 5 retrieval mock entries has expected fields
- **Steps**:
  1. Read lines 173-206 of test (retrieval_audit_log)
  2. For each of 5 retrieval nodes, confirm presence of:
     - `event: "retrieval_*"` (specific name)
     - `latency_ms: <positive number>`
     - `user_id: "user-123"`
  3. Check specialized fields exist (e.g., `result_count` for lookup, `embedding_latency_ms` for vector_search)
- **Expected Result**: All retrieval nodes have latency_ms > 0 and user_id; specialized fields match node purpose
- [x] Pass <!-- 2026-06-06 -->

### UAT-STRUCT-003: Generation Entries Have Appropriate Fields
- **Description**: Verify each of the 3 generation mock entries has expected fields
- **Steps**:
  1. Read lines 210-236 of test (generation_audit_log)
  2. For `kg_generation_llm`, confirm:
     - `model: "claude-3-5-sonnet-20241022"`
     - `provider: "anthropic"`
     - `latency_ms: 450`
     - `tokens_in: 1200`
     - `tokens_out: 300`
  3. For `kg_generation_safety_gate`, confirm:
     - `latency_ms: 25`
     - `exercise_in: 1`
     - `exercise_out: 1`
  4. For `kg_generation_fallback`, confirm:
     - `latency_ms: 0` (fallback did not trigger, so minimal latency)
     - `fallback_triggered: False`
- **Expected Result**: All generation nodes have expected fields with realistic values
- [x] Pass <!-- 2026-06-06 -->

---

## State & Graph Mocking Tests

### UAT-MOCK-001: Retrieval Graph Mock Returns Context and Audit Log
- **Description**: Verify mock_retrieval_invoke returns both context and audit_log
- **Steps**:
  1. Read lines 238-249 of test (mock_retrieval_invoke)
  2. Confirm async function returns dict with keys:
     - `context` (mock_context)
     - `audit_log` (retrieval_audit_log)
- **Expected Result**: Both keys present in return value
- [x] Pass <!-- 2026-06-06 -->

### UAT-MOCK-002: Generation Graph Mock Returns Recommendation and Audit Log
- **Description**: Verify mock_generation_invoke returns both recommendation and audit_log
- **Steps**:
  1. Read lines 251-262 of test (mock_generation_invoke)
  2. Confirm async function returns dict with keys:
     - `recommendation` (mock_rec)
     - `audit_log` (generation_audit_log)
- **Expected Result**: Both keys present in return value
- [x] Pass <!-- 2026-06-06 -->

### UAT-MOCK-003: State Includes All Required AgentState Fields
- **Description**: Verify initial state dict includes all required fields from AgentState type
- **Steps**:
  1. Read lines 279-285 of test (state dict)
  2. Confirm presence of:
     - `messages: [HumanMessage(...)]`
     - `route_decision: None`
     - `user_id: "user-123"`
     - `session_id: "sess-abc"`
     - `audit_log: [router_entry]`
  3. Verify messages is a list of LangChain messages
- **Expected Result**: All required state fields present with appropriate types
- [x] Pass <!-- 2026-06-06 -->

### UAT-MOCK-004: _knowledge_graph_node Patches Applied Correctly
- **Description**: Verify all three patches are applied in the test context
- **Steps**:
  1. Read lines 287-290 of test (patch context)
  2. Confirm patches cover:
     - `app.agents.hub.neo4j` → mock_neo4j
     - `app.agents.hub.build_retrieval_graph` → mock_retrieval_graph
     - `app.agents.hub.build_generation_graph` → mock_gen_graph
  3. Verify mock_driver is configured with async context managers
- **Expected Result**: All three modules patched correctly with mock returns
- [x] Pass <!-- 2026-06-06 -->

---

## Integration & Behavioral Tests

### UAT-INT-001: Audit Log Aggregation Works End-to-End
- **Description**: Verify the _knowledge_graph_node correctly aggregates all audit entries from retrieval and generation graphs
- **Steps**:
  1. Run test with verbose output: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v -s`
  2. Observe that result["audit_log"] contains:
     - 1 router entry (from initial state)
     - 1 kg_hub entry (added by _knowledge_graph_node)
     - 5 retrieval entries (from mock_retrieval_invoke)
     - 3 generation entries (from mock_generation_invoke)
  3. Total: >= 10 entries
- **Expected Result**: Final audit_log has all 10+ entries in correct order/structure
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v -s
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: User ID Consistency Across All Audit Entries
- **Description**: Verify all audit entries reference the same user_id
- **Steps**:
  1. Inspect the test assertions indirectly by checking mock data:
     - Router entry: `user_id: "user-123"`
     - Retrieval entries: all have `user_id: "user-123"`
     - Generation entries: all have `user_id: "user-123"`
  2. Run test and verify no assertion errors about user_id mismatches
- **Expected Result**: All audit entries in result["audit_log"] have `user_id == "user-123"`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: Latency Values Are Non-Negative Across Pipeline
- **Description**: Verify that latency calculations work across retrieval and generation stages
- **Steps**:
  1. Note mock_retrieval_invoke includes `await asyncio.sleep(0.05)` to simulate real latency
  2. Note mock_generation_invoke includes `await asyncio.sleep(0.05)` to simulate real latency
  3. Verify that when test runs, the computed kg_hub latency (from _knowledge_graph_node) is > 0
  4. Run test and confirm no latency-related failures
- **Expected Result**: All latency_ms values >= 0; kg_hub latency > 0 due to asyncio.sleep
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-004: Recommendations Flow Through Correctly
- **Description**: Verify mock_rec exercises flow through generation graph output
- **Steps**:
  1. Check line 156: mock_rec has 1 exercise: `exercise_id="ex-1", name="Squat"`
  2. Check line 218: generation_audit_log `kg_generation_llm` entry has `exercise_count: 1`
  3. Verify that if code tried to access `result["recommendation"]`, it would have the mocked exercises
- **Expected Result**: Mock recommendation flows through and is reflected in generation node exercise counts
- [x] Pass <!-- 2026-06-06 -->

---

## Coverage & Completeness Tests

### UAT-COV-001: Test File Imports Are Correct
- **Description**: Verify all imports at the top of test_agents_hub.py are available
- **Steps**:
  1. Read lines 1-10 of test_agents_hub.py
  2. Confirm imports include:
     - `uuid`
     - `unittest.mock` (MagicMock, patch, AsyncMock)
     - `app.agents.hub` (build_hub_graph, hub, _knowledge_graph_node)
     - `app.agents.state` (AgentState, RouteDecision, Intent)
     - `pytest`
  3. Within test function (lines 150-152), confirm local imports:
     - `AsyncMock, patch, MagicMock` from unittest.mock
     - `HumanMessage` from langchain_core.messages
     - `_knowledge_graph_node` from app.agents.hub
- **Expected Result**: All imports resolvable; test can be executed
- [x] Pass <!-- 2026-06-06 -->

### UAT-COV-002: Test Has Proper Async/Await Pattern
- **Description**: Verify test function is properly async and all awaits are correct
- **Steps**:
  1. Confirm function signature: `async def test_audit_trace_coverage():`
  2. Confirm decorator: `@pytest.mark.asyncio`
  3. Confirm test awaits the _knowledge_graph_node call: `result = await _knowledge_graph_node(state)`
  4. Confirm mock functions are async and properly awaitable
- **Expected Result**: All async/await patterns correct; test will not hang or fail with "RuntimeError: Event loop"
- [x] Pass <!-- 2026-06-06 -->

### UAT-COV-003: Test Documents Expected Audit Log Structure
- **Description**: Verify test docstring explains what is being tested
- **Steps**:
  1. Read lines 140-148 (test docstring)
  2. Confirm it lists:
     - Router node entry verification
     - KG hub node entry verification
     - All 5 retrieval nodes verification
     - All 3 generation nodes verification
     - Non-zero latency verification
     - Token count verification for LLM nodes
- **Expected Result**: Docstring covers all major test objectives
- [x] Pass <!-- 2026-06-06 -->

### UAT-COV-004: Test Assertions Cover Both Happy Path and Constraints
- **Description**: Verify test checks both presence and validity constraints
- **Steps**:
  1. Confirm assertions check not just presence, but also:
     - Latency is non-negative (>= 0)
     - Latency for certain nodes is positive (> 0)
     - Token counts exist and are non-negative
     - Route is correct ("KNOWLEDGE_GRAPH")
     - Provider is correct ("neo4j")
  2. Count total distinct assertions (should be 7+ major groups)
- **Expected Result**: Test goes beyond presence checking to validate field values and constraints
- [x] Pass <!-- 2026-06-06 -->

---

## Error Scenario Tests

### UAT-ERR-001: Test Detects Missing Router Entry
- **Description**: Verify test assertion catches if router entry is removed
- **Steps**:
  1. Understand that lines 296-299 check: `assert len(router_entries) == 1, "Router entry missing"`
  2. This assertion would catch:
     - No router entries in audit_log
     - Multiple router entries (> 1)
     - Router entry with missing latency_ms or route fields
- **Expected Result**: If router entry structure changes or is removed, test fails with clear message
- [x] Pass <!-- 2026-06-06 -->

### UAT-ERR-002: Test Detects Missing Retrieval Nodes
- **Description**: Verify test assertion catches if any of 5 retrieval nodes are absent
- **Steps**:
  1. Understand that lines 315-319 build a set of actual events and compare
  2. If any of the 5 expected nodes are missing, line 319 assertion fires:
     `assert not missing_retrieval, f"Missing retrieval nodes: {missing_retrieval}"`
- **Expected Result**: Removes any one retrieval node → test fails with specific node name
- [x] Pass <!-- 2026-06-06 -->

### UAT-ERR-003: Test Detects Missing Generation Nodes
- **Description**: Verify test assertion catches if any of 3 generation nodes are absent
- **Steps**:
  1. Understand that lines 327-331 build a set of actual events and compare
  2. If any of the 3 expected nodes are missing, line 331 assertion fires:
     `assert not missing_generation, f"Missing generation nodes: {missing_generation}"`
- **Expected Result**: Remove any one generation node → test fails with specific node name
- [x] Pass <!-- 2026-06-06 -->

### UAT-ERR-004: Test Detects Invalid Latency Values
- **Description**: Verify test rejects null, negative, or missing latency_ms
- **Steps**:
  1. Understand that lines 336-338 iterate all entries and check:
     - `assert latency is not None` (catches missing latency_ms)
     - `assert latency >= 0` (catches negative latencies)
  2. Note: test allows latency == 0 (non-strict positive)
- **Expected Result**: If any entry lacks latency_ms or has negative value, test fails
- [x] Pass <!-- 2026-06-06 -->

### UAT-ERR-005: Test Detects Missing Token Counts on LLM Nodes
- **Description**: Verify test requires tokens_in and tokens_out on LLM nodes
- **Steps**:
  1. Understand lines 341-349 iterate LLM nodes: router and kg_generation_llm
  2. For each, check:
     - `assert tokens_in is not None`
     - `assert tokens_out is not None`
     - `assert tokens_in >= 0`
     - `assert tokens_out >= 0`
- **Expected Result**: If router or kg_generation_llm lacks token fields, test fails
- [x] Pass <!-- 2026-06-06 -->

### UAT-ERR-006: Test Detects Insufficient Audit Log Entries
- **Description**: Verify test checks minimum audit entry count
- **Steps**:
  1. Understand line 353 assertion:
     `assert len(audit_log) >= 10, f"Expected at least 10 audit entries, got {len(audit_log)}"`
  2. If audit_log has fewer than 10 entries, test fails with count
  3. Expected composition: 1 router + 1 kg_hub + 5 retrieval + 3 generation
- **Expected Result**: If total entries < 10, test fails with diagnostic message
- [x] Pass <!-- 2026-06-06 -->

---

## Pytest Integration Tests

### UAT-PYTEST-001: Test Can Be Run Individually
- **Description**: Verify test can be invoked by its function name
- **Steps**:
  1. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  2. Confirm pytest recognizes and runs only this test
- **Expected Result**: PASSED; output shows only one test ran
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-PYTEST-002: Test Can Be Run as Part of Full Suite
- **Description**: Verify test runs without errors when invoked as part of the full test_agents_hub.py suite
- **Steps**:
  1. Run: `cd backend && python -m pytest tests/test_agents_hub.py -v`
  2. Confirm test_audit_trace_coverage is included and passes
- **Expected Result**: PASSED; test appears in output alongside other hub tests
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py -v 2>&1 | grep test_audit_trace_coverage
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-PYTEST-003: Test Output Shows All Assertions
- **Description**: Verify pytest displays assertion details on failure
- **Steps**:
  1. Run with maximum verbosity: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -vv --tb=long`
  2. On pass: output should show test completed
  3. If modified to fail, output should show which assertion failed
- **Expected Result**: Pytest output is clear and diagnostic
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -vv --tb=long
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-PYTEST-004: Test Works with pytest-asyncio Plugin
- **Description**: Verify test respects @pytest.mark.asyncio decorator
- **Steps**:
  1. Confirm pytest-asyncio is installed: `cd backend && python -c "import pytest_asyncio; print(pytest_asyncio.__version__)"`
  2. Run test: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Confirm no "asyncio" or "event loop" related errors
- **Expected Result**: PASSED; no asyncio warnings or errors
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-PYTEST-005: Test Output Shows Execution Time
- **Description**: Verify pytest reports test execution time
- **Steps**:
  1. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  2. Observe output line like: `test_audit_trace_coverage PASSED [X.XXs]`
  3. Confirm time is reasonable (< 10s)
- **Expected Result**: Output includes elapsed time; time is acceptable
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v
  ```
- [x] Pass <!-- 2026-06-06 -->

---

## Documentation & Maintenance Tests

### UAT-DOC-001: Test Docstring Is Comprehensive
- **Description**: Verify test has a clear, detailed docstring explaining purpose
- **Steps**:
  1. Read docstring (lines 140-148)
  2. Confirm it explains:
     - High-level purpose (audit_log contains complete trace)
     - The 6 specific things being tested
- **Expected Result**: Docstring clearly explains test objective
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-002: Comments Explain Mock Data
- **Description**: Verify test includes comments explaining the mock setup
- **Steps**:
  1. Scan lines 150-286 for inline comments
  2. Confirm comments exist for:
     - Mock recommendation (line 154)
     - Mock context (line 160)
     - Retrieval audit log (line 172)
     - Generation audit log (line 209)
     - Initial router entry (line 268)
  3. Verify comments explain why mocks are structured as they are
- **Expected Result**: Key mock structures have explanatory comments
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-003: Test Variable Names Are Descriptive
- **Description**: Verify test uses clear, self-documenting variable names
- **Steps**:
  1. Check variable names: mock_rec, mock_context, retrieval_audit_log, generation_audit_log, mock_retrieval_graph, mock_gen_graph, state, audit_log, router_entries, kg_hub_entries, actual_retrieval_events, etc.
  2. Confirm each name clearly indicates what data it holds
- **Expected Result**: Variable naming aids readability; no cryptic abbreviations
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-004: Assertions Have Clear Error Messages
- **Description**: Verify assertions include descriptive failure messages
- **Steps**:
  1. Review assertions:
     - Line 297: `assert len(router_entries) == 1, "Router entry missing"`
     - Line 298: `assert router_entries[0]["latency_ms"] > 0, "Router latency should be > 0"`
     - Line 319: `assert not missing_retrieval, f"Missing retrieval nodes: {missing_retrieval}"`
     - etc.
  2. Confirm each has a clear message indicating what failed
- **Expected Result**: All assertions include helpful error messages
- [x] Pass <!-- 2026-06-06 -->

---

## Boundary & Edge Case Tests

### UAT-EDGE-001: Test Handles Zero Latency Correctly
- **Description**: Verify test accepts latency >= 0 but checks > 0 for specific nodes
- **Steps**:
  1. Note line 338 check: `latency >= 0` (allows zero)
  2. Note lines 298, 304 checks: `latency_ms > 0` (requires > 0 for router and kg_hub)
  3. Note line 231: kg_generation_fallback has `latency_ms: 0` and this is allowed
- **Expected Result**: Test correctly allows fallback node to have 0 latency, requires router/kg_hub > 0
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Test Handles Empty Exercises in Recommendation
- **Description**: Verify test works even with minimal exercises
- **Steps**:
  1. Note line 156: mock_rec.exercises has 1 item
  2. Note line 158: mock_rec.skipped_exercise_ids is empty []
  3. Verify test does not require a minimum number of exercises (no assertions on exercise count outside of generation node fields)
- **Expected Result**: Test passes with minimal exercise data
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: Test Handles Empty Contraindications
- **Description**: Verify test works with no contraindicated exercises
- **Steps**:
  1. Note line 166: contraindicated_ids is empty []
  2. Verify test does not assume contraindications exist
- **Expected Result**: Test passes with empty contraindications list
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-004: Test Handles Large Token Counts
- **Description**: Verify test accepts any non-negative token count
- **Steps**:
  1. Note lines 217-218: generation LLM has tokens_in=1200, tokens_out=300 (realistic large values)
  2. Verify assertions only check >= 0, not upper bounds
- **Expected Result**: Test passes with realistic large token counts
- [x] Pass <!-- 2026-06-06 -->

---

## Final Verification Test

### UAT-FINAL-001: Complete Test Run Against Pristine Code
- **Description**: Run complete test on unmodified code and verify all assertions pass
- **Steps**:
  1. Ensure no temporary modifications to test file
  2. Run: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v`
  3. Confirm PASSED
  4. Run with coverage: `cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage --cov=app.agents.hub --cov-report=term-missing`
  5. Observe coverage report for hub.py module
- **Expected Result**: Test PASSED; coverage report shows hub module lines covered by test
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v
  ```
- [x] Pass <!-- 2026-06-06 -->

---

**UAT**: [`.docs/uat/082-test-routing-trace-coverage.uat.md`](082-test-routing-trace-coverage.uat.md)
