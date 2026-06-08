"""Tests for seed_rich_member_context_all — verifies that every non-demo persona
gets LabResult, ChatMessage, and AssessmentWorkout nodes, and that the function
is idempotent (MERGE-based, no extra nodes on re-run).
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, call
import random

from faker import Faker

from app.knowledge_graph.seed import (
    PERSONAS,
    _DEMO_MEMBER_EMAIL,
    seed_rich_member_context_all,
)


def _make_driver_and_session() -> tuple[MagicMock, MagicMock]:
    """Return a (driver, session) mock pair wired for the context-manager protocol."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return mock_driver, mock_session


def _make_member_map() -> dict[str, uuid.UUID]:
    """Build a member_map with a stable UUID per persona email."""
    return {p["email"]: uuid.uuid5(uuid.NAMESPACE_URL, p["email"]) for p in PERSONAS}


# ---------------------------------------------------------------------------
# Helpers to extract cypher calls from a mock session
# ---------------------------------------------------------------------------

def _cypher_calls(mock_session: MagicMock) -> list[str]:
    """Return the first positional arg (the Cypher string) from every session.run call."""
    return [c.args[0] if c.args else "" for c in mock_session.run.call_args_list]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSeedRichMemberContextAll:
    """Unit tests for seed_rich_member_context_all using a mocked neo4j driver."""

    def setup_method(self) -> None:
        # Reset random seeds for determinism
        random.seed(42)
        Faker.seed(42)
        self.fake = Faker()
        self.member_map = _make_member_map()

    # ------------------------------------------------------------------
    # Coverage: every non-demo persona gets the 3 node types
    # ------------------------------------------------------------------

    def test_every_non_demo_persona_gets_lab_results(self) -> None:
        """Each non-demo persona must trigger at least 2 LabResult MERGE statements."""
        mock_driver, mock_session = _make_driver_and_session()

        seed_rich_member_context_all(mock_driver, self.member_map, self.fake)

        cypher_list = _cypher_calls(mock_session)
        non_demo_personas = [p for p in PERSONAS if p["email"] != _DEMO_MEMBER_EMAIL]

        for persona in non_demo_personas:
            member_id = str(self.member_map[persona["email"]])
            blood_id = f"{member_id}:labs:blood_panel"
            dexa_id = f"{member_id}:labs:dexa_scan"

            # Check that session.run was called with parameters containing both lab IDs
            call_kwargs = [
                c.kwargs if c.kwargs else {}
                for c in mock_session.run.call_args_list
            ]
            ids_in_kwargs = {kw.get("id") for kw in call_kwargs}

            assert blood_id in ids_in_kwargs, (
                f"blood_panel lab not seeded for {persona['email']}"
            )
            assert dexa_id in ids_in_kwargs, (
                f"dexa_scan lab not seeded for {persona['email']}"
            )

    def test_every_non_demo_persona_gets_chat_messages(self) -> None:
        """Each non-demo persona must have at least one ChatMessage MERGE call."""
        mock_driver, mock_session = _make_driver_and_session()

        seed_rich_member_context_all(mock_driver, self.member_map, self.fake)

        non_demo_personas = [p for p in PERSONAS if p["email"] != _DEMO_MEMBER_EMAIL]
        cypher_list = _cypher_calls(mock_session)

        for persona in non_demo_personas:
            member_id = str(self.member_map[persona["email"]])
            # ChatMessage IDs follow the pattern uuid5(..., f"{member_id}:chat:{i}")
            chat_id_0 = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{member_id}:chat:0"))
            ids_in_kwargs = {
                c.kwargs.get("id") for c in mock_session.run.call_args_list if c.kwargs
            }
            assert chat_id_0 in ids_in_kwargs, (
                f"No ChatMessage seeded for {persona['email']}"
            )

    def test_every_non_demo_persona_gets_assessment_workouts(self) -> None:
        """Each non-demo persona must have at least one AssessmentWorkout MERGE call."""
        mock_driver, mock_session = _make_driver_and_session()

        seed_rich_member_context_all(mock_driver, self.member_map, self.fake)

        non_demo_personas = [p for p in PERSONAS if p["email"] != _DEMO_MEMBER_EMAIL]

        for persona in non_demo_personas:
            member_id = str(self.member_map[persona["email"]])
            # All workout MERGE calls reference member_id in their kwargs
            workout_calls = [
                c for c in mock_session.run.call_args_list
                if c.kwargs.get("member_id") == member_id
                and "AssessmentWorkout" in (c.args[0] if c.args else "")
            ]
            assert len(workout_calls) >= 1, (
                f"No AssessmentWorkout seeded for {persona['email']}"
            )

    # ------------------------------------------------------------------
    # Demo member must be skipped
    # ------------------------------------------------------------------

    def test_demo_member_is_skipped(self) -> None:
        """Jordan Rivera (Demo) must NOT be touched by seed_rich_member_context_all."""
        mock_driver, mock_session = _make_driver_and_session()

        seed_rich_member_context_all(mock_driver, self.member_map, self.fake)

        demo_id = str(self.member_map[_DEMO_MEMBER_EMAIL])
        for c in mock_session.run.call_args_list:
            kwargs = c.kwargs or {}
            assert kwargs.get("member_id") != demo_id, (
                f"Demo member was written to by seed_rich_member_context_all (call: {c})"
            )

    # ------------------------------------------------------------------
    # Idempotency: calling twice produces same set of MERGE ids
    # ------------------------------------------------------------------

    def test_idempotent_same_ids_on_second_run(self) -> None:
        """Running seed_rich_member_context_all twice uses identical MERGE IDs (MERGE = idempotent)."""
        mock_driver_1, mock_session_1 = _make_driver_and_session()
        mock_driver_2, mock_session_2 = _make_driver_and_session()

        random.seed(42)
        Faker.seed(42)
        fake1 = Faker()
        seed_rich_member_context_all(mock_driver_1, self.member_map, fake1)

        random.seed(42)
        Faker.seed(42)
        fake2 = Faker()
        seed_rich_member_context_all(mock_driver_2, self.member_map, fake2)

        ids_run1 = {
            c.kwargs.get("id")
            for c in mock_session_1.run.call_args_list
            if c.kwargs and c.kwargs.get("id")
        }
        ids_run2 = {
            c.kwargs.get("id")
            for c in mock_session_2.run.call_args_list
            if c.kwargs and c.kwargs.get("id")
        }

        # Both runs should produce the exact same set of stable MERGE IDs
        assert ids_run1 == ids_run2, (
            f"Second run produced different IDs.\nOnly in run1: {ids_run1 - ids_run2}\nOnly in run2: {ids_run2 - ids_run1}"
        )

    # ------------------------------------------------------------------
    # Count: total session.run calls >= 4 calls per non-demo persona
    # (profile SET + blood_panel + dexa_scan + at least 1 chat + at least 1 workout)
    # ------------------------------------------------------------------

    def test_minimum_run_calls_per_persona(self) -> None:
        """At minimum 5 session.run calls per non-demo persona (profile + 2 labs + 1 chat + 1 workout)."""
        mock_driver, mock_session = _make_driver_and_session()

        seed_rich_member_context_all(mock_driver, self.member_map, self.fake)

        total_calls = mock_session.run.call_count
        non_demo_count = sum(1 for p in PERSONAS if p["email"] != _DEMO_MEMBER_EMAIL)
        # 1 profile SET + 2 LabResult + at least 1 ChatMessage + at least 1 Workout = 5 min
        assert total_calls >= non_demo_count * 5, (
            f"Expected at least {non_demo_count * 5} session.run calls, got {total_calls}"
        )
