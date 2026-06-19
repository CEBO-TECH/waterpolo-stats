"""Auth endpoint tests — register, login, me."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    r = await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "a@b.pl"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    r = await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    r = await client.post("/v1/auth/login", json={"email": "a@b.pl", "password": "pass123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    r = await client.post("/v1/auth/login", json={"email": "a@b.pl", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    r = await client.get("/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(auth_client: AsyncClient):
    r = await auth_client.get("/v1/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "test@test.pl"
    assert len(data["clubs"]) == 1
    assert data["clubs"][0]["role"] == "owner"


@pytest.mark.asyncio
async def test_select_club(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    login = await client.post("/v1/auth/login", json={"email": "a@b.pl", "password": "pass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    club = await client.post("/v1/clubs", json={"name": "Klub A"}, headers=headers)
    club_id = club.json()["id"]

    r = await client.post("/v1/auth/select-club", json={"club_id": club_id}, headers=headers)
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_select_club_not_member(client: AsyncClient):
    await client.post("/v1/auth/register", json={"email": "a@b.pl", "password": "pass123"})
    login = await client.post("/v1/auth/login", json={"email": "a@b.pl", "password": "pass123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    r = await client.post("/v1/auth/select-club", json={"club_id": "nonexistent"}, headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_select_club_unauthenticated(client: AsyncClient):
    r = await client.post("/v1/auth/select-club", json={"club_id": "x"})
    assert r.status_code == 401
