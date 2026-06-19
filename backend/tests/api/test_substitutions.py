"""Substitution / play-time endpoints."""

import pytest
from httpx import AsyncClient


async def _setup(c: AsyncClient, club_id: str) -> tuple[str, str]:
    p = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 3, "name": "Jan"})).json()
    mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "K", "age_category": "U17"},
        "roster": [{"player_id": p["player_id"], "number": 3, "name": "Jan", "team": "my"}],
    })
    return mr.json()["matchId"], p["player_id"]


@pytest.mark.asyncio
async def test_substitution_flow(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, pid = await _setup(c, club_id)

    # Sub in
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/substitutions", json={"player_id": pid, "direction": "in"})
    assert r.status_code == 201

    # Playtime — player on water
    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/playtime")
    assert r.status_code == 200
    assert r.json()["players"][pid]["on_water"] is True

    # Sub out
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/substitutions", json={"player_id": pid, "direction": "out"})
    assert r.status_code == 201

    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/playtime")
    assert r.json()["players"][pid]["on_water"] is False
    assert r.json()["players"][pid]["seconds"] >= 0


@pytest.mark.asyncio
async def test_invalid_direction(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, pid = await _setup(c, club_id)
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/substitutions", json={"player_id": pid, "direction": "sideways"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_end_match_closes_open_stints(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, pid = await _setup(c, club_id)

    await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/substitutions", json={"player_id": pid, "direction": "in"})
    await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/end")

    # After ending, the open stint should be closed (player no longer on water)
    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/playtime")
    assert r.json()["players"][pid]["on_water"] is False
