"""Player management tests — edit, age categories, list enrichment."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_player(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    created = await c.post(f"/v1/clubs/{club_id}/players", json={"number": 5, "name": "Jan Kowalski"})
    player_id = created.json()["player_id"]

    r = await c.put(
        f"/v1/clubs/{club_id}/players/{player_id}",
        json={"number": 9, "name": "Jan Nowak"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["number"] == 9
    assert data["name"] == "Jan Nowak"


@pytest.mark.asyncio
async def test_update_player_not_found(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.put(f"/v1/clubs/{club_id}/players/nope", json={"number": 1})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_player_no_fields(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    created = await c.post(f"/v1/clubs/{club_id}/players", json={"number": 5, "name": "X"})
    player_id = created.json()["player_id"]
    r = await c.put(f"/v1/clubs/{club_id}/players/{player_id}", json={})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_age_categories_in_list(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    created = await c.post(f"/v1/clubs/{club_id}/players", json={"number": 3, "name": "Adam"})
    player_id = created.json()["player_id"]

    # Newly created player has no categories
    r = await c.get(f"/v1/clubs/{club_id}/players")
    assert r.json()[0]["age_categories"] == []

    # Assign categories
    r = await c.put(
        f"/v1/clubs/{club_id}/players/{player_id}/age-categories",
        json={"categories": ["U17", "Seniorzy"]},
    )
    assert r.status_code == 200

    # List now includes them
    r = await c.get(f"/v1/clubs/{club_id}/players")
    assert sorted(r.json()[0]["age_categories"]) == ["Seniorzy", "U17"]
