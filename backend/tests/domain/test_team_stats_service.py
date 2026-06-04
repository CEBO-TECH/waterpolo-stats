"""Tests for TeamStatsService — season summaries and rankings."""

from src.domain.models import Event, Match, MatchStatus
from src.domain.services import TeamStatsService


def _make_match(
    match_id: str, opponent: str, my: int, opp: int,
    age_category: str = "Seniorzy",
) -> Match:
    return Match(
        id=match_id, club_id="c1", match_id=match_id, date="2026-01-15",
        opponent=opponent, place="Home", age_category=age_category,
        status=MatchStatus.ENDED, season_id="s1",
        q4_my=my, q4_opp=opp, final_my=my, final_opp=opp,
    )


def _make_event(match_id: str, player_id: str, name: str, **flags: int) -> Event:
    return Event(
        id=f"e_{match_id}_{player_id}_{id(flags)}", club_id="c1",
        match_id=match_id, player_id=player_id, player_name=name, **flags,
    )


class TestTeamStatsService:
    svc = TeamStatsService()

    def test_season_wld_record(self):
        matches = [
            _make_match("m1", "TeamA", my=10, opp=5),   # Win
            _make_match("m2", "TeamB", my=5, opp=10),   # Loss
            _make_match("m3", "TeamC", my=7, opp=7),    # Draw
        ]
        result = self.svc.compute_season_summary("s1", "2026/2027", matches, [])

        assert result.wins == 1
        assert result.losses == 1
        assert result.draws == 1
        assert result.goals_for == 22
        assert result.goals_against == 22
        assert result.goal_difference == 0

    def test_top_scorers_ranking(self):
        matches = [_make_match("m1", "X", 5, 3)]
        events = [
            _make_event("m1", "p1", "Jan", is_goal_from_play_positional=1),
            _make_event("m1", "p1", "Jan", is_goal_from_center_positional=1),
            _make_event("m1", "p2", "Anna", is_goal_5m_penalty=1),
        ]
        result = self.svc.compute_season_summary("s1", "2026/2027", matches, events)

        assert len(result.top_scorers) == 2
        assert result.top_scorers[0].player_id == "p1"
        assert result.top_scorers[0].value == 2
        assert result.top_scorers[1].player_id == "p2"
        assert result.top_scorers[1].value == 1

    def test_filter_by_age_category(self):
        matches = [
            _make_match("m1", "X", 10, 5, age_category="Seniorzy"),
            _make_match("m2", "Y", 3, 8, age_category="U17"),
        ]
        result = self.svc.compute_season_summary(
            "s1", "2026/2027", matches, [], age_category="U17"
        )
        assert result.total_matches == 1
        assert result.losses == 1

    def test_filter_by_opponent(self):
        matches = [
            _make_match("m1", "TeamA", 10, 5),
            _make_match("m2", "TeamB", 3, 8),
            _make_match("m3", "TeamA", 7, 6),
        ]
        result = self.svc.compute_season_summary(
            "s1", "2026/2027", matches, [], opponent="TeamA"
        )
        assert result.total_matches == 2
        assert result.wins == 2
