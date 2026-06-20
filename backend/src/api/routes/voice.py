"""Voice command agent — resolve a spoken utterance to an event.

POST /v1/clubs/{club_id}/voice/parse takes a transcript (from the browser's
Web Speech API), runs the deterministic parser first, falls back to Claude for
free-form phrasing, then resolves the cap number against the active roster.
The frontend shows the result for confirmation and enqueues it via /events —
so a spoken command flows through the exact same offline-resilient path as a tap.
"""

from fastapi import APIRouter

from src.adapters.ai.claude_nlu import get_voice_command_port
from src.api.deps import CoachOrOwner, RosterRepo, SettingsRepo
from src.api.schemas.voice import VoiceParseRequest, VoiceParseResponse
from src.domain.models import EVENT_FLAG_FIELDS, EVENT_FLAG_LABELS
from src.domain.services import VoiceCommandService

router = APIRouter(prefix="/v1/clubs/{club_id}", tags=["voice"])
voice_service = VoiceCommandService()


@router.post("/voice/parse", response_model=VoiceParseResponse)
async def parse_voice_command(
    club_id: str, body: VoiceParseRequest,
    ctx: CoachOrOwner, roster_repo: RosterRepo, settings_repo: SettingsRepo,
):
    transcript = (body.transcript or "").strip()
    if not transcript:
        return VoiceParseResponse(matched=False, transcript="", reason="Pusta komenda")

    settings = await settings_repo.get_for_club(club_id)
    match_id = body.match_id or settings.active_match
    roster = await roster_repo.get_for_match(club_id, match_id) if match_id else []
    by_number = {e.number: e for e in roster}

    # 1) deterministic parser (offline, instant)
    parsed = voice_service.parse(transcript)

    # 2) Claude fallback when nothing matched or the number is missing
    if parsed is None or parsed.number is None:
        port = get_voice_command_port()
        if port is not None:
            claude = await port.parse(
                transcript, list(by_number.keys()), EVENT_FLAG_LABELS
            )
            # prefer Claude only if it adds information (a flag, or the missing number)
            if claude is not None and (parsed is None or claude.number is not None):
                parsed = claude

    if parsed is None or parsed.flag not in EVENT_FLAG_FIELDS:
        return VoiceParseResponse(
            matched=False, transcript=transcript, reason="Nie rozpoznano akcji"
        )

    if parsed.number is None:
        return VoiceParseResponse(
            matched=False, transcript=transcript,
            reason="Nie rozpoznano numeru zawodnika",
        )

    entry = by_number.get(parsed.number)
    if entry is None:
        return VoiceParseResponse(
            matched=False, transcript=transcript,
            reason=f"Numer {parsed.number} nie jest w składzie",
        )

    return VoiceParseResponse(
        matched=True,
        transcript=transcript,
        player_id=entry.player_id,
        player_name=entry.name,
        number=parsed.number,
        flag=parsed.flag,
        label=EVENT_FLAG_LABELS.get(parsed.flag, parsed.flag),
        confidence=parsed.confidence,
        source=parsed.source,
    )
