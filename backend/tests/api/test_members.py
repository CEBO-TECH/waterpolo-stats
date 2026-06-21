"""Club members management + invitations."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_members_management(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    await c.post("/v1/auth/register", json={"email": "b@b.pl", "password": "pass123"})

    r = await c.post(f"/v1/clubs/{club_id}/invite", json={"email": "b@b.pl", "role": "coach"})
    assert r.status_code == 201
    assert r.json()["added"] is True

    r = await c.get(f"/v1/clubs/{club_id}/members")
    members = r.json()
    emails = {m["email"]: m["role"] for m in members}
    assert emails["test@test.pl"] == "owner"
    assert emails["b@b.pl"] == "coach"

    bid = next(m["user_id"] for m in members if m["email"] == "b@b.pl")

    r = await c.patch(f"/v1/clubs/{club_id}/members/{bid}", json={"role": "player"})
    assert r.status_code == 200 and r.json()["role"] == "player"

    r = await c.delete(f"/v1/clubs/{club_id}/members/{bid}")
    assert r.status_code == 200
    assert len((await c.get(f"/v1/clubs/{club_id}/members")).json()) == 1


@pytest.mark.asyncio
async def test_last_owner_guard(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    members = (await c.get(f"/v1/clubs/{club_id}/members")).json()
    oid = members[0]["user_id"]

    assert (await c.patch(f"/v1/clubs/{club_id}/members/{oid}", json={"role": "coach"})).status_code == 400
    assert (await c.delete(f"/v1/clubs/{club_id}/members/{oid}")).status_code == 400


@pytest.mark.asyncio
async def test_invited_email_auto_joins_on_register(client: AsyncClient):
    """Invite by email, then register that email → auto-joined, no token link."""
    await client.post("/v1/auth/register", json={"email": "owner@o.pl", "password": "pass"})
    tok = (await client.post("/v1/auth/login", json={"email": "owner@o.pl", "password": "pass"})).json()["access_token"]
    club = await client.post("/v1/clubs", json={"name": "Klub"}, headers={"Authorization": f"Bearer {tok}"})
    club_id = club.json()["id"]
    tok = (await client.post("/v1/auth/login", json={"email": "owner@o.pl", "password": "pass"})).json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}

    r = await client.post(f"/v1/clubs/{club_id}/invite", json={"email": "new@p.pl", "role": "coach"}, headers=H)
    assert r.status_code == 201 and r.json()["added"] is False
    assert len((await client.get(f"/v1/clubs/{club_id}/invitations", headers=H)).json()) == 1

    # Registering with the invited email is enough — no token accept needed.
    reg = await client.post("/v1/auth/register", json={"email": "new@p.pl", "password": "pass"})
    assert reg.status_code == 201
    assert any(cl["club_id"] == club_id and cl["role"] == "coach" for cl in reg.json()["clubs"])

    ntok = (await client.post("/v1/auth/login", json={"email": "new@p.pl", "password": "pass"})).json()["access_token"]
    NH = {"Authorization": f"Bearer {ntok}"}
    me = await client.get("/v1/auth/me", headers=NH)
    assert any(cl["club_id"] == club_id for cl in me.json()["clubs"])

    # Invitation is now consumed (no longer pending).
    assert len((await client.get(f"/v1/clubs/{club_id}/invitations", headers=H)).json()) == 0
