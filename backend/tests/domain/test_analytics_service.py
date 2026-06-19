from src.domain.models import Event, Match
from src.domain.services import AnalyticsService


def _ev(match_id: str, quarter: int, **flags) -> Event:
    return Event(
        id="x", club_id="c", match_id=match_id, player_id="p", player_name="P",
        quarter=quarter, **flags,
    )


def _match(mid: str, date: str) -> Match:
    return Match(
        id=mid, club_id="c", match_id=mid, date=date, opponent="O", place="",
        age_category="U17", final_my=5, final_opp=3,
    )


def test_compute_multi():
    m1, m2 = _match("m1", "2026-05-01"), _match("m2", "2026-05-08")
    events = [
        _ev("m1", 1, is_goal_from_play_positional=1),
        _ev("m1", 1, is_assist_positional=1),
        _ev("m1", 2, is_turnover_1v1_positional=1),
        _ev("m1", 2, is_steal_positional=1),
        _ev("m2", 1, is_goal_from_play_counter=1),
    ]
    r = AnalyticsService().compute_multi([m1, m2], events)

    assert r.match_count == 2
    assert r.totals["goals"] == 2
    assert r.totals["assists"] == 1
    assert r.totals["turnovers"] == 1
    assert r.totals["steals"] == 1
    assert r.totals["of_index"] == 2   # (2 goals + 1 assist) - 1 turnover
    assert r.totals["def_index"] == 1  # 1 steal

    # trend sorted by date
    assert [t.match_id for t in r.trend] == ["m1", "m2"]
    assert r.trend[0].goals == 1 and r.trend[1].goals == 1

    q1 = next(q for q in r.by_quarter if q.quarter == 1)
    q2 = next(q for q in r.by_quarter if q.quarter == 2)
    assert q1.goals == 2
    assert q2.turnovers == 1
    assert len(r.by_quarter) == 4
