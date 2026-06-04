"""Player profile statistics — cross-match aggregation, trends, effectiveness.

New service from roadmapa Faza 1: profil zawodnika.
"""

from dataclasses import dataclass

from src.domain.models import EVENT_FLAG_FIELDS, Event, Match


# Goal-related flags for shot effectiveness calculation
GOAL_FLAGS = {
    "is_goal_from_play_positional",
    "is_goal_from_play_counter",
    "is_goal_from_center_positional",
    "is_goal_from_center_man_up",
    "is_goal_5m_man_up",
    "is_goal_5m_penalty",
}

# Shot attempt flags (goals + saved + missed)
SHOT_FLAGS = GOAL_FLAGS | {
    "is_shot_saved_gk_positional",
    "is_shot_saved_gk_man_up",
    "is_shot_miss_turnover_positional",
    "is_shot_miss_turnover_man_up",
    "is_shot_miss_reset30_positional",
    "is_shot_miss_reset30_man_up",
}

ASSIST_FLAGS = {"is_assist_positional", "is_assist_man_up"}

TURNOVER_FLAGS = {
    "is_bad_pass_turnover_positional",
    "is_bad_pass_turnover_man_up",
    "is_turnover_1v1_positional",
    "is_turnover_1v1_man_up",
}

EXCLUSION_FLAGS = {
    "is_excl_committed_field_positional",
    "is_excl_committed_field_man_up",
    "is_excl_committed_center_positional",
    "is_excl_committed_center_man_up",
}

STEAL_FLAGS = {"is_steal_positional", "is_steal_man_up"}
BLOCK_FLAGS = {"is_block_hand_positional", "is_block_hand_man_up"}


@dataclass
class MatchPerformance:
    """Single-match performance summary for trend tracking."""
    match_id: str
    match_date: str
    opponent: str
    goals: int
    shots: int
    shot_effectiveness: float  # goals / shots, 0.0 if no shots
    assists: int
    turnovers: int
    exclusions: int
    steals: int
    blocks: int


@dataclass
class PlayerProfile:
    """Aggregated player statistics across matches."""
    player_id: str
    player_name: str
    total_matches: int
    # Totals
    total_goals: int
    total_shots: int
    overall_effectiveness: float
    total_assists: int
    total_turnovers: int
    total_exclusions: int
    total_steals: int
    total_blocks: int
    # All 44 flags aggregated
    flag_totals: dict[str, int]
    # Per-match trend (ordered by date)
    match_trend: list[MatchPerformance]


class PlayerProfileService:
    def compute_player_profile(
        self,
        player_id: str,
        player_name: str,
        events: list[Event],
        matches: list[Match],
    ) -> PlayerProfile:
        """Aggregate player stats across multiple matches for profile view.

        Args:
            player_id: The player's ID.
            player_name: Display name.
            events: All events for this player (pre-filtered by player_id).
            matches: All matches the player participated in (for date/opponent).
        """
        match_map = {m.match_id: m for m in matches}

        # Group events by match
        events_by_match: dict[str, list[Event]] = {}
        for ev in events:
            events_by_match.setdefault(ev.match_id, []).append(ev)

        # Compute per-match performance
        match_trend: list[MatchPerformance] = []
        flag_totals = {f: 0 for f in EVENT_FLAG_FIELDS}

        for mid, match_events in events_by_match.items():
            match = match_map.get(mid)
            goals = 0
            shots = 0
            assists = 0
            turnovers = 0
            exclusions = 0
            steals = 0
            blocks = 0

            for ev in match_events:
                for flag in EVENT_FLAG_FIELDS:
                    val = ev.get_flag_value(flag)
                    flag_totals[flag] += val

                    if flag in GOAL_FLAGS:
                        goals += val
                    if flag in SHOT_FLAGS:
                        shots += val
                    if flag in ASSIST_FLAGS:
                        assists += val
                    if flag in TURNOVER_FLAGS:
                        turnovers += val
                    if flag in EXCLUSION_FLAGS:
                        exclusions += val
                    if flag in STEAL_FLAGS:
                        steals += val
                    if flag in BLOCK_FLAGS:
                        blocks += val

            effectiveness = goals / shots if shots > 0 else 0.0

            match_trend.append(
                MatchPerformance(
                    match_id=mid,
                    match_date=match.date if match else "",
                    opponent=match.opponent if match else "",
                    goals=goals,
                    shots=shots,
                    shot_effectiveness=round(effectiveness, 3),
                    assists=assists,
                    turnovers=turnovers,
                    exclusions=exclusions,
                    steals=steals,
                    blocks=blocks,
                )
            )

        # Sort by match date
        match_trend.sort(key=lambda mp: mp.match_date)

        # Compute totals
        total_goals = sum(mp.goals for mp in match_trend)
        total_shots = sum(mp.shots for mp in match_trend)
        overall_eff = total_goals / total_shots if total_shots > 0 else 0.0

        return PlayerProfile(
            player_id=player_id,
            player_name=player_name,
            total_matches=len(match_trend),
            total_goals=total_goals,
            total_shots=total_shots,
            overall_effectiveness=round(overall_eff, 3),
            total_assists=sum(mp.assists for mp in match_trend),
            total_turnovers=sum(mp.turnovers for mp in match_trend),
            total_exclusions=sum(mp.exclusions for mp in match_trend),
            total_steals=sum(mp.steals for mp in match_trend),
            total_blocks=sum(mp.blocks for mp in match_trend),
            flag_totals=flag_totals,
            match_trend=match_trend,
        )
