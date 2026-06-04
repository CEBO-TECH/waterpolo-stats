"""Tests for PlayerProfileService — cross-match aggregation and trends."""

from src.domain.models import Event, Match, MatchStatus
from src.domain.services import PlayerProfileService


def _make_match(match_id: str, date: str, opponent: str) -> Match:
    return Match(
        id=match_id, club_id="c1", match_id=match_id, date=date,
        opponent=opponent, place="Home", age_category="Seniorzy",
        status=MatchStatus.ENDED,
    )


def _make_event(match_id: str, **flags: int) -> Event:
    return Event(
        id=f"e_{match_id}_{id(flags)}", club_id="c1", match_id=match_id,
        player_id="p1", player_name="Jan", **flags,
    )


class TestPlayerProfileService:
    svc = PlayerProfileService()

    def test_empty_events(self):
        profile = self.svc.compute_player_profile("p1", "Jan", [], [])
        assert profile.total_matches == 0
        assert profile.total_goals == 0
        assert profile.overall_effectiveness == 0.0

    def test_single_match_profile(self):
        matches = [_make_match("m1", "2026-01-15", "Rival")]
        events = [
            _make_event("m1", is_goal_from_play_positional=1),
            _make_event("m1", is_goal_from_center_positional=1),
            _make_event("m1", is_shot_saved_gk_positional=1),  # Shot but not goal
            _make_event("m1", is_assist_positional=1),
        ]

        profile = self.svc.compute_player_profile("p1", "Jan", events, matches)

        assert profile.total_matches == 1
        assert profile.total_goals == 2
        assert profile.total_shots == 3  # 2 goals + 1 saved
        assert profile.overall_effectiveness == round(2 / 3, 3)
        assert profile.total_assists == 1
        assert len(profile.match_trend) == 1
        assert profile.match_trend[0].opponent == "Rival"

    def test_multi_match_trend(self):
        matches = [
            _make_match("m1", "2026-01-15", "TeamA"),
            _make_match("m2", "2026-01-22", "TeamB"),
        ]
        events = [
            _make_event("m1", is_goal_from_play_positional=1),
            _make_event("m2", is_goal_from_play_positional=1),
            _make_event("m2", is_goal_from_play_positional=1),
            _make_event("m2", is_shot_miss_turnover_positional=1),
        ]

        profile = self.svc.compute_player_profile("p1", "Jan", events, matches)

        assert profile.total_matches == 2
        assert profile.total_goals == 3
        # Trend sorted by date
        assert profile.match_trend[0].match_id == "m1"
        assert profile.match_trend[0].goals == 1
        assert profile.match_trend[1].match_id == "m2"
        assert profile.match_trend[1].goals == 2
        assert profile.match_trend[1].shots == 3  # 2 goals + 1 miss

    def test_turnovers_and_exclusions(self):
        matches = [_make_match("m1", "2026-01-15", "X")]
        events = [
            _make_event("m1", is_bad_pass_turnover_positional=1),
            _make_event("m1", is_turnover_1v1_man_up=1),
            _make_event("m1", is_excl_committed_field_positional=1),
        ]

        profile = self.svc.compute_player_profile("p1", "Jan", events, matches)
        assert profile.total_turnovers == 2
        assert profile.total_exclusions == 1
