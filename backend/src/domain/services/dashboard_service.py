"""Dashboard overview — aggregates club-wide KPIs, recent matches and rankings.

Reuses TeamStatsService for W/L/D record and player rankings.
"""

from dataclasses import dataclass

from src.domain.models import Event, Match, MatchStatus
from src.domain.services.team_stats_service import PlayerRanking, TeamStatsService


@dataclass
class DashboardMatch:
    match_id: str
    date: str
    opponent: str
    age_category: str
    status: str
    my_score: int
    opp_score: int
    result: str  # "W" | "L" | "D" | "" (not finished)


@dataclass
class DashboardOverview:
    total_matches: int
    wins: int
    losses: int
    draws: int
    goals_for: int
    goals_against: int
    goal_difference: int
    top_scorers: list[PlayerRanking]
    top_assistants: list[PlayerRanking]
    recent_matches: list[DashboardMatch]
    active_match: DashboardMatch | None


class DashboardService:
    def __init__(self) -> None:
        self._team_stats = TeamStatsService()

    def _to_match(self, m: Match) -> DashboardMatch:
        my = m.final_my or m.q4_my
        opp = m.final_opp or m.q4_opp
        result = ""
        if m.status == MatchStatus.ENDED:
            result = "W" if my > opp else "L" if my < opp else "D"
        return DashboardMatch(
            match_id=m.match_id, date=m.date, opponent=m.opponent,
            age_category=m.age_category, status=m.status.value,
            my_score=my, opp_score=opp, result=result,
        )

    def compute_overview(
        self,
        matches: list[Match],
        events: list[Event],
        active_match_id: str = "",
        recent_n: int = 5,
        age_category: str | None = None,
    ) -> DashboardOverview:
        filtered = matches
        if age_category:
            filtered = [m for m in matches if m.age_category == age_category]

        summary = self._team_stats.compute_season_summary("", "", filtered, events)

        recent = sorted(
            filtered,
            key=lambda m: (m.date or "", m.created_at),
            reverse=True,
        )[:recent_n]

        active = next((m for m in matches if m.match_id == active_match_id), None)

        return DashboardOverview(
            total_matches=summary.total_matches,
            wins=summary.wins,
            losses=summary.losses,
            draws=summary.draws,
            goals_for=summary.goals_for,
            goals_against=summary.goals_against,
            goal_difference=summary.goal_difference,
            top_scorers=summary.top_scorers[:5],
            top_assistants=summary.top_assistants[:5],
            recent_matches=[self._to_match(m) for m in recent],
            active_match=self._to_match(active) if active else None,
        )
