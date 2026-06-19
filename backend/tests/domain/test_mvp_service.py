from src.domain.models import Event
from src.domain.services import MvpService


def _ev(pid: str, name: str, **flags) -> Event:
    return Event(id="x", club_id="c", match_id="m", player_id=pid, player_name=name, **flags)


def test_mvp_ranking():
    events = [
        _ev("p1", "Jan", is_goal_from_play_positional=1),
        _ev("p1", "Jan", is_goal_from_play_positional=1),
        _ev("p1", "Jan", is_goal_from_play_positional=1),
        _ev("p1", "Jan", is_assist_positional=1),
        _ev("p2", "Piotr", is_goal_from_play_counter=1),
        _ev("p2", "Piotr", is_steal_positional=1),
        _ev("p2", "Piotr", is_steal_positional=1),
        _ev("p2", "Piotr", is_turnover_1v1_positional=1),
    ]
    ranking = MvpService().compute(events, roster=[])

    # p1: 3*3 + 1*2 = 11 ; p2: 1*3 + 2*1.5 - 1*1 = 5
    assert ranking[0].player_id == "p1"
    assert ranking[0].score == 11.0
    assert ranking[0].goals == 3
    assert ranking[1].player_id == "p2"
    assert ranking[1].score == 5.0
    assert ranking[1].steals == 2
    assert ranking[1].turnovers == 1
