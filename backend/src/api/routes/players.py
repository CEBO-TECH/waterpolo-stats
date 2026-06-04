"""Player routes — port of /api/players."""

import uuid

from fastapi import APIRouter, HTTPException

from src.api.deps import AnyMember, CoachOrOwner, PlayerRepo
from src.api.schemas.player import AgeCategoryUpdate, PlayerCreate, PlayerResponse
from src.domain.models import Player

router = APIRouter(prefix="/v1/clubs/{club_id}/players", tags=["players"])


@router.get("", response_model=list[PlayerResponse])
async def list_players(
    club_id: str, ctx: AnyMember, repo: PlayerRepo,
):
    players = await repo.list_by_club(club_id)
    return [
        PlayerResponse(
            player_id=p.player_id, number=p.number, name=p.name, team=p.team
        )
        for p in players
    ]


@router.post("", response_model=PlayerResponse, status_code=201)
async def create_player(
    club_id: str, body: PlayerCreate, ctx: CoachOrOwner, repo: PlayerRepo,
):
    player = Player(
        id=str(uuid.uuid4()),
        club_id=club_id,
        player_id=f"player_{int(uuid.uuid4().time_low)}",
        number=body.number,
        name=body.name,
        team=body.team,
    )
    created = await repo.create(player)
    return PlayerResponse(
        player_id=created.player_id, number=created.number,
        name=created.name, team=created.team,
    )


@router.delete("/{player_id}")
async def delete_player(
    club_id: str, player_id: str, ctx: CoachOrOwner, repo: PlayerRepo,
):
    existing = await repo.get_by_player_id(club_id, player_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Player not found")
    await repo.delete(club_id, player_id)
    return {"ok": True}


@router.get("/{player_id}/age-categories")
async def get_age_categories(
    club_id: str, player_id: str, ctx: AnyMember, repo: PlayerRepo,
):
    categories = await repo.get_age_categories(player_id)
    return [{"age_category": c.age_category} for c in categories]


@router.put("/{player_id}/age-categories")
async def set_age_categories(
    club_id: str, player_id: str, body: AgeCategoryUpdate,
    ctx: CoachOrOwner, repo: PlayerRepo,
):
    result = await repo.set_age_categories(player_id, body.categories)
    return [{"age_category": c.age_category} for c in result]
