"""Club management routes — clubs, members, invitations."""

import secrets
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from src.api.deps import (
    AgeCategoryRepo,
    ClubRepo,
    CoachOrOwner,
    ConfigRepo,
    CurrentUser,
    InvitationRepo,
    OwnerOnly,
    PlayerRepo,
    SettingsRepo,
    UserRepo,
)
from src.domain.models import Club, ClubInvitation, ClubMembership, UserRole

router = APIRouter(prefix="/v1/clubs", tags=["clubs"])
invitations_router = APIRouter(prefix="/v1/invitations", tags=["invitations"])


class ClubCreateRequest(BaseModel):
    name: str


class ClubResponse(BaseModel):
    id: str
    name: str
    club_type: str


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "player"  # "coach" or "player"


class RoleUpdate(BaseModel):
    role: str


def _role(value: str) -> UserRole:
    return UserRole(value) if value in ("owner", "coach", "player") else UserRole.PLAYER


@router.post("", response_model=ClubResponse, status_code=201)
async def create_club(
    body: ClubCreateRequest,
    user: CurrentUser,
    club_repo: ClubRepo,
    user_repo: UserRepo,
    settings_repo: SettingsRepo,
    config_repo: ConfigRepo,
    age_category_repo: AgeCategoryRepo,
):
    """Create a new club. The authenticated user becomes the owner."""
    club = Club(id=str(uuid.uuid4()), name=body.name)
    created = await club_repo.create(club)

    await user_repo.create_membership(ClubMembership(
        id=str(uuid.uuid4()), user_id=user.id, club_id=created.id, role=UserRole.OWNER,
    ))
    await settings_repo.create_default(created.id)
    await config_repo.create_default(created.id)
    await age_category_repo.seed_defaults(created.id)

    return ClubResponse(id=created.id, name=created.name, club_type=created.club_type.value)


# ─── Members ───

@router.get("/{club_id}/members")
async def list_members(club_id: str, ctx: CoachOrOwner, user_repo: UserRepo):
    members = await user_repo.list_members(club_id)
    return [
        {"user_id": mm.user_id, "email": email, "role": mm.role.value}
        for mm, email in members
    ]


@router.patch("/{club_id}/members/{user_id}")
async def update_member_role(
    club_id: str, user_id: str, body: RoleUpdate, ctx: OwnerOnly, user_repo: UserRepo,
):
    if body.role not in ("owner", "coach", "player"):
        raise HTTPException(status_code=400, detail="Invalid role")
    membership = await user_repo.get_membership(user_id, club_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
    if membership.role == UserRole.OWNER and body.role != "owner":
        if await user_repo.count_owners(club_id) <= 1:
            raise HTTPException(status_code=400, detail="Nie można odebrać roli ostatniemu właścicielowi")
    updated = await user_repo.update_membership_role(user_id, club_id, UserRole(body.role))
    return {"user_id": user_id, "role": updated.role.value}


@router.delete("/{club_id}/members/{user_id}")
async def remove_member(club_id: str, user_id: str, ctx: OwnerOnly, user_repo: UserRepo):
    membership = await user_repo.get_membership(user_id, club_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")
    if membership.role == UserRole.OWNER and await user_repo.count_owners(club_id) <= 1:
        raise HTTPException(status_code=400, detail="Nie można usunąć ostatniego właściciela")
    await user_repo.delete_membership(user_id, club_id)
    return {"ok": True}


# ─── Invitations ───

@router.post("/{club_id}/invite", status_code=201)
async def invite_user(
    club_id: str, body: InviteRequest, ctx: OwnerOnly,
    user_repo: UserRepo, invitation_repo: InvitationRepo,
):
    """Invite by email. Existing account → added immediately; otherwise an invitation
    (with a shareable token) is created. Owner only."""
    role = _role(body.role)
    target = await user_repo.get_by_email(body.email)
    if target:
        if await user_repo.get_membership(target.id, club_id):
            raise HTTPException(status_code=400, detail="User already a member")
        await user_repo.create_membership(ClubMembership(
            id=str(uuid.uuid4()), user_id=target.id, club_id=club_id, role=role,
        ))
        return {"ok": True, "added": True, "email": body.email, "role": role.value}

    inv = await invitation_repo.create(ClubInvitation(
        id=str(uuid.uuid4()), club_id=club_id, email=body.email, role=role,
        token=secrets.token_urlsafe(16),
    ))
    return {
        "ok": True, "added": False,
        "invitation": {"id": inv.id, "email": inv.email, "role": inv.role.value, "token": inv.token},
    }


@router.get("/{club_id}/invitations")
async def list_invitations(club_id: str, ctx: OwnerOnly, invitation_repo: InvitationRepo):
    invs = await invitation_repo.list_pending(club_id)
    return [
        {"id": i.id, "email": i.email, "role": i.role.value, "token": i.token}
        for i in invs
    ]


@router.delete("/{club_id}/invitations/{invitation_id}")
async def revoke_invitation(
    club_id: str, invitation_id: str, ctx: OwnerOnly, invitation_repo: InvitationRepo,
):
    await invitation_repo.delete(club_id, invitation_id)
    return {"ok": True}


@invitations_router.post("/{token}/accept")
async def accept_invitation(
    token: str, user: CurrentUser,
    user_repo: UserRepo, invitation_repo: InvitationRepo, player_repo: PlayerRepo,
):
    """Authenticated user accepts an invitation addressed to their email.

    If a player record in that club has the same email, it is linked to the account
    so the player can see their own matches/stats.
    """
    inv = await invitation_repo.get_by_token(token)
    if not inv or inv.status != "pending":
        raise HTTPException(status_code=404, detail="Invitation not found")
    if inv.email.lower() != user.email.lower():
        raise HTTPException(status_code=403, detail="Zaproszenie wystawione na inny email")
    if not await user_repo.get_membership(user.id, inv.club_id):
        await user_repo.create_membership(ClubMembership(
            id=str(uuid.uuid4()), user_id=user.id, club_id=inv.club_id, role=inv.role,
        ))
    # Auto-link a matching player record to this account.
    player = await player_repo.get_by_email(inv.club_id, inv.email)
    if player and not player.user_id:
        await player_repo.update_fields(inv.club_id, player.player_id, {"user_id": user.id})

    await invitation_repo.update_status(inv.id, "accepted")
    return {"ok": True, "club_id": inv.club_id}
