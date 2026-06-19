"""Auth routes — register, login, refresh, me."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.auth.jwt_adapter import JWTAdapter
from src.adapters.auth.password_adapter import PasswordAdapter
from src.adapters.persistence.database import get_async_session
from src.adapters.persistence.repositories import SQLAlchemyClubRepository, SQLAlchemyUserRepository
from src.api.deps import CurrentUser
from src.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SelectClubRequest,
    TokenResponse,
    UserResponse,
)
from src.domain.models import User

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
    return UserResponse(id=created.id, email=created.email, clubs=[])


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
