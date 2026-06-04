"""Team/season statistics — W/L record, rankings, summaries.

New service from roadmapa Faza 1: statystyki drużyny i sezonu.
"""

from dataclasses import dataclass, field

from src.domain.models import Event, Match, MatchStatus
from src.domain.services.player_profile_service import GOAL_FLAGS


@dataclass
class PlayerRanking:
    player_id: str
    player_name: str
    value: int  # The metric being ranked (goals, assists, etc.)


@dataclass
class SeasonSummary:
    season_id: str
    season_name: str
    total_matches: int
    wins: int
    losses: int
    draws: int
    goals_for: int
    goals_against: int
    goal_difference: int
    # Rankings
    top_scorers: list[PlayerRanking]
    top_assistants: list[PlayerRanking]
    top_stealers: list[PlayerRanking]


class TeamStatsService:
    def compute_season_summary(
        self,
        season_id: str,
        season_name: str,
        matches: list[Match],
        events: list[Event],
        age_category: str | None = None,
        opponent: str | None = None,
    ) -> SeasonSummary:
        """Compute season summary with W/L/D record and player rankings.

        Args:
            matches: All matches for the season (pre-filtered by season_id).
            events: All events for the season.
            age_category: Optional filter by age category.
            opponent: Optional filter by opponent name.
        """
        # Apply filters
        filtered_matches = matches
        if age_category:
            filtered_matches = [
                m for m in filtered_matches if m.age_category == age_category
            ]
        if opponent:
            filtered_matches = [
                m for m in filtered_matches
                if m.opponent.lower() == opponent.lower()
            ]

        # Only count ended matches for W/L/D
        ended_matches = [
            m for m in filtered_matches if m.status == MatchStatus.ENDED
        ]
        match_ids = {m.match_id for m in filtered_matches}

        wins = 0
        losses = 0
        draws = 0
        goals_for = 0
        goals_against = 0

        for m in ended_matches:
            my = m.final_my or m.q4_my
            opp = m.final_opp or m.q4_opp
            goals_for += my
            goals_against += opp
            if my > opp:
                wins += 1
            elif my < opp:
                losses += 1
            else:
                draws += 1

        # Filter events by match IDs
        season_events = [e for e in events if e.match_id in match_ids]

        # Compute player rankings
        player_goals: dict[str, int] = {}
        player_assists: dict[str, int] = {}
        player_steals: dict[str, int] = {}
        player_names: dict[str, str] = {}

        for ev in season_events:
            pid = ev.player_id
            player_names[pid] = ev.player_name

            for flag in GOAL_FLAGS:
                player_goals[pid] = player_goals.get(pid, 0) + ev.get_flag_value(flag)

            for flag in ("is_assist_positional", "is_assist_man_up"):
                player_assists[pid] = (
                    player_assists.get(pid, 0) + ev.get_flag_value(flag)
                )

            for flag in ("is_steal_positional", "is_steal_man_up"):
                player_steals[pid] = (
                    player_steals.get(pid, 0) + ev.get_flag_value(flag)
                )

        def make_ranking(
            data: dict[str, int], limit: int = 10
        ) -> list[PlayerRanking]:
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            return [
                PlayerRanking(
                    player_id=pid,
                    player_name=player_names.get(pid, ""),
                    value=val,
                )
                for pid, val in sorted_items[:limit]
                if val > 0
            ]

        return SeasonSummary(
            season_id=season_id,
            season_name=season_name,
            total_matches=len(filtered_matches),
            wins=wins,
            losses=losses,
            draws=draws,
            goals_for=goals_for,
            goals_against=goals_against,
            goal_difference=goals_for - goals_against,
            top_scorers=make_ranking(player_goals),
            top_assistants=make_ranking(player_assists),
            top_stealers=make_ranking(player_steals),
        )
