"""Multi-match analytics endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_multi_stats(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    p = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 3, "name": "Jan"})).json()
    pid = p["player_id"]

    ids = []
    for opp in ("Legia", "Polonia"):
        mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
            "match": {"date": "2026-06-01", "opponent": opp, "place": "K", "age_category": "U17"},
            "roster": [{"player_id": pid, "number": 3, "name": "Jan", "team": "my"}],
        })
        mid = mr.json()["matchId"]
        ids.append(mid)
        await c.put(f"/v1/clubs/{club_id}/settings/active-match", json={"match_id": mid})
        await c.post(f"/v1/clubs/{club_id}/events", json={"events": [
            {"player_id": pid, "player_name": "Jan", "is_goal_from_play_positional": 1},
            {"player_id": pid, "player_name": "Jan", "is_steal_positional": 1},
        ]})

    r = await c.post(f"/v1/clubs/{club_id}/stats/multi", json={"match_ids": ids})
    assert r.status_code == 200
    d = r.json()
    assert d["match_count"] == 2
    assert d["totals"]["goals"] == 2
    assert d["totals"]["steals"] == 2
    assert d["totals"]["of_index"] == 2
    assert d["totals"]["def_index"] == 2
    assert len(d["trend"]) == 2
    assert len(d["by_quarter"]) == 4
