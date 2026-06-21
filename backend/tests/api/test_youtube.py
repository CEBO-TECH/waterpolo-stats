"""YouTube stream attach + per-event video jump."""

import pytest
from httpx import AsyncClient


async def _setup_match(c: AsyncClient, club_id: str) -> tuple[str, str]:
    p = (await c.post(f"/v1/clubs/{club_id}/players", json={"number": 5, "name": "X"})).json()
    pid = p["player_id"]
    mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "Legia", "place": "K", "age_category": "U17"},
        "roster": [{"player_id": pid, "number": 5, "name": "X", "team": "my"}],
    })
    return mr.json()["matchId"], pid


@pytest.mark.asyncio
async def test_attach_stream_and_event_jump(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, pid = await _setup_match(c, club_id)
    await c.put(f"/v1/clubs/{club_id}/settings/active-match", json={"match_id": match_id})

    # Attach stream with a past start time so the seek is meaningful
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/youtube", json={
        "youtube_url": "https://youtu.be/dQw4w9WgXcQ",
        "stream_start_time": "2020-01-01T00:00:00",
    })
    assert r.status_code == 201
    assert r.json()["video_id"] == "dQw4w9WgXcQ"

    # Record an event
    await c.post(f"/v1/clubs/{club_id}/events", json={"events": [
        {"player_id": pid, "player_name": "X", "is_goal_from_play_positional": 1},
    ]})
    ev = (await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/events?limit=10")).json()[0]

    # Jump URL for the event
    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/events/{ev['id']}/video-url")
    assert r.status_code == 200
    d = r.json()
    assert d["video_id"] == "dQw4w9WgXcQ"
    assert d["seek_seconds"] > 0
    assert "dQw4w9WgXcQ" in d["video_url"]


@pytest.mark.asyncio
async def test_start_now(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, _ = await _setup_match(c, club_id)
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/youtube", json={
        "youtube_url": "https://www.youtube.com/watch?v=abcdefghijk",
        "start_now": True,
    })
    assert r.status_code == 201
    assert r.json()["stream_start_time"] is not None


@pytest.mark.asyncio
async def test_auto_detect_start_from_youtube(auth_client: AsyncClient, monkeypatch):
    """Pasting just a link auto-detects the broadcast start (no start_now)."""
    from datetime import datetime

    class _FakeYouTube:
        def extract_video_id(self, url):
            return "abcdefghijk" if "youtu" in url else None

        async def get_stream_start_time(self, video_id):
            return datetime(2021, 5, 1, 18, 0, 0)

    monkeypatch.setattr(
        "src.api.routes.youtube.get_youtube_port", lambda: _FakeYouTube()
    )

    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, _ = await _setup_match(c, club_id)
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/youtube", json={
        "youtube_url": "https://youtu.be/abcdefghijk",
    })
    assert r.status_code == 201
    assert r.json()["stream_start_time"] == "2021-05-01T18:00:00"


@pytest.mark.asyncio
async def test_invalid_youtube_url(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore
    match_id, _ = await _setup_match(c, club_id)
    r = await c.post(f"/v1/clubs/{club_id}/matches/{match_id}/youtube", json={
        "youtube_url": "https://example.com/not-a-video",
    })
    assert r.status_code == 400
