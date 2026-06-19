"""MVP suggestion + confirmation endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mvp_suggest_and_confirm(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    p1 = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 3, "name": "Jan"})).json()
    p2 = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 7, "name": "Piotr"})).json()

    mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "K", "age_category": "U17"},
        "roster": [
            {"player_id": p1["player_id"], "number": 3, "name": "Jan", "team": "my"},
            {"player_id": p2["player_id"], "number": 7, "name": "Piotr", "team": "my"},
        ],
    })
    match_id = mr.json()["matchId"]
    await c.put(f"/v1/clubs/{club_id}/settings/active-match", json={"match_id": match_id})

    await c.post(f"/v1/clubs/{club_id}/events", json={"events": [
        {"player_id": p1["player_id"], "player_name": "Jan", "is_goal_from_play_positional": 1},
        {"player_id": p1["player_id"], "player_name": "Jan", "is_goal_from_play_positional": 1},
        {"player_id": p2["player_id"], "player_name": "Piotr", "is_steal_positional": 1},
    ]})

    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/mvp")
    assert r.status_code == 200
    d = r.json()
    assert d["suggested"]["player_id"] == p1["player_id"]
    assert d["suggested"]["goals"] == 2
    assert len(d["ranking"]) == 2
    assert d["confirmed_player_id"] is None

    # Coach overrides MVP to p2
    r = await c.put(f"/v1/clubs/{club_id}/matches/{match_id}/mvp", json={"player_id": p2["player_id"]})
    assert r.status_code == 200

    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/mvp")
    assert r.json()["confirmed_player_id"] == p2["player_id"]
