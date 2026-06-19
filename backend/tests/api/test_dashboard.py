"""Dashboard overview endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    p = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 7, "name": "Anna"})).json()
    pid = p["player_id"]

    mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "Kraków", "age_category": "U17"},
        "roster": [{"player_id": pid, "number": 7, "name": "Anna", "team": "my"}],
    })
    match_id = mr.json()["matchId"]

    await c.put(f"/v1/clubs/{club_id}/settings/active-match", json={"match_id": match_id})

    await c.post(f"/v1/clubs/{club_id}/events", json={"events": [
        {"player_id": pid, "player_name": "Anna", "is_goal_from_play_positional": 1},
        {"player_id": pid, "player_name": "Anna", "is_goal_from_play_positional": 1},
        {"player_id": pid, "player_name": "Anna", "is_assist_positional": 1},
    ]})

    await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/scores", json={"quarter": "final", "my_score": 10, "opp_score": 5})
    await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/end")

    r = await c.get(f"/v1/clubs/{club_id}/dashboard")
    assert r.status_code == 200
    d = r.json()
    assert d["total_matches"] == 1
    assert d["wins"] == 1
    assert d["losses"] == 0
    assert d["goals_for"] == 10
    assert d["goals_against"] == 5
    assert d["goal_difference"] == 5
    assert d["top_scorers"][0]["player_name"] == "Anna"
    assert d["top_scorers"][0]["value"] == 2
    assert d["top_assistants"][0]["value"] == 1
    assert len(d["recent_matches"]) == 1
    assert d["recent_matches"][0]["result"] == "W"
    assert d["active_match"]["match_id"] == match_id


@pytest.mark.asyncio
async def test_dashboard_empty(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.get(f"/v1/clubs/{club_id}/dashboard")
    assert r.status_code == 200
    d = r.json()
    assert d["total_matches"] == 0
    assert d["recent_matches"] == []
    assert d["active_match"] is None
