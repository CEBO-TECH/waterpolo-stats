"""Bootstrap route — loads initial app state. Port of GET /api/bootstrap."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.api.deps import (
    AnyMember,
    ConfigRepo,
    MatchRepo,
    PlayerRepo,
    RosterRepo,
    SettingsRepo,
    YouTubeRepo,
)

router = APIRouter(prefix="/v1/clubs/{club_id}", tags=["bootstrap"])


@router.get("/bootstrap")
async def get_bootstrap(
    club_id: str,
    ctx: AnyMember,
    settings_repo: SettingsRepo,
    player_repo: PlayerRepo,
    match_repo: MatchRepo,
    roster_repo: RosterRepo,
    config_repo: ConfigRepo,
    youtube_repo: YouTubeRepo,
):
    """Load initial data for the app — settings, players, matches, roster, config."""
    user, membership = ctx

    settings = await settings_repo.get_for_club(club_id)
    players = await player_repo.list_by_club(club_id)
    matches = await match_repo.list_active(club_id)
    config = await config_repo.get_for_club(club_id)

    # Get roster for active match
    roster_active = []
    if settings.active_match:
        roster_active = await roster_repo.get_for_match(club_id, settings.active_match)

    # Get YouTube stream for active match
    youtube = None
    if settings.active_match:
        stream = await youtube_repo.get_for_match(settings.active_match)
        if stream:
            youtube = {
                "youtube_url": stream.youtube_url,
                "video_id": stream.video_id,
                "stream_start_time": stream.stream_start_time.isoformat() if stream.stream_start_time else None,
            }

    return JSONResponse(
        content={
            "settings": {
                "ActiveMatch": settings.active_match,
                "Quarter": settings.quarter,
            },
            "players": [
                {"player_id": p.player_id, "number": p.number, "name": p.name, "team": p.team}
                for p in players
            ],
            "matches": [
                {
                    "match_id": m.match_id, "date": m.date, "opponent": m.opponent,
                    "place": m.place, "ageCategory": m.age_category, "status": m.status.value,
                }
                for m in matches
            ],
            "user": {"email": user.email, "role": membership.role.value},
            "rosterActive": [
                {"match_id": r.match_id, "player_id": r.player_id, "number": r.number, "name": r.name, "team": r.team}
                for r in roster_active
            ],
            "config": {
                "active_modules": config.active_modules,
                "button_layout": config.button_layout,
            },
            "youtube": youtube,
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
