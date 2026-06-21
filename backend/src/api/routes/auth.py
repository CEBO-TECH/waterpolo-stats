"""Auth routes — register, login, refresh, me."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.auth.jwt_adapter import JWTAdapter
from src.adapters.auth.password_adapter import PasswordAdapter
from src.adapters.persistence.database import get_async_session
from src.adapters.persistence.repositories import (
    SQLAlchemyClubInvitationRepository,
    SQLAlchemyClubRepository,
    SQLAlchemyPlayerRepository,
    SQLAlchemyUserRepository,
)
from src.api.deps import CurrentUser
from src.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SelectClubRequest,
    TokenResponse,
    UserResponse,
)
from src.domain.models import ClubMembership, User, UserRole

router = APIRouter(prefix="/v1/auth", tags=["auth"])
jwt = JWTAdapter()
pwd = PasswordAdapter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
):
    user_repo = SQLAlchemyUserRepository(session)
    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=pwd.hash(body.password),
    )
    created = await user_repo.create(user)

    # Auto-join by email — no token link needed. A person joins a club when they
    # register with an email that was invited to it OR attached to a player record
    # in it; that player profile is linked to the new account.
    inv_repo = SQLAlchemyClubInvitationRepository(session)
    player_repo = SQLAlchemyPlayerRepository(session)
    club_repo = SQLAlchemyClubRepository(session)
    joined: dict[str, UserRole] = {}

    async def ensure_membership(club_id: str, role: UserRole) -> None:
        if club_id in joined:
            return
        if not await user_repo.get_membership(created.id, club_id):
            await user_repo.create_membership(ClubMembership(
                id=str(uuid.uuid4()), user_id=created.id, club_id=club_id, role=role,
            ))
        joined[club_id] = role

    async def link_player(club_id: str) -> None:
        player = await player_repo.get_by_email(club_id, created.email)
        if player and not player.user_id:
            await player_repo.update_fields(club_id, player.player_id, {"user_id": created.id})

    for inv in await inv_repo.list_pending_for_email(created.email):
        await ensure_membership(inv.club_id, inv.role)
        await link_player(inv.club_id)
        await inv_repo.update_status(inv.id, "accepted")

    for player in await player_repo.list_by_email_all_clubs(created.email):
        await ensure_membership(player.club_id, UserRole.PLAYER)
        if not player.user_id:
            await player_repo.update_fields(player.club_id, player.player_id, {"user_id": created.id})

    clubs = []
    for club_id, role in joined.items():
        club = await club_repo.get_by_id(club_id)
        clubs.append({
            "club_id": club_id,
            "club_name": club.name if club else "",
            "role": role.value,
        })

    return UserResponse(id=created.id, email=created.email, clubs=clubs)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
):
    user_repo = SQLAlchemyUserRepository(session)
    user = await user_repo.get_by_email(body.email)
    if not user or not pwd.verify(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Get user's club memberships for the first club's token
    memberships = await user_repo.get_memberships(user.id)
    club_id = memberships[0].club_id if memberships else ""
    role = memberships[0].role.value if memberships else ""

    return TokenResponse(
        access_token=jwt.create_access_token(user.id, club_id, role),
        refresh_token=jwt.create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_async_session),
):
    user_id = jwt.decode_refresh_token(body.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_repo = SQLAlchemyUserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    memberships = await user_repo.get_memberships(user.id)
    club_id = memberships[0].club_id if memberships else ""
    role = memberships[0].role.value if memberships else ""

    return TokenResponse(
        access_token=jwt.create_access_token(user.id, club_id, role),
        refresh_token=jwt.create_refresh_token(user.id),
    )


@router.post("/select-club", response_model=TokenResponse)
async def select_club(
    body: SelectClubRequest,
    user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    """Re-issue an access token scoped to the chosen club.

    Used when a user belongs to multiple clubs and picks/switches the active one.
    Verifies the user is actually a member of the requested club.
    """
    user_repo = SQLAlchemyUserRepository(session)
    membership = await user_repo.get_membership(user.id, body.club_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this club",
        )

    return TokenResponse(
        access_token=jwt.create_access_token(
            user.id, membership.club_id, membership.role.value
        ),
        refresh_token=jwt.create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    user_repo = SQLAlchemyUserRepository(session)
    club_repo = SQLAlchemyClubRepository(session)
    memberships = await user_repo.get_memberships(user.id)

    clubs = []
    for m in memberships:
        club = await club_repo.get_by_id(m.club_id)
        clubs.append({
            "club_id": m.club_id,
            "club_name": club.name if club else "",
            "role": m.role.value,
        })

    return UserResponse(id=user.id, email=user.email, clubs=clubs)
