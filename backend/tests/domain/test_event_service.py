"""Tests for EventService — verifies getEventAction() label resolution."""

from src.domain.models import Event
from src.domain.services import EventService


def _make_event(**flags: int) -> Event:
    return Event(
        id="e1", club_id="c1", match_id="m1",
        player_id="p1", player_name="Jan", **flags,
    )


class TestEventService:
    svc = EventService()

    def test_goal_from_play_positional(self):
        ev = _make_event(is_goal_from_play_positional=1)
        assert self.svc.get_event_action(ev) == "G z akcji (poz.)"

    def test_goal_from_counter(self):
        ev = _make_event(is_goal_from_play_counter=1)
        assert self.svc.get_event_action(ev) == "G z kontrataku"

    def test_goal_5m_penalty(self):
        ev = _make_event(is_goal_5m_penalty=1)
        assert self.svc.get_event_action(ev) == "G z karnego"

    def test_steal_man_up(self):
        ev = _make_event(is_steal_man_up=1)
        assert self.svc.get_event_action(ev) == "Przejęcie (przew.)"

    def test_block_positional(self):
        ev = _make_event(is_block_hand_positional=1)
        assert self.svc.get_event_action(ev) == "Blok (poz.)"

    def test_no_flags_set(self):
        ev = _make_event()
        assert self.svc.get_event_action(ev) == "Nieznana akcja"

    def test_first_flag_wins(self):
        """When multiple flags are set, the first one in ORDER wins."""
        ev = _make_event(
            is_steal_positional=1,  # Later in order
            is_goal_from_play_positional=1,  # Earlier in order
        )
        # Goal should win because it comes first in EVENT_FLAG_FIELDS
        assert self.svc.get_event_action(ev) == "G z akcji (poz.)"

    def test_format_recent_event(self):
        ev = _make_event(is_assist_man_up=1)
        formatted = self.svc.format_recent_event(ev)
        assert formatted["action"] == "Asysta (przew.)"
        assert formatted["player_name"] == "Jan"
        assert formatted["quarter"] == 1
