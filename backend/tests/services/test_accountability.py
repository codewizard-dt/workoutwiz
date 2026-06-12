from app.services.accountability import rank_action_items
from app.schemas.coach import AdherenceWeek, ChurnRisk


def test_high_churn_yields_action_item():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=80)],
        churn_risk=ChurnRisk(level="high", reasons=["3 missed workouts"]),
    )
    assert len(result) == 1
    assert result[0].priority == "high"


def test_low_adherence_yields_high_priority():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=40)],
        churn_risk=ChurnRisk(level="low", reasons=[]),
    )
    assert len(result) == 1
    assert result[0].priority == "high"


def test_medium_adherence_yields_medium_priority():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=60)],
        churn_risk=ChurnRisk(level="low", reasons=[]),
    )
    assert len(result) == 1
    assert result[0].priority == "medium"


def test_healthy_member_yields_empty():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=90)],
        churn_risk=ChurnRisk(level="low", reasons=[]),
    )
    assert result == []


def test_high_churn_plus_low_adherence_sorted_high_first():
    result = rank_action_items(
        member_id="m1", member_name="Alice",
        adherence_weeks=[AdherenceWeek(week_of="2026-06-01", pct=40)],
        churn_risk=ChurnRisk(level="high", reasons=["dropout pattern"]),
    )
    assert all(r.priority == "high" for r in result)
    assert len(result) == 2
