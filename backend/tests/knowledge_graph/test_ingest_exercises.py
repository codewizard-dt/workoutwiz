from typing import Any
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_exercises import ingest_exercises, load_exercises

SAMPLE: list[dict[str, Any]] = [
    {
        "id": "aaaaaaaa-0000-0000-0000-000000000001",
        "name": "Test Squat",
        "muscle_groups": ["quads"],
        "joints_loaded": ["knee"],
        "movement_patterns": ["squat"],
        "equipment_required": [],
        "is_bilateral": True,
        "side": None,
        "priority_tier": 1,
        "is_reps": True,
        "is_duration": False,
        "supports_weight": True,
        "estimated_rep_duration": 1.0,
        "bilateral_pair_id": None,
    }
]


def test_ingest_exercises_calls_merge_and_edge_pass():
    """ingest_exercises runs MERGE for each exercise then the edge pass."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    result = ingest_exercises(mock_driver, SAMPLE)

    assert result == 1
    # session.run called at least twice: 1 MERGE per exercise + 1 edge pass
    assert mock_session.run.call_count >= 2


def test_ingest_exercises_creates_typed_nodes_and_edges():
    """ingest_exercises issues TARGETS, REQUIRES, HAS_PATTERN MERGE passes."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    sample_with_data: list[dict[str, Any]] = [
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000002",
            "name": "Barbell Bench Press",
            "muscle_groups": ["chest", "triceps"],
            "joints_loaded": ["shoulder", "elbow"],
            "movement_patterns": ["upper push - horizontal"],
            "equipment_required": ["Barbell"],
            "is_bilateral": True,
            "side": None,
            "priority_tier": 1,
            "is_reps": True,
            "is_duration": False,
            "supports_weight": True,
            "estimated_rep_duration": 2.0,
            "bilateral_pair_id": None,
        }
    ]

    result = ingest_exercises(mock_driver, sample_with_data)

    assert result == 1

    # Collect all Cypher strings from session.run calls
    all_cypher = [
        str(call.args[0]) if call.args else ""
        for call in mock_session.run.call_args_list
    ]

    # Each new pass must appear in at least one call
    assert any("MERGE (m:Muscle" in c for c in all_cypher), "No Muscle MERGE found"
    assert any(":TARGETS" in c for c in all_cypher), "No TARGETS edge found"
    assert any(":REQUIRES" in c for c in all_cypher), "No REQUIRES edge found"
    assert any(":HAS_PATTERN" in c for c in all_cypher), "No HAS_PATTERN edge found"


def test_ingest_exercises_skips_typed_passes_for_empty_arrays():
    """ingest_exercises does not issue typed-node passes when arrays are empty."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    empty_sample: list[dict[str, Any]] = [
        {
            "id": "aaaaaaaa-0000-0000-0000-000000000003",
            "name": "Bodyweight Squat",
            "muscle_groups": [],
            "joints_loaded": [],
            "movement_patterns": [],
            "equipment_required": [],
            "is_bilateral": True,
            "side": None,
            "priority_tier": 2,
            "is_reps": True,
            "is_duration": False,
            "supports_weight": False,
            "estimated_rep_duration": 1.5,
            "bilateral_pair_id": None,
        }
    ]

    ingest_exercises(mock_driver, empty_sample)

    all_cypher = [
        str(call.args[0]) if call.args else ""
        for call in mock_session.run.call_args_list
    ]

    # Typed-node passes must NOT be called for empty arrays
    assert not any("MERGE (m:Muscle" in c for c in all_cypher), "Unexpected Muscle MERGE"
    assert not any(":TARGETS" in c for c in all_cypher), "Unexpected TARGETS edge"
    assert not any(":REQUIRES" in c for c in all_cypher), "Unexpected REQUIRES edge"
    assert not any(":HAS_PATTERN" in c for c in all_cypher), "Unexpected HAS_PATTERN edge"


def test_load_exercises_returns_50():
    """exercises.json contains exactly 50 records."""
    data = load_exercises()
    assert len(data) == 50
    assert all("id" in ex and "joints_loaded" in ex for ex in data)
