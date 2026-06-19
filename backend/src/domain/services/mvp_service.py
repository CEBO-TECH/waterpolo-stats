"""MVP suggestion — weighted contribution score per player for a match."""

from dataclasses import dataclass

from src.domain.models import Event, RosterEntry
from src.domain.services.analytics_service import DEFENSE_NEG, DRAWN_FLAGS, OFFENSE_NEG
from src.domain.services.player_profile_service import (
    ASSIST_FLAGS,
    BLOCK_FLAGS,
    GOAL_FLAGS,
    STEAL_FLAGS,
)

GK_DEF_FLAGS = {"is_shot_saved_gk_def_positional", "is_shot_saved_gk_def_man_up"}

# (component label, flag set, weight)
MVP_WEIGHTS: list[tuple[str, set[str], float]] = [
    ("goals", GOAL_FLAGS, 3.0),
    ("assists", ASSIST_FLAGS, 2.0),
    ("drawn", DRAWN_FLAGS, 1.5),
    ("steals", STEAL_FLAGS, 1.5),
    ("blocks", BLOCK_FLAGS, 1.0),
    ("gk_saves", GK_DEF_FLAGS, 1.0),
    ("turnovers", OFFENSE_NEG, -1.0),
    ("fouls", DEFENSE_NEG, -1.0),
]


@dataclass
class MvpEntry:
    player_id: str
    player_name: str
    score: float
    goals: int
    assists: int
    steals: int
    blocks: int
    turnovers: int
    fouls: int


class MvpService:
    def compute(self, events: list[Event], roster: list[RosterEntry]) -> list[MvpEntry]:
        names = {r.player_id: r.name for r in roster}

        by_player: dict[str, list[Event]] = {}
        for ev in events:
            by_player.setdefault(ev.player_id, []).append(ev)

        entries: list[MvpEntry] = []
        for pid, evs in by_player.items():
            def cnt(flags: set[str]) -> int:
                return sum(e.get_flag_value(f) for e in evs for f in flags)

            comp = {label: cnt(flags) for label, flags, _ in MVP_WEIGHTS}
            score = sum(comp[label] * w for label, _, w in MVP_WEIGHTS)
            name = names.get(pid) or (evs[0].player_name if evs else "")
            entries.append(MvpEntry(
                player_id=pid, player_name=name, score=round(score, 1),
                goals=comp["goals"], assists=comp["assists"], steals=comp["steals"],
                blocks=comp["blocks"], turnovers=comp["turnovers"], fouls=comp["fouls"],
            ))

        entries.sort(key=lambda e: e.score, reverse=True)
        return entries
