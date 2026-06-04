"""Full E2E flow test — register → club → player → match → events → stats.

Tests 1:1 feature parity with the original monolith.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_match_flow(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    # ── 1. Create player ──
    r = await c.post(f"/v1/clubs/{club_id}/players", json={"number": 7, "name": "Anna Nowak"})
    assert r.status_code == 201
    player = r.json()
    assert player["number"] == 7
    player_id = player["player_id"]

    # ── 2. Create match with roster ──
    r = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "Kraków", "age_category": "Seniorzy"},
        "roster": [{"player_id": player_id, "number": 7, "name": "Anna Nowak", "team": "my"}],
    })
    assert r.status_code == 201
    match_id = r.json()["matchId"]

    # ── 3. Set active match ──
    r = await c.put(f"/v1/clubs/{club_id}/settings/active-match", json={"match_id": match_id})
    assert r.status_code == 200
    assert r.json()["ActiveMatch"] == match_id

    # ── 4. Record events ──
    r = await c.post(f"/v1/clubs/{club_id}/events", json={"events": [
        {"player_id": player_id, "player_name": "Anna Nowak", "is_goal_from_play_positional": 1},
        {"player_id": player_id, "player_name": "Anna Nowak", "is_assist_positional": 1},
        {"player_id": player_id, "player_name": "Anna Nowak", "is_steal_positional": 1},
    ]})
    assert r.status_code == 200
    assert r.json()["count"] == 3

    # ── 5. Get recent events ──
    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/events?limit=10")
    assert r.status_code == 200
    events = r.json()
    assert len(events) == 3
    actions = {e["action"] for e in events}
    assert "G z akcji (poz.)" in actions
    assert "Asysta (poz.)" in actions
    assert "Przejęcie (poz.)" in actions

    # ── 6. Get match stats ──
    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/stats")
    assert r.status_code == 200
    stats = r.json()
    assert len(stats["flags"]) == 44
    assert stats["totalsAll"]["is_goal_from_play_positional"] == 1
    assert stats["totalsAll"]["is_assist_positional"] == 1
    assert stats["totalsAll"]["is_steal_positional"] == 1
    assert stats["perPlayerAll"][player_id]["is_goal_from_play_positional"] == 1

    # ── 7. Save score ──
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/scores", json={
        "quarter": "1", "my_score": 5, "opp_score": 3,
    })
    assert r.status_code == 200
    scores = r.json()
    assert scores["1"]["my"] == 5

    # ── 8. Undo last event ──
    r = await c.post(f"/v1/clubs/{club_id}/events/undo", json={"window_minutes": 5})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Verify one event was removed
    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/events?limit=10")
    assert len(r.json()) == 2

    # ── 9. End match ──
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/end")
    assert r.status_code == 200
    assert r.json()["status"] == "ended"

    # ── 10. Archive match ──
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/archive")
    assert r.status_code == 200
    assert r.json()["archived"] is True

    # ── 11. Verify match is gone from list ──
    r = await c.get(f"/v1/clubs/{club_id}/matches")
    assert r.status_code == 200
    assert len(r.json()) == 0  # Archived = hidden


@pytest.mark.asyncio
async def test_bootstrap(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    r = await c.get(f"/v1/clubs/{club_id}/bootstrap")
    assert r.status_code == 200
    data = r.json()
    assert "settings" in data
    assert "players" in data
    assert "matches" in data
    assert "user" in data
    assert "config" in data
    assert data["user"]["role"] == "owner"
    assert "active_modules" in data["config"]


@pytest.mark.asyncio
async def test_club_isolation(client: AsyncClient):
    """Data from club A should not be visible to club B."""
    # Create two users with two clubs
    await client.post("/v1/auth/register", json={"email": "a@a.pl", "password": "pass"})
    await client.post("/v1/auth/register", json={"email": "b@b.pl", "password": "pass"})

    login_a = await client.post("/v1/auth/login", json={"email": "a@a.pl", "password": "pass"})
    token_a = login_a.json()["access_token"]

    login_b = await client.post("/v1/auth/login", json={"email": "b@b.pl", "password": "pass"})
    token_b = login_b.json()["access_token"]

    club_a = await client.post("/v1/clubs", json={"name": "Club A"}, headers={"Authorization": f"Bearer {token_a}"})
    club_a_id = club_a.json()["id"]

    # Re-login to get club context
    login_a2 = await client.post("/v1/auth/login", json={"email": "a@a.pl", "password": "pass"})
    token_a = login_a2.json()["access_token"]

    club_b = await client.post("/v1/clubs", json={"name": "Club B"}, headers={"Authorization": f"Bearer {token_b}"})
    club_b_id = club_b.json()["id"]

    # User A creates a player in club A
    r = await client.post(
        f"/v1/clubs/{club_a_id}/players",
        json={"number": 1, "name": "Player A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201

    # User B should NOT see Player A (they're not a member of club A)
    login_b2 = await client.post("/v1/auth/login", json={"email": "b@b.pl", "password": "pass"})
    token_b = login_b2.json()["access_token"]

    r = await client.get(
        f"/v1/clubs/{club_a_id}/players",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 403  # Not a member

    # User B can see their own club (empty)
    r = await client.get(
        f"/v1/clubs/{club_b_id}/players",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 0


@pytest.mark.asyncio
async def test_config_endpoint(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    # Get default config
    r = await c.get(f"/v1/clubs/{club_id}/config")
    assert r.status_code == 200
    data = r.json()
    assert len(data["active_modules"]) == 5
    assert len(data["active_flags"]) == 44

    # Update config — disable man-up modules
    r = await c.put(f"/v1/clubs/{club_id}/config", json={
        "active_modules": ["attack_positional", "penalties", "defense_positional"],
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["active_modules"]) == 3
    assert "attack_man_up" not in data["active_modules"]
    assert len(data["active_flags"]) < 44  # Fewer flags when modules disabled
