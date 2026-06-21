"""Player account linking — birth year, invite, accept, /me endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_player_account_flow(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    p = (await c.post(f"/v1/clubs/{club_id}/players", json={
        "number": 10, "name": "Kid", "birth_year": 2010, "email": "kid@k.pl",
    })).json()
    assert p["birth_year"] == 2010
    assert p["has_account"] is False
    pid = p["player_id"]

    mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "K", "age_category": "U17"},
        "roster": [{"player_id": pid, "number": 10, "name": "Kid", "team": "my"}],
    })
    match_id = mr.json()["matchId"]

    # No invite, no token: attaching the email to the player is enough — registering
    # with that email auto-joins the club and links the player profile.
    reg = await c.post("/v1/auth/register", json={"email": "kid@k.pl", "password": "pass123"})
    assert reg.status_code == 201
    assert any(cl["club_id"] == club_id and cl["role"] == "player" for cl in reg.json()["clubs"])
    login = await c.post("/v1/auth/login", json={"email": "kid@k.pl", "password": "pass123"})
    KH = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = await c.get(f"/v1/clubs/{club_id}/me/player", headers=KH)
    assert r.json()["player"]["player_id"] == pid
    assert r.json()["player"]["birth_year"] == 2010

    r = await c.get(f"/v1/clubs/{club_id}/me/matches", headers=KH)
    assert any(m["match_id"] == match_id for m in r.json())

    r = await c.get(f"/v1/clubs/{club_id}/players")
    kid = next(x for x in r.json() if x["player_id"] == pid)
    assert kid["has_account"] is True


@pytest.mark.asyncio
async def test_me_player_none_when_unlinked(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.get(f"/v1/clubs/{club_id}/me/player")
    assert r.status_code == 200
    assert r.json()["player"] is None
