"""Voice-note routes — record/list/play/delete short audio notes per match."""

import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from src.adapters.storage import get_storage
from src.api.deps import AnyMember, CoachOrOwner, VoiceNoteRepo
from src.domain.models import VoiceNote

router = APIRouter(
    prefix="/v1/clubs/{club_id}/matches/{match_id}/voice-notes",
    tags=["voice-notes"],
)


def _dto(n: VoiceNote) -> dict:
    return {
        "id": n.id, "player_id": n.player_id, "duration_s": n.duration_s,
        "note": n.note, "content_type": n.content_type,
        "created_by": n.created_by, "created_at": n.created_at.isoformat(),
    }


@router.post("", status_code=201)
async def upload_voice_note(
    club_id: str, match_id: str, ctx: CoachOrOwner, repo: VoiceNoteRepo,
    file: UploadFile = File(...),
    player_id: str = Form(""),
    duration_s: int = Form(0),
    note: str = Form(""),
):
    user, _ = ctx
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio")

    note_id = str(uuid.uuid4())
    content_type = file.content_type or "audio/webm"
    key = f"{club_id}/{match_id}/{note_id}.webm"
    get_storage().put(key, data, content_type)

    created = await repo.create(VoiceNote(
        id=note_id, club_id=club_id, match_id=match_id, audio_key=key,
        content_type=content_type, duration_s=duration_s,
        player_id=player_id or None, note=note, created_by=user.email,
    ))
    return _dto(created)


@router.get("")
async def list_voice_notes(club_id: str, match_id: str, ctx: AnyMember, repo: VoiceNoteRepo):
    notes = await repo.list_for_match(club_id, match_id)
    return [_dto(n) for n in notes]


@router.get("/{note_id}/audio")
async def get_voice_note_audio(
    club_id: str, match_id: str, note_id: str, ctx: AnyMember, repo: VoiceNoteRepo,
):
    n = await repo.get_by_id(club_id, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="Voice note not found")
    data = get_storage().get_bytes(n.audio_key)
    if data is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    return Response(content=data, media_type=n.content_type)


@router.delete("/{note_id}")
async def delete_voice_note(
    club_id: str, match_id: str, note_id: str, ctx: CoachOrOwner, repo: VoiceNoteRepo,
):
    n = await repo.get_by_id(club_id, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="Voice note not found")
    get_storage().delete(n.audio_key)
    await repo.delete(club_id, note_id)
    return {"ok": True}
