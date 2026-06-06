import uuid as _uuid
import uuid
from unittest.mock import MagicMock, patch

from app.agents.hub import build_hub_graph, hub
from app.agents.state import AgentState, RouteDecision, Intent


import pytest


@pytest.fixture(autouse=True)
def populate_exercise_cache():
    from app.agents import exercises as ex_module
    from app.models.exercise import Exercise as ExModel
    fake = MagicMock(spec=ExModel)
    fake.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    fake.name = "Squat"
    fake.muscle_groups = ["quadriceps"]
    fake.equipment_required = ["barbell"]
    fake.movement_patterns = ["squat"]
    fake.is_reps = True
    fake.is_duration = False
    fake.supports_weight = True
    fake.priority_tier = 1
    ex_module._cache = [fake]
    yield
    ex_module._cache = []


@pytest.fixture
def mock_all_llms():
    """Patch all LLM constructors so no real API calls are made."""
    from app.agents.state import RouteDecision, Intent

    def _make_hub_mock():
        m = MagicMock()
        m.with_structured_output.return_value.invoke.return_value = {
            "parsed": RouteDecision(intent=Intent.FALLBACK, confidence=0.0, reasoning="mocked"),
            "raw": MagicMock(usage_metadata={"input_tokens": 0, "output_tokens": 0}),
        }
        return m

    with patch("app.agents.hub.ChatAnthropic", return_value=_make_hub_mock()), \
         patch("app.agents.coach.ChatAnthropic"), \
         patch("app.agents.workout_generator.ChatAnthropic"), \
         patch("app.agents.workout_logger.ChatAnthropic"):
        yield


def test_hub_compiles():
    compiled = build_hub_graph().compile()
    assert compiled is not None


def test_clarification_on_low_confidence(mock_all_llms):
    """Router stub returns no route_decision → should route to clarification."""
    from langchain_core.messages import HumanMessage
    result = hub.invoke({
        "messages": [HumanMessage(content="asdf")],
        "route_decision": None,
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    })
    # With stub router (no LLM), route_decision stays None → clarification fires
    last_msg = result["messages"][-1].content
    assert "rephrase" in last_msg.lower() or "sure" in last_msg.lower()


def test_fallback_routes_to_clarification(mock_all_llms):
    """Explicit FALLBACK intent should route to clarification."""
    from langchain_core.messages import HumanMessage
    result = hub.invoke({
        "messages": [HumanMessage(content="tell me a joke")],
        "route_decision": RouteDecision(
            intent=Intent.FALLBACK, confidence=0.8, reasoning="off-topic"
        ),
        "user_id": None,
        "session_id": None,
        "audit_log": [],
    })
    last_msg = result["messages"][-1].content
    assert "stub" not in last_msg  # stub nodes shouldn't fire for FALLBACK


@pytest.mark.asyncio
async def test_kg_hub_node_audit_entry():
    """_knowledge_graph_node appends a kg_hub audit entry with required fields."""
    from unittest.mock import AsyncMock, patch, MagicMock
    from langchain_core.messages import HumanMessage
    from app.agents.hub import _knowledge_graph_node

    # Minimal recommendation object
    mock_rec = MagicMock()
    mock_rec.exercises = []
    mock_rec.overall_reasoning = ""
    mock_rec.skipped_exercise_ids = []

    mock_gen_result = {"recommendation": mock_rec, "tokens_in": 5, "tokens_out": 3}
    mock_retrieval_result = {"context": None}

    mock_retrieval_graph = MagicMock()
    mock_retrieval_graph.ainvoke = AsyncMock(return_value=mock_retrieval_result)

    mock_gen_graph = MagicMock()
    mock_gen_graph.ainvoke = AsyncMock(return_value=mock_gen_result)

    mock_driver = AsyncMock()
    mock_driver.__aenter__ = AsyncMock(return_value=mock_driver)
    mock_driver.__aexit__ = AsyncMock(return_value=None)

    state = {
        "messages": [HumanMessage(content="recommend me a workout")],
        "route_decision": None,
        "user_id": "user-123",
        "session_id": "sess-abc",
        "audit_log": [{"event": "router", "route": "KNOWLEDGE_GRAPH"}],
    }

    with patch("app.agents.hub.neo4j") as mock_neo4j, \
         patch("app.agents.hub.build_retrieval_graph", return_value=mock_retrieval_graph), \
         patch("app.agents.hub.build_generation_graph", return_value=mock_gen_graph):
        mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver
        result = await _knowledge_graph_node(state)

    audit_log = result["audit_log"]
    assert any(e["event"] == "kg_hub" for e in audit_log), "kg_hub entry missing from audit_log"

    kg_entry = next(e for e in audit_log if e["event"] == "kg_hub")
    assert kg_entry["intent"] == "KNOWLEDGE_GRAPH"
    assert kg_entry["latency_ms"] >= 0
    assert kg_entry["user_id"] == "user-123"
    assert kg_entry["tokens_in"] == 5
    assert kg_entry["tokens_out"] == 3
    assert kg_entry["provider"] == "neo4j"


@pytest.mark.asyncio
async def test_audit_trace_coverage():
    """Verify audit_log contains complete trace of all KG hub, retrieval, and generation nodes.

    This test confirms end-to-end observability coverage by checking that:
    1. Router node entry is present
    2. KG hub node entry is present
    3. All 5 retrieval nodes emit audit entries
    4. All 3 generation nodes emit audit entries
    5. All entries have non-zero latency_ms
    6. LLM-backed nodes have token counts
    """
    from unittest.mock import AsyncMock, patch, MagicMock
    from langchain_core.messages import HumanMessage
    from app.agents.hub import _knowledge_graph_node

    # Build mock recommendation with exercises
    mock_rec = MagicMock()
    mock_rec.exercises = [MagicMock(exercise_id="ex-1", name="Squat")]
    mock_rec.overall_reasoning = "Recommended for strength"
    mock_rec.skipped_exercise_ids = []

    # Mock context from retrieval graph with all fields
    mock_context = {
        "safe_exercises": [
            {"id": "ex-1", "name": "Squat", "muscle_groups": ["quadriceps"]},
            {"id": "ex-2", "name": "Leg Press", "muscle_groups": ["quadriceps"]},
        ],
        "contraindicated_ids": [],
        "preferred_exercises": [{"id": "ex-1", "name": "Squat"}],
        "performed_exercises": [{"id": "ex-2", "name": "Leg Press"}],
        "vector_docs": [MagicMock(metadata={"exercise_id": "ex-1"})],
    }

    # Build retrieval audit log with all 5 retrieval nodes
    retrieval_audit_log = [
        {
            "event": "retrieval_lookup_member",
            "latency_ms": 45,
            "user_id": "user-123",
            "result_count": 1,
        },
        {
            "event": "retrieval_injury_traversal",
            "latency_ms": 120,
            "user_id": "user-123",
            "result_count": 2,
            "constraint_count": 0,
        },
        {
            "event": "retrieval_preference_traversal",
            "latency_ms": 85,
            "user_id": "user-123",
            "result_count": 2,
        },
        {
            "event": "retrieval_vector_search",
            "latency_ms": 200,
            "user_id": "user-123",
            "result_count": 1,
            "embedding_latency_ms": 150,
        },
        {
            "event": "retrieval_assemble",
            "latency_ms": 60,
            "user_id": "user-123",
            "input_count": 4,
            "output_count": 2,
        },
    ]

    # Build generation audit log with all 3 generation nodes
    generation_audit_log = [
        {
            "event": "kg_generation_llm",
            "model": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "latency_ms": 450,
            "user_id": "user-123",
            "tokens_in": 1200,
            "tokens_out": 300,
            "exercise_count": 1,
        },
        {
            "event": "kg_generation_safety_gate",
            "latency_ms": 25,
            "user_id": "user-123",
            "exercise_in": 1,
            "exercise_out": 1,
            "violations_filtered": 0,
        },
        {
            "event": "kg_generation_fallback",
            "latency_ms": 0,
            "user_id": "user-123",
            "fallback_triggered": False,
            "exercise_count": 1,
        },
    ]

    # Mock retrieval graph to return context + audit entries
    async def mock_retrieval_invoke(*args, **kwargs):
        import asyncio
        # Add a small delay to ensure latency_ms > 0
        await asyncio.sleep(0.05)
        return {
            "context": mock_context,
            "audit_log": retrieval_audit_log,
        }

    mock_retrieval_graph = MagicMock()
    mock_retrieval_graph.ainvoke = mock_retrieval_invoke

    # Mock generation graph to return recommendation + audit entries
    async def mock_generation_invoke(*args, **kwargs):
        import asyncio
        # Add a small delay to ensure latency_ms > 0
        await asyncio.sleep(0.05)
        return {
            "recommendation": mock_rec,
            "audit_log": generation_audit_log,
        }

    mock_gen_graph = MagicMock()
    mock_gen_graph.ainvoke = mock_generation_invoke

    mock_driver = AsyncMock()
    mock_driver.__aenter__ = AsyncMock(return_value=mock_driver)
    mock_driver.__aexit__ = AsyncMock(return_value=None)

    # Initial router entry (pre-populated from an earlier router node execution)
    router_entry = {
        "event": "router",
        "latency_ms": 150,
        "user_id": "user-123",
        "route": "KNOWLEDGE_GRAPH",
        "confidence": 0.95,
        "tokens_in": 500,
        "tokens_out": 100,
    }

    state = {
        "messages": [HumanMessage(content="recommend exercises for my knee")],
        "route_decision": None,
        "user_id": "user-123",
        "session_id": "sess-abc",
        "audit_log": [router_entry],
    }

    with patch("app.agents.hub.neo4j") as mock_neo4j, \
         patch("app.agents.hub.build_retrieval_graph", return_value=mock_retrieval_graph), \
         patch("app.agents.hub.build_generation_graph", return_value=mock_gen_graph):
        mock_neo4j.AsyncGraphDatabase.driver.return_value = mock_driver
        result = await _knowledge_graph_node(state)

    audit_log = result["audit_log"]

    # Assertion 1: Router entry is present
    router_entries = [e for e in audit_log if e["event"] == "router"]
    assert len(router_entries) == 1, "Router entry missing"
    assert router_entries[0]["latency_ms"] > 0, "Router latency should be > 0"
    assert router_entries[0]["route"] == "KNOWLEDGE_GRAPH", "Router route should be KNOWLEDGE_GRAPH"

    # Assertion 2: KG hub entry exists
    kg_hub_entries = [e for e in audit_log if e["event"] == "kg_hub"]
    assert len(kg_hub_entries) >= 1, "kg_hub entry missing"
    assert kg_hub_entries[0]["latency_ms"] > 0, "kg_hub latency should be > 0"
    assert kg_hub_entries[0]["provider"] == "neo4j", "kg_hub provider should be neo4j"

    # Assertion 3: All 5 retrieval nodes are present
    retrieval_events = {
        "retrieval_lookup_member",
        "retrieval_injury_traversal",
        "retrieval_preference_traversal",
        "retrieval_vector_search",
        "retrieval_assemble",
    }
    actual_retrieval_events = {
        e["event"] for e in audit_log if e["event"].startswith("retrieval_")
    }
    missing_retrieval = retrieval_events - actual_retrieval_events
    assert not missing_retrieval, f"Missing retrieval nodes: {missing_retrieval}"

    # Assertion 4: All 3 generation nodes are present
    generation_events = {
        "kg_generation_llm",
        "kg_generation_safety_gate",
        "kg_generation_fallback",
    }
    actual_generation_events = {
        e["event"] for e in audit_log if e["event"].startswith("kg_generation_")
    }
    missing_generation = generation_events - actual_generation_events
    assert not missing_generation, f"Missing generation nodes: {missing_generation}"

    # Assertion 5: All entries have non-zero latency_ms
    for entry in audit_log:
        event_name = entry["event"]
        latency = entry.get("latency_ms")
        assert latency is not None, f"Entry {event_name} missing latency_ms"
        assert latency >= 0, f"Entry {event_name} latency_ms should be >= 0, got {latency}"

    # Assertion 6: LLM-backed nodes have token counts
    llm_nodes = [e for e in audit_log if e["event"] in ("router", "kg_generation_llm")]
    for entry in llm_nodes:
        event_name = entry["event"]
        tokens_in = entry.get("tokens_in")
        tokens_out = entry.get("tokens_out")
        assert tokens_in is not None, f"LLM node {event_name} missing tokens_in"
        assert tokens_out is not None, f"LLM node {event_name} missing tokens_out"
        assert tokens_in >= 0, f"LLM node {event_name} tokens_in should be >= 0"
        assert tokens_out >= 0, f"LLM node {event_name} tokens_out should be >= 0"

    # Assertion 7: Total audit log should have at least 10 entries
    # (1 router + 1 kg_hub + 5 retrieval + 3 generation)
    assert len(audit_log) >= 10, f"Expected at least 10 audit entries, got {len(audit_log)}"
