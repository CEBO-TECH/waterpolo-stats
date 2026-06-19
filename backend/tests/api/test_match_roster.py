"""Match roster management — create without roster, set roster later, counts."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_without_roster_then_add(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    # Players
    p1 = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 3, "name": "A"})).json()
    p2 = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 7, "name": "B"})).json()

    # Create match WITHOUT roster
    r = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "Kraków", "age_category": "U17"},
        "roster": [],
    })
    assert r.status_code == 201
    match_id = r.json()["matchId"]

    # List shows roster_count 0
    r = await c.get(f"/v1/clubs/{club_id}/matches")
    m = next(x for x in r.json() if x["match_id"] == match_id)
    assert m["roster_count"] == 0

    # Add roster later
    r = await c.put(f"/v1/clubs/{club_id}/matches/{match_id}/roster", json={
        "roster": [
            {"player_id": p1["player_id"], "number": 3, "name": "A", "team": "my"},
            {"player_id": p2["player_id"], "number": 7, "name": "B", "team": "my"},
        ],
    })
    assert r.status_code == 200
    assert len(r.json()) == 2

    # List now shows roster_count 2
    r = await c.get(f"/v1/clubs/{club_id}/matches")
    m = next(x for x in r.json() if x["match_id"] == match_id)
    assert m["roster_count"] == 2

    # Bootstrap also exposes rosterCount
    r = await c.get(f"/v1/clubs/{club_id}/bootstrap")
    bm = next(x for x in r.json()["matches"] if x["match_id"] == match_id)
    assert bm["rosterCount"] == 2


@pytest.mark.asyncio
async def test_set_roster_match_not_found(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.put(f"/v1/clubs/{club_id}/matches/nope/roster", json={"roster": []})
    assert r.status_code == 404
