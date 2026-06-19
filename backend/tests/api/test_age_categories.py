"""Club age-category dictionary tests — seeding, CRUD, bootstrap."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_defaults_seeded_on_club_create(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.get(f"/v1/clubs/{club_id}/age-categories")
    assert r.status_code == 200
    names = [x["name"] for x in r.json()]
    assert names == ["Seniorzy", "U19", "U17", "U15"]


@pytest.mark.asyncio
async def test_create_and_delete_category(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    r = await c.post(f"/v1/clubs/{club_id}/age-categories", json={"name": "U13"})
    assert r.status_code == 201
    cat_id = r.json()["id"]
    assert r.json()["name"] == "U13"

    r = await c.get(f"/v1/clubs/{club_id}/age-categories")
    assert "U13" in [x["name"] for x in r.json()]

    r = await c.delete(f"/v1/clubs/{club_id}/age-categories/{cat_id}")
    assert r.status_code == 200

    r = await c.get(f"/v1/clubs/{club_id}/age-categories")
    assert "U13" not in [x["name"] for x in r.json()]


@pytest.mark.asyncio
async def test_create_duplicate_category(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.post(f"/v1/clubs/{club_id}/age-categories", json={"name": "U17"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_bootstrap_includes_age_categories(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.get(f"/v1/clubs/{club_id}/bootstrap")
    assert r.status_code == 200
    cats = r.json()["ageCategories"]
    assert [x["name"] for x in cats] == ["Seniorzy", "U19", "U17", "U15"]


@pytest.mark.asyncio
async def test_match_without_category(auth_client: AsyncClient):
    """A match can be created with an empty age category ('mecz bez grupy')."""
    c = auth_client
    club_id = c._club_id  # type: ignore
    r = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Sparing", "place": "Kraków", "age_category": ""},
        "roster": [],
    })
    assert r.status_code == 201
    r = await c.get(f"/v1/clubs/{club_id}/matches")
    assert r.json()[0]["age_category"] == ""
