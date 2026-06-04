"""Season management routes."""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.deps import AnyMember, OwnerOnly, SeasonRepo
from src.domain.models import Season

router = APIRouter(prefix="/v1/clubs/{club_id}/seasons", tags=["seasons"])


class SeasonCreate(BaseModel):
    name: str
    start_date: str  # ISO date
    end_date: str
    is_active: bool = True


class SeasonResponse(BaseModel):
    id: str
    name: str
    start_date: str
    end_date: str
    is_active: bool


@router.get("", response_model=list[SeasonResponse])
async def list_seasons(club_id: str, ctx: AnyMember, repo: SeasonRepo):
    seasons = await repo.list_by_club(club_id)
    return [
        SeasonResponse(
            id=s.id, name=s.name,
            start_date=str(s.start_date), end_date=str(s.end_date),
            is_active=s.is_active,
        )
        for s in seasons
    ]


@router.post("", response_model=SeasonResponse, status_code=201)
async def create_season(club_id: str, body: SeasonCreate, ctx: OwnerOnly, repo: SeasonRepo):
    season = Season(
        id=str(uuid.uuid4()),
        club_id=club_id,
        name=body.name,
        start_date=date.fromisoformat(body.start_date),
        end_date=date.fromisoformat(body.end_date),
        is_active=body.is_active,
    )
    created = await repo.create(season)
    return SeasonResponse(
        id=created.id, name=created.name,
        start_date=str(created.start_date), end_date=str(created.end_date),
        is_active=created.is_active,
    )


@router.put("/{season_id}", response_model=SeasonResponse)
async def update_season(
    club_id: str, season_id: str, body: SeasonCreate,
    ctx: OwnerOnly, repo: SeasonRepo,
):
    existing = await repo.get_by_id(club_id, season_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Season not found")

    existing.name = body.name
    existing.start_date = date.fromisoformat(body.start_date)
    existing.end_date = date.fromisoformat(body.end_date)
    existing.is_active = body.is_active

    updated = await repo.update(existing)
    return SeasonResponse(
        id=updated.id, name=updated.name,
        start_date=str(updated.start_date), end_date=str(updated.end_date),
        is_active=updated.is_active,
    )


@router.delete("/{season_id}")
async def delete_season(club_id: str, season_id: str, ctx: OwnerOnly, repo: SeasonRepo):
    await repo.delete(club_id, season_id)
    return {"ok": True}
