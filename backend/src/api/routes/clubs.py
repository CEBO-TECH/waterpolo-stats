"""Club management routes."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from src.api.deps import (
    ClubRepo,
    ConfigRepo,
    CurrentUser,
    DBSession,
    OwnerOnly,
    SettingsRepo,
    UserRepo,
)
from src.domain.models import Club, ClubMembership, UserRole

router = APIRouter(prefix="/v1/clubs", tags=["clubs"])


class ClubCreateRequest(BaseModel):
    name: str


class ClubResponse(BaseModel):
    id: str
    name: str
    club_type: str


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "player"  # "coach" or "player"


@router.post("", response_model=ClubResponse, status_code=201)
async def create_club(
    body: ClubCreateRequest,
    user: CurrentUser,
    club_repo: ClubRepo,
    user_repo: UserRepo,
    settings_repo: SettingsRepo,
    config_repo: ConfigRepo,
):
    """Create a new club. The authenticated user becomes the owner."""
    club = Club(id=str(uuid.uuid4()), name=body.name)
    created = await club_repo.create(club)

    # Create owner membership
    membership = ClubMembership(
        id=str(uuid.uuid4()),
        user_id=user.id,
        club_id=created.id,
        role=UserRole.OWNER,
    )
    await user_repo.create_membership(membership)

    # Create default settings and config for the club
    await settings_repo.create_default(created.id)
    await config_repo.create_default(created.id)

    return ClubResponse(
        id=created.id, name=created.name, club_type=created.club_type.value
    )


@router.post("/{club_id}/invite", status_code=201)
async def invite_user(
    club_id: str,
    body: InviteRequest,
    ctx: OwnerOnly,
    user_repo: UserRepo,
):
    """Invite a user to the club by email. Owner only."""
    target_user = await user_repo.get_by_email(body.email)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await user_repo.get_membership(target_user.id, club_id)
    if existing:
        raise HTTPException(status_code=400, detail="User already a member")

    role = UserRole(body.role) if body.role in ("coach", "player") else UserRole.PLAYER
    membership = ClubMembership(
        id=str(uuid.uuid4()),
        user_id=target_user.id,
        club_id=club_id,
        role=role,
    )
    await user_repo.create_membership(membership)
    return {"ok": True, "email": body.email, "role": role.value}
