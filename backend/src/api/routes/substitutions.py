"""Substitution / play-time routes — woda/ławka i czas gry."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.deps import AnyMember, CoachOrOwner, SubstitutionRepo
from src.domain.models import Substitution
from src.domain.services import PlaytimeService

router = APIRouter(prefix="/v1/clubs/{club_id}/matches/{match_id}", tags=["substitutions"])
playtime_service = PlaytimeService()


class SubstitutionCreate(BaseModel):
    player_id: str
    direction: str  # "in" | "out"
    quarter: int = 1


@router.post("/substitutions", status_code=201)
async def create_substitution(
    club_id: str, match_id: str, body: SubstitutionCreate,
    ctx: CoachOrOwner, repo: SubstitutionRepo,
):
    if body.direction not in ("in", "out"):
        raise HTTPException(status_code=400, detail="direction must be 'in' or 'out'")
    created = await repo.create(Substitution(
        id=str(uuid.uuid4()), club_id=club_id, match_id=match_id,
        player_id=body.player_id, direction=body.direction, quarter=body.quarter,
    ))
    return {
        "id": created.id, "player_id": created.player_id,
        "direction": created.direction, "quarter": created.quarter,
        "timestamp": created.timestamp.isoformat(),
    }


@router.get("/substitutions")
async def list_substitutions(
    club_id: str, match_id: str, ctx: AnyMember, repo: SubstitutionRepo,
):
    subs = await repo.list_for_match(club_id, match_id)
    return [
        {
            "id": s.id, "player_id": s.player_id, "direction": s.direction,
            "quarter": s.quarter, "timestamp": s.timestamp.isoformat(),
        }
        for s in subs
    ]


@router.get("/playtime")
async def get_playtime(
    club_id: str, match_id: str, ctx: AnyMember, repo: SubstitutionRepo,
):
    subs = await repo.list_for_match(club_id, match_id)
    pt = playtime_service.compute(subs)
    return {
        "players": {
            pid: {
                "seconds": e.seconds,
                "on_water": e.on_water,
                "stint_start": e.stint_start.isoformat() if e.stint_start else None,
            }
            for pid, e in pt.items()
        }
    }
