"""Tests for StatsService — verifies 1:1 parity with the TypeScript implementation."""

from src.domain.models import Event, Match, MatchStatus, RosterEntry
from src.domain.services import StatsService


def _make_event(
    player_id: str,
    player_name: str,
    quarter: int = 1,
    match_id: str = "m1",
    club_id: str = "c1",
    **flags: int,
) -> Event:
    return Event(
        id=f"e_{player_id}_{quarter}_{id(flags)}",
        club_id=club_id,
        match_id=match_id,
        player_id=player_id,
        player_name=player_name,
        quarter=quarter,
        **flags,
    )


def _make_roster(player_id: str, number: int, name: str) -> RosterEntry:
    return RosterEntry(
        id=f"r_{player_id}",
        club_id="c1",
        match_id="m1",
        player_id=player_id,
        number=number,
        name=name,
    )


def _make_match(**overrides) -> Match:
    defaults = dict(
        id="1", club_id="c1", match_id="m1", date="2026-01-15",
        opponent="Rival FC", place="Home", age_category="Seniorzy",
        status=MatchStatus.ENDED,
        q1_my=3, q1_opp=2, q2_my=6, q2_opp=4,
        q3_my=8, q3_opp=7, q4_my=11, q4_opp=9,
        final_my=11, final_opp=9,
    )
    defaults.update(overrides)
    return Match(**defaults)


class TestStatsService:
    svc = StatsService()

    def test_empty_events(self):
        """No events → all zeros, scores still computed."""
        match = _make_match()
        roster = [_make_roster("p1", 3, "Jan")]
        result = self.svc.compute_match_stats([], roster, match)

        assert len(result.flags) == 44
        assert all(v == 0 for v in result.totals_all.values())
        assert result.per_player_all == {}
        assert result.scores["1"] == {"my": 3, "opp": 2}
        assert result.players[0]["player_id"] == "p1"

    def test_single_event_aggregation(self):
        """One goal event → shows in totals and per-player."""
        match = _make_match()
        roster = [_make_roster("p1", 3, "Jan")]
        events = [
            _make_event("p1", "Jan", quarter=1, is_goal_from_play_positional=1),
        ]

        result = self.svc.compute_match_stats(events, roster, match)

        assert result.totals_all["is_goal_from_play_positional"] == 1
        assert result.totals_by_q["1"]["is_goal_from_play_positional"] == 1
        assert result.totals_by_q["2"]["is_goal_from_play_positional"] == 0
        assert result.per_player_all["p1"]["is_goal_from_play_positional"] == 1
        assert result.per_player_by_q["1"]["p1"]["is_goal_from_play_positional"] == 1

    def test_multi_player_multi_quarter(self):
        """Multiple players across quarters aggregate correctly."""
        match = _make_match()
        roster = [
            _make_roster("p1", 3, "Jan"),
            _make_roster("p2", 7, "Anna"),
        ]
        events = [
            _make_event("p1", "Jan", quarter=1, is_goal_from_play_positional=1),
            _make_event("p1", "Jan", quarter=2, is_goal_from_play_positional=1),
            _make_event("p2", "Anna", quarter=1, is_assist_positional=1),
            _make_event("p2", "Anna", quarter=3, is_steal_positional=1),
        ]

        result = self.svc.compute_match_stats(events, roster, match)

        # Totals
        assert result.totals_all["is_goal_from_play_positional"] == 2
        assert result.totals_all["is_assist_positional"] == 1
        assert result.totals_all["is_steal_positional"] == 1

        # Per player
        assert result.per_player_all["p1"]["is_goal_from_play_positional"] == 2
        assert result.per_player_all["p2"]["is_assist_positional"] == 1

        # Per quarter
        assert result.per_player_by_q["1"]["p1"]["is_goal_from_play_positional"] == 1
        assert result.per_player_by_q["2"]["p1"]["is_goal_from_play_positional"] == 1
        assert "p1" not in result.per_player_by_q["3"]
        assert result.per_player_by_q["3"]["p2"]["is_steal_positional"] == 1

    def test_scores_cumulative_to_per_quarter(self):
        """Scores are stored cumulatively, displayed as per-quarter differences."""
        match = _make_match(
            q1_my=2, q1_opp=1,
            q2_my=5, q2_opp=3,
            q3_my=7, q3_opp=6,
            q4_my=10, q4_opp=8,
            final_my=10, final_opp=8,
        )
        result = self.svc.compute_match_stats([], [], match)

        assert result.scores["1"] == {"my": 2, "opp": 1}
        assert result.scores["2"] == {"my": 3, "opp": 2}  # 5-2, 3-1
        assert result.scores["3"] == {"my": 2, "opp": 3}  # 7-5, 6-3
        assert result.scores["4"] == {"my": 3, "opp": 2}  # 10-7, 8-6
        assert result.scores["final"] == {"my": 10, "opp": 8}

    def test_final_score_fallback_to_q4(self):
        """If final_my/final_opp are 0, use q4 scores."""
        match = _make_match(
            q4_my=10, q4_opp=8, final_my=0, final_opp=0,
        )
        result = self.svc.compute_match_stats([], [], match)
        assert result.scores["final"] == {"my": 10, "opp": 8}

    def test_all_44_flags_present(self):
        """Verify all 44 flags appear in the result."""
        match = _make_match()
        result = self.svc.compute_match_stats([], [], match)
        assert len(result.flags) == 44
        assert len(result.totals_all) == 44
