"""Play-time tracking — turns in/out-of-water substitutions into time on water."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.models import Substitution


@dataclass
class PlaytimeEntry:
    player_id: str
    seconds: int
    on_water: bool
    stint_start: datetime | None  # start of the currently-open stint (if on_water)


class PlaytimeService:
    def compute(
        self, subs: list[Substitution], now: datetime | None = None
    ) -> dict[str, PlaytimeEntry]:
        """Sum in→out intervals per player; open stints are closed at `now`."""
        now = now or datetime.utcnow()

        by_player: dict[str, list[Substitution]] = {}
        for s in sorted(subs, key=lambda x: x.timestamp):
            by_player.setdefault(s.player_id, []).append(s)

        result: dict[str, PlaytimeEntry] = {}
        for pid, plist in by_player.items():
            total = 0.0
            open_start: datetime | None = None
            for s in plist:
                if s.direction == "in":
                    if open_start is None:
                        open_start = s.timestamp
                elif s.direction == "out":
                    if open_start is not None:
                        total += (s.timestamp - open_start).total_seconds()
                        open_start = None
            on_water = open_start is not None
            if on_water:
                total += (now - open_start).total_seconds()
            result[pid] = PlaytimeEntry(
                player_id=pid,
                seconds=int(max(0, total)),
                on_water=on_water,
                stint_start=open_start,
            )
        return result

    def on_water_players(self, subs: list[Substitution]) -> list[str]:
        return [pid for pid, e in self.compute(subs).items() if e.on_water]
