"""Advanced analytics — multi-match aggregation, per-quarter distribution,
offense/defense index. Reuses flag groupings from player_profile_service.
"""

from dataclasses import dataclass

from src.domain.models import Event, Match
from src.domain.services.player_profile_service import (
    ASSIST_FLAGS,
    BLOCK_FLAGS,
    EXCLUSION_FLAGS,
    GOAL_FLAGS,
    STEAL_FLAGS,
    TURNOVER_FLAGS,
)

# Offense/defense index flag groups
DRAWN_FLAGS = {
    "is_excl_drawn_field_positional",
    "is_excl_drawn_center_positional",
    "is_penalty_drawn_field_positional",
    "is_penalty_drawn_center_positional",
}
OFFENSE_POS = GOAL_FLAGS | ASSIST_FLAGS | DRAWN_FLAGS
OFFENSE_NEG = TURNOVER_FLAGS | {
    "is_shot_clock_violation_positional",
    "is_shot_clock_violation_man_up",
    "is_shot_miss_turnover_positional",
    "is_shot_miss_turnover_man_up",
}
DEFENSE_POS = STEAL_FLAGS | BLOCK_FLAGS | {
    "is_shot_saved_gk_def_positional",
    "is_shot_saved_gk_def_man_up",
}
DEFENSE_NEG = EXCLUSION_FLAGS | {
    "is_penalty_committed_field_positional",
    "is_penalty_committed_field_man_up",
    "is_penalty_committed_center_positional",
    "is_penalty_committed_center_man_up",
    "is_no_return_positional",
    "is_no_return_man_up",
    "is_no_block_positional",
    "is_no_block_man_up",
}


def _sum(events: list[Event], flags: set[str]) -> int:
    return sum(ev.get_flag_value(f) for ev in events for f in flags)


@dataclass
class MatchTrendPoint:
    match_id: str
    date: str
    opponent: str
    goals: int
    turnovers: int
    steals: int
    of_index: int
    def_index: int
    my_score: int
    opp_score: int


@dataclass
class QuarterPoint:
    quarter: int
    goals: int
    turnovers: int
    of_index: int
    def_index: int
    events: int


@dataclass
class MultiMatchAnalytics:
    match_count: int
    totals: dict[str, int]
    trend: list[MatchTrendPoint]
    by_quarter: list[QuarterPoint]


class AnalyticsService:
    def _metrics(self, events: list[Event]) -> dict[str, int]:
        return {
            "goals": _sum(events, GOAL_FLAGS),
            "assists": _sum(events, ASSIST_FLAGS),
            "turnovers": _sum(events, OFFENSE_NEG),
            "steals": _sum(events, STEAL_FLAGS),
            "blocks": _sum(events, BLOCK_FLAGS),
            "exclusions": _sum(events, EXCLUSION_FLAGS),
            "of_index": _sum(events, OFFENSE_POS) - _sum(events, OFFENSE_NEG),
            "def_index": _sum(events, DEFENSE_POS) - _sum(events, DEFENSE_NEG),
        }

    def compute_multi(
        self, matches: list[Match], events: list[Event]
    ) -> MultiMatchAnalytics:
        by_match: dict[str, list[Event]] = {}
        for ev in events:
            by_match.setdefault(ev.match_id, []).append(ev)

        trend: list[MatchTrendPoint] = []
        for m in sorted(matches, key=lambda x: (x.date or "", x.created_at)):
            me = by_match.get(m.match_id, [])
            mtr = self._metrics(me)
            trend.append(MatchTrendPoint(
                match_id=m.match_id, date=m.date, opponent=m.opponent,
                goals=mtr["goals"], turnovers=mtr["turnovers"], steals=mtr["steals"],
                of_index=mtr["of_index"], def_index=mtr["def_index"],
                my_score=(m.final_my or m.q4_my), opp_score=(m.final_opp or m.q4_opp),
            ))

        totals = self._metrics(events)

        by_quarter: list[QuarterPoint] = []
        for q in (1, 2, 3, 4):
            qe = [ev for ev in events if ev.quarter == q]
            qm = self._metrics(qe)
            by_quarter.append(QuarterPoint(
                quarter=q, goals=qm["goals"], turnovers=qm["turnovers"],
                of_index=qm["of_index"], def_index=qm["def_index"], events=len(qe),
            ))

        return MultiMatchAnalytics(
            match_count=len(matches), totals=totals, trend=trend, by_quarter=by_quarter,
        )
