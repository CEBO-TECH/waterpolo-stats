"""FastAPI dependency injection — session, auth, club scoping."""

from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.auth.jwt_adapter import JWTAdapter, TokenPayload
from src.adapters.persistence.database import get_async_session
from src.adapters.persistence.repositories import (
    SQLAlchemyAgeCategoryRepository,
    SQLAlchemyClubConfigRepository,
    SQLAlchemyClubInvitationRepository,
    SQLAlchemyClubRepository,
    SQLAlchemyEventRepository,
    SQLAlchemyMatchRepository,
    SQLAlchemyPlayerRepository,
    SQLAlchemyRosterRepository,
    SQLAlchemySeasonRepository,
    SQLAlchemySettingsRepository,
    SQLAlchemySubstitutionRepository,
    SQLAlchemyUserRepository,
    SQLAlchemyVoiceNoteRepository,
    SQLAlchemyYouTubeStreamRepository,
)
from src.domain.models import ClubMembership, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)
jwt_adapter = JWTAdapter()

# Type aliases
DBSession = Annotated[AsyncSession, Depends(get_async_session)]
Token = Annotated[str | None, Depends(oauth2_scheme)]


async def get_current_user(
    session: DBSession, token: Token
) -> User:
    """Decode JWT and return the authenticated user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = jwt_adapter.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_repo = SQLAlchemyUserRepository(session)
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_club_context(
    session: DBSession,
    user: CurrentUser,
    club_id: str = Path(..., description="Club ID"),
) -> tuple[User, ClubMembership]:
    """Verify user has membership in the club. Returns (user, membership)."""
    user_repo = SQLAlchemyUserRepository(session)
    membership = await user_repo.get_membership(user.id, club_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this club",
        )
    return user, membership


ClubContext = Annotated[tuple[User, ClubMembership], Depends(get_club_context)]


def require_role(*roles: UserRole):
    """Dependency factory — require the user's club role to be one of `roles`."""
    async def _check(ctx: ClubContext) -> tuple[User, ClubMembership]:
        user, membership = ctx
        if membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return user, membership
    return _check


# Convenience role dependencies
CoachOrOwner = Annotated[
    tuple[User, ClubMembership],
    Depends(require_role(UserRole.OWNER, UserRole.COACH)),
]
OwnerOnly = Annotated[
    tuple[User, ClubMembership],
    Depends(require_role(UserRole.OWNER)),
]
AnyMember = Annotated[
    tuple[User, ClubMembership],
    Depends(require_role(UserRole.OWNER, UserRole.COACH, UserRole.PLAYER)),
]


# Repository factories
def get_player_repo(session: DBSession) -> SQLAlchemyPlayerRepository:
    return SQLAlchemyPlayerRepository(session)

def get_match_repo(session: DBSession) -> SQLAlchemyMatchRepository:
    return SQLAlchemyMatchRepository(session)

def get_event_repo(session: DBSession) -> SQLAlchemyEventRepository:
    return SQLAlchemyEventRepository(session)

def get_settings_repo(session: DBSession) -> SQLAlchemySettingsRepository:
    return SQLAlchemySettingsRepository(session)

def get_roster_repo(session: DBSession) -> SQLAlchemyRosterRepository:
    return SQLAlchemyRosterRepository(session)

def get_club_repo(session: DBSession) -> SQLAlchemyClubRepository:
    return SQLAlchemyClubRepository(session)

def get_user_repo(session: DBSession) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)

def get_season_repo(session: DBSession) -> SQLAlchemySeasonRepository:
    return SQLAlchemySeasonRepository(session)

def get_config_repo(session: DBSession) -> SQLAlchemyClubConfigRepository:
    return SQLAlchemyClubConfigRepository(session)

def get_youtube_repo(session: DBSession) -> SQLAlchemyYouTubeStreamRepository:
    return SQLAlchemyYouTubeStreamRepository(session)

def get_age_category_repo(session: DBSession) -> SQLAlchemyAgeCategoryRepository:
    return SQLAlchemyAgeCategoryRepository(session)

def get_substitution_repo(session: DBSession) -> SQLAlchemySubstitutionRepository:
    return SQLAlchemySubstitutionRepository(session)

def get_invitation_repo(session: DBSession) -> SQLAlchemyClubInvitationRepository:
    return SQLAlchemyClubInvitationRepository(session)

def get_voice_note_repo(session: DBSession) -> SQLAlchemyVoiceNoteRepository:
    return SQLAlchemyVoiceNoteRepository(session)


PlayerRepo = Annotated[SQLAlchemyPlayerRepository, Depends(get_player_repo)]
MatchRepo = Annotated[SQLAlchemyMatchRepository, Depends(get_match_repo)]
EventRepo = Annotated[SQLAlchemyEventRepository, Depends(get_event_repo)]
SettingsRepo = Annotated[SQLAlchemySettingsRepository, Depends(get_settings_repo)]
RosterRepo = Annotated[SQLAlchemyRosterRepository, Depends(get_roster_repo)]
ClubRepo = Annotated[SQLAlchemyClubRepository, Depends(get_club_repo)]
UserRepo = Annotated[SQLAlchemyUserRepository, Depends(get_user_repo)]
SeasonRepo = Annotated[SQLAlchemySeasonRepository, Depends(get_season_repo)]
ConfigRepo = Annotated[SQLAlchemyClubConfigRepository, Depends(get_config_repo)]
YouTubeRepo = Annotated[SQLAlchemyYouTubeStreamRepository, Depends(get_youtube_repo)]
AgeCategoryRepo = Annotated[SQLAlchemyAgeCategoryRepository, Depends(get_age_category_repo)]
SubstitutionRepo = Annotated[SQLAlchemySubstitutionRepository, Depends(get_substitution_repo)]
InvitationRepo = Annotated[SQLAlchemyClubInvitationRepository, Depends(get_invitation_repo)]
VoiceNoteRepo = Annotated[SQLAlchemyVoiceNoteRepository, Depends(get_voice_note_repo)]
