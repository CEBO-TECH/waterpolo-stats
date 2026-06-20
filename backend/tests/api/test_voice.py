"""Voice command route — transcript resolved against the match roster."""

import pytest
from httpx import AsyncClient


async def _match_with_roster(c: AsyncClient, club_id: str):
    p1 = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 12, "name": "Kowalski"})).json()
    p2 = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 7, "name": "Nowak"})).json()
    r = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "Kraków", "age_category": "U17"},
        "roster": [
            {"player_id": p1["player_id"], "number": 12, "name": "Kowalski", "team": "my"},
            {"player_id": p2["player_id"], "number": 7, "name": "Nowak", "team": "my"},
        ],
    })
    return r.json()["matchId"], p1


@pytest.mark.asyncio
async def test_parse_resolves_player(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, p1 = await _match_with_roster(c, club_id)

    r = await c.post(f"/v1/clubs/{club_id}/voice/parse", json={
        "transcript": "numer dwanaście gol z kontrataku", "match_id": match_id,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["matched"] is True
    assert data["flag"] == "is_goal_from_play_counter"
    assert data["number"] == 12
    assert data["player_id"] == p1["player_id"]
    assert data["player_name"] == "Kowalski"
    assert data["source"] == "deterministic"


@pytest.mark.asyncio
async def test_parse_number_not_in_roster(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, _ = await _match_with_roster(c, club_id)

    r = await c.post(f"/v1/clubs/{club_id}/voice/parse", json={
        "transcript": "numer 5 asysta", "match_id": match_id,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["matched"] is False
    assert "5" in data["reason"]


@pytest.mark.asyncio
async def test_parse_unrecognised_action(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, _ = await _match_with_roster(c, club_id)

    r = await c.post(f"/v1/clubs/{club_id}/voice/parse", json={
        "transcript": "dzień dobry wszystkim", "match_id": match_id,
    })
    assert r.status_code == 200
    assert r.json()["matched"] is False
