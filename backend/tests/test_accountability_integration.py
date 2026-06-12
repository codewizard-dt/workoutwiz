import pytest
import pytest_asyncio
from app.services.accountability import rank_action_items
from app.schemas.coach import AdherenceWeek, ChurnRisk


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations():
    """No-op override: this test needs no database."""
    yield


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_exercises(apply_migrations):
    """No-op override: this test needs no database."""
    yield


def test_low_adherence_member_yields_ranked_action_item():
    """End-to-end: CoachBriefResponse signals flow into rank_action_items correctly."""
    adherence_weeks = [
        AdherenceWeek(week_of="2026-05-18", pct=80),
        AdherenceWeek(week_of="2026-05-25", pct=70),
        AdherenceWeek(week_of="2026-06-01", pct=40),  # recent drop
    ]
    churn_risk = ChurnRisk(level="medium", reasons=["decreasing workout frequency"])

    items = rank_action_items(
        member_id="test-member",
        member_name="Test Member",
        adherence_weeks=adherence_weeks,
        churn_risk=churn_risk,
    )

    assert len(items) >= 1, "Expected at least one action item for low-adherence member"
    assert items[0].priority == "high", f"Expected high priority, got: {items[0].priority}"
    assert "40" in items[0].reason, "Expected adherence pct in reason"
