"""Match statistics aggregation service.

Port of the logic from app/api/stats/[matchId]/route.ts:57-166.
Pure function — no I/O, no database access.
"""

from dataclasses import dataclass

from src.domain.models import EVENT_FLAG_FIELDS, Event, Match, RosterEntry


@dataclass
class MatchStats:
    flags: list[str]
    players: list[dict]
    per_player_all: dict[str, dict[str, int]]
    per_player_by_q: dict[str, dict[str, dict[str, int]]]
    totals_all: dict[str, int]
    totals_by_q: dict[str, dict[str, int]]
    scores: dict


class StatsService:
    def compute_match_stats(
        self,
        events: list[Event],
        roster: list[RosterEntry],
        match: Match,
    ) -> MatchStats:
        """Aggregate all 44 flag fields per player, per quarter, and total.

        Mirrors the exact behavior of the TypeScript implementation:
        - flags are returned in snake_case (EVENT_FLAG_FIELDS is already snake_case)
        - per_player_all[player_id][flag] = sum of that flag across all quarters
        - per_player_by_q["1"][player_id][flag] = sum for quarter 1
        - totals_all[flag] = sum across all players and quarters
        - totals_by_q["1"][flag] = sum across all players for quarter 1
        """
        flags = list(EVENT_FLAG_FIELDS)

        def zero_flags() -> dict[str, int]:
            return {f: 0 for f in flags}

        totals_all = zero_flags()
        totals_by_q: dict[str, dict[str, int]] = {
            "1": zero_flags(),
            "2": zero_flags(),
            "3": zero_flags(),
            "4": zero_flags(),
        }
        per_player_all: dict[str, dict[str, int]] = {}
        per_player_by_q: dict[str, dict[str, dict[str, int]]] = {
            "1": {},
            "2": {},
            "3": {},
            "4": {},
        }

        for ev in events:
            q = str(ev.quarter)
            pid = ev.player_id

            for flag in flags:
                val = ev.get_flag_value(flag)

                totals_all[flag] += val
                if q in ("1", "2", "3", "4"):
                    totals_by_q[q][flag] += val

                if pid not in per_player_all:
                    per_player_all[pid] = zero_flags()
                per_player_all[pid][flag] += val

                if q in ("1", "2", "3", "4"):
                    if pid not in per_player_by_q[q]:
                        per_player_by_q[q][pid] = zero_flags()
                    per_player_by_q[q][pid][flag] += val

        players = [
            {
                "player_id": r.player_id,
                "number": r.number,
                "name": r.name,
                "team": r.team,
            }
            for r in roster
        ]

        return MatchStats(
            flags=flags,
            players=players,
            per_player_all=per_player_all,
            per_player_by_q=per_player_by_q,
            totals_all=totals_all,
            totals_by_q=totals_by_q,
            scores=match.per_quarter_scores(),
        )
