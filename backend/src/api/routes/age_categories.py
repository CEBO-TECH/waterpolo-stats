"""Club age-category dictionary routes (per-club editable list)."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.deps import AgeCategoryRepo, AnyMember, CoachOrOwner
from src.domain.models import AgeCategory

router = APIRouter(prefix="/v1/clubs/{club_id}/age-categories", tags=["age-categories"])


class AgeCategoryCreate(BaseModel):
    name: str


class AgeCategoryUpdateRequest(BaseModel):
    name: str | None = None
    sort_order: int | None = None


class AgeCategoryResponse(BaseModel):
    id: str
    name: str
    sort_order: int


@router.get("", response_model=list[AgeCategoryResponse])
async def list_age_categories(club_id: str, ctx: AnyMember, repo: AgeCategoryRepo):
    cats = await repo.list_by_club(club_id)
    return [AgeCategoryResponse(id=c.id, name=c.name, sort_order=c.sort_order) for c in cats]


@router.post("", response_model=AgeCategoryResponse, status_code=201)
async def create_age_category(
    club_id: str, body: AgeCategoryCreate, ctx: CoachOrOwner, repo: AgeCategoryRepo,
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    existing = await repo.list_by_club(club_id)
    if any(c.name.lower() == name.lower() for c in existing):
        raise HTTPException(status_code=400, detail="Category already exists")

    created = await repo.create(AgeCategory(
        id=str(uuid.uuid4()),
        club_id=club_id,
        name=name,
        sort_order=len(existing),
    ))
    return AgeCategoryResponse(id=created.id, name=created.name, sort_order=created.sort_order)


@router.put("/{category_id}", response_model=AgeCategoryResponse)
async def update_age_category(
    club_id: str, category_id: str, body: AgeCategoryUpdateRequest,
    ctx: CoachOrOwner, repo: AgeCategoryRepo,
):
    existing = await repo.list_by_club(club_id)
    current = next((c for c in existing if c.id == category_id), None)
    if not current:
        raise HTTPException(status_code=404, detail="Category not found")

    if body.name is not None:
        current.name = body.name.strip()
    if body.sort_order is not None:
        current.sort_order = body.sort_order

    updated = await repo.update(current)
    return AgeCategoryResponse(id=updated.id, name=updated.name, sort_order=updated.sort_order)


@router.delete("/{category_id}")
async def delete_age_category(
    club_id: str, category_id: str, ctx: CoachOrOwner, repo: AgeCategoryRepo,
):
    await repo.delete(club_id, category_id)
    return {"ok": True}
