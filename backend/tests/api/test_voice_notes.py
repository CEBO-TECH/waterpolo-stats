"""Voice-note upload / list / playback / delete (local storage)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_voice_note_flow(auth_client: AsyncClient):
    c = auth_client
    club_id = c._club_id  # type: ignore

    mr = await c.post(f"/v1/clubs/{club_id}/matches", json={
        "match": {"date": "2026-06-01", "opponent": "L", "place": "K", "age_category": "U17"},
        "roster": [],
    })
    match_id = mr.json()["matchId"]

    audio = b"FAKE-AUDIO-BYTES"
    r = await c.post(
        f"/v1/clubs/{club_id}/matches/{match_id}/voice-notes",
        files={"file": ("note.webm", audio, "audio/webm")},
        data={"duration_s": "7", "note": "timeout Q3"},
    )
    assert r.status_code == 201
    note_id = r.json()["id"]
    assert r.json()["duration_s"] == 7
    assert r.json()["note"] == "timeout Q3"

    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/voice-notes")
    assert len(r.json()) == 1

    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/voice-notes/{note_id}/audio")
    assert r.status_code == 200
    assert r.content == audio

    r = await c.delete(f"/v1/clubs/{club_id}/matches/{match_id}/voice-notes/{note_id}")
    assert r.status_code == 200

    r = await c.get(f"/v1/clubs/{club_id}/matches/{match_id}/voice-notes")
    assert len(r.json()) == 0
