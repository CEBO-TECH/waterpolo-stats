from datetime import datetime, timedelta

from src.domain.models import Substitution
from src.domain.services import PlaytimeService


def _sub(pid: str, direction: str, t: datetime) -> Substitution:
    return Substitution(id="x", club_id="c", match_id="m", player_id=pid, direction=direction, timestamp=t)


T0 = datetime(2026, 1, 1, 18, 0, 0)


def test_closed_stint():
    subs = [_sub("p1", "in", T0), _sub("p1", "out", T0 + timedelta(seconds=120))]
    pt = PlaytimeService().compute(subs, now=T0 + timedelta(seconds=300))
    assert pt["p1"].seconds == 120
    assert pt["p1"].on_water is False


def test_open_stint_counts_to_now():
    pt = PlaytimeService().compute([_sub("p1", "in", T0)], now=T0 + timedelta(seconds=90))
    assert pt["p1"].seconds == 90
    assert pt["p1"].on_water is True
    assert pt["p1"].stint_start == T0


def test_multiple_stints_sum():
    subs = [
        _sub("p1", "in", T0),
        _sub("p1", "out", T0 + timedelta(seconds=60)),
        _sub("p1", "in", T0 + timedelta(seconds=120)),
        _sub("p1", "out", T0 + timedelta(seconds=180)),
    ]
    pt = PlaytimeService().compute(subs, now=T0 + timedelta(seconds=300))
    assert pt["p1"].seconds == 120
    assert pt["p1"].on_water is False


def test_on_water_players():
    subs = [
        _sub("p1", "in", T0),
        _sub("p2", "in", T0),
        _sub("p2", "out", T0 + timedelta(seconds=30)),
    ]
    assert PlaytimeService().on_water_players(subs) == ["p1"]
