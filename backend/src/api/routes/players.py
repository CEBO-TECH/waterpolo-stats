"""Player routes — port of /api/players."""

import uuid

from fastapi import APIRouter, HTTPException

from src.api.deps import AnyMember, CoachOrOwner, PlayerRepo
from src.api.schemas.player import (
    AgeCategoryUpdate,
    PlayerCreate,
    PlayerResponse,
    PlayerUpdate,
)
from src.domain.models import Player

router = APIRouter(prefix="/v1/clubs/{club_id}/players", tags=["players"])


def _player_response(p: Player, age_categories: list[str]) -> PlayerResponse:
    return PlayerResponse(
        player_id=p.player_id, number=p.number, name=p.name, team=p.team,
        birth_year=p.birth_year, email=p.email, has_account=p.user_id is not None,
        age_categories=age_categories,
    )


@router.get("", response_model=list[PlayerResponse])
async def list_players(
    club_id: str, ctx: AnyMember, repo: PlayerRepo,
):
    players = await repo.list_by_club(club_id)
    categories = await repo.get_age_categories_map(club_id)
    return [_player_response(p, categories.get(p.player_id, [])) for p in players]


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
        birth_year=body.birth_year,
        email=body.email,
    )
    created = await repo.create(player)
    return _player_response(created, [])


@router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(
    club_id: str, player_id: str, body: PlayerUpdate,
    ctx: CoachOrOwner, repo: PlayerRepo,
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = await repo.update_fields(club_id, player_id, fields)
    if not updated:
        raise HTTPException(status_code=404, detail="Player not found")
    categories = await repo.get_age_categories(player_id)
    return _player_response(updated, [c.age_category for c in categories])


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
