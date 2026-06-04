"""Settings routes — port of /api/settings, /api/settings/match, /api/settings/quarter."""

from fastapi import APIRouter

from src.api.deps import AnyMember, CoachOrOwner, SettingsRepo
from src.api.schemas.settings import (
    SetActiveMatchRequest,
    SetQuarterRequest,
    SettingsResponse,
)

router = APIRouter(prefix="/v1/clubs/{club_id}/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    club_id: str, ctx: AnyMember, repo: SettingsRepo,
):
    s = await repo.get_for_club(club_id)
    return SettingsResponse(ActiveMatch=s.active_match, Quarter=s.quarter)


@router.put("/active-match", response_model=SettingsResponse)
async def set_active_match(
    club_id: str, body: SetActiveMatchRequest, ctx: CoachOrOwner, repo: SettingsRepo,
):
    s = await repo.set_active_match(club_id, body.match_id)
    return SettingsResponse(ActiveMatch=s.active_match, Quarter=s.quarter)


@router.put("/quarter", response_model=SettingsResponse)
async def set_quarter(
    club_id: str, body: SetQuarterRequest, ctx: CoachOrOwner, repo: SettingsRepo,
):
    s = await repo.set_quarter(club_id, body.quarter)
    return SettingsResponse(ActiveMatch=s.active_match, Quarter=s.quarter)
