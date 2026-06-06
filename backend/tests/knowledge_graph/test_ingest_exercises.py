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


def test_load_exercises_returns_50():
    """exercises.json contains exactly 50 records."""
    data = load_exercises()
    assert len(data) == 50
    assert all("id" in ex and "joints_loaded" in ex for ex in data)
