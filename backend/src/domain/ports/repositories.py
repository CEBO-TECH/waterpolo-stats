from abc import ABC, abstractmethod

from src.domain.models import (
    AgeCategory,
    Club,
    ClubConfig,
    ClubInvitation,
    Substitution,
    ClubMembership,
    ClubSettings,
    Event,
    Match,
    MatchStatus,
    Player,
    PlayerAgeCategory,
    RosterEntry,
    Season,
    User,
    UserRole,
    VoiceNote,
    YouTubeStream,
)


class SubstitutionRepository(ABC):
    @abstractmethod
    async def list_for_match(
        self, club_id: str, match_id: str
    ) -> list[Substitution]: ...

    @abstractmethod
    async def create(self, sub: Substitution) -> Substitution: ...

    @abstractmethod
    async def create_many(self, subs: list[Substitution]) -> list[Substitution]: ...


class VoiceNoteRepository(ABC):
    @abstractmethod
    async def create(self, note: VoiceNote) -> VoiceNote: ...

    @abstractmethod
    async def list_for_match(self, club_id: str, match_id: str) -> list[VoiceNote]: ...

    @abstractmethod
    async def get_by_id(self, club_id: str, note_id: str) -> VoiceNote | None: ...

    @abstractmethod
    async def delete(self, club_id: str, note_id: str) -> None: ...


class ClubInvitationRepository(ABC):
    @abstractmethod
    async def create(self, invitation: ClubInvitation) -> ClubInvitation: ...

    @abstractmethod
    async def list_pending(self, club_id: str) -> list[ClubInvitation]: ...

    @abstractmethod
    async def list_pending_for_email(self, email: str) -> list[ClubInvitation]:
        """All pending invitations for an email across every club (for auto-join on register)."""
        ...

    @abstractmethod
    async def get_by_token(self, token: str) -> ClubInvitation | None: ...

    @abstractmethod
    async def update_status(self, invitation_id: str, status: str) -> None: ...

    @abstractmethod
    async def delete(self, club_id: str, invitation_id: str) -> None: ...


class AgeCategoryRepository(ABC):
    @abstractmethod
    async def list_by_club(self, club_id: str) -> list[AgeCategory]: ...

    @abstractmethod
    async def create(self, category: AgeCategory) -> AgeCategory: ...

    @abstractmethod
    async def update(self, category: AgeCategory) -> AgeCategory | None: ...

    @abstractmethod
    async def delete(self, club_id: str, category_id: str) -> None: ...

    @abstractmethod
    async def seed_defaults(self, club_id: str) -> list[AgeCategory]: ...


class ClubRepository(ABC):
    @abstractmethod
    async def create(self, club: Club) -> Club: ...

    @abstractmethod
    async def get_by_id(self, club_id: str) -> Club | None: ...

    @abstractmethod
    async def list_all(self) -> list[Club]: ...


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get_memberships(self, user_id: str) -> list[ClubMembership]: ...

    @abstractmethod
    async def get_membership(
        self, user_id: str, club_id: str
    ) -> ClubMembership | None: ...

    @abstractmethod
    async def create_membership(self, membership: ClubMembership) -> ClubMembership: ...

    @abstractmethod
    async def list_members(self, club_id: str) -> list[tuple[ClubMembership, str]]: ...

    @abstractmethod
    async def update_membership_role(
        self, user_id: str, club_id: str, role: UserRole
    ) -> ClubMembership | None: ...

    @abstractmethod
    async def delete_membership(self, user_id: str, club_id: str) -> None: ...

    @abstractmethod
    async def count_owners(self, club_id: str) -> int: ...


class PlayerRepository(ABC):
    @abstractmethod
    async def list_by_club(self, club_id: str) -> list[Player]: ...

    @abstractmethod
    async def get_by_player_id(
        self, club_id: str, player_id: str
    ) -> Player | None: ...

    @abstractmethod
    async def get_by_user_id(self, club_id: str, user_id: str) -> Player | None: ...

    @abstractmethod
    async def get_by_email(self, club_id: str, email: str) -> Player | None: ...

    @abstractmethod
    async def list_by_email_all_clubs(self, email: str) -> list[Player]:
        """All player records with this email across every club (for auto-link on register)."""
        ...

    @abstractmethod
    async def create(self, player: Player) -> Player: ...

    @abstractmethod
    async def update_fields(
        self, club_id: str, player_id: str, fields: dict
    ) -> Player | None: ...

    @abstractmethod
    async def delete(self, club_id: str, player_id: str) -> None: ...

    @abstractmethod
    async def exists_with_number(self, club_id: str, number: int) -> bool: ...

    @abstractmethod
    async def get_age_categories(
        self, player_id: str
    ) -> list[PlayerAgeCategory]: ...

    @abstractmethod
    async def get_age_categories_map(self, club_id: str) -> dict[str, list[str]]: ...

    @abstractmethod
    async def set_age_categories(
        self, player_id: str, categories: list[str]
    ) -> list[PlayerAgeCategory]: ...


class MatchRepository(ABC):
    @abstractmethod
    async def list_active(self, club_id: str) -> list[Match]: ...

    @abstractmethod
    async def list_by_season(
        self, club_id: str, season_id: str
    ) -> list[Match]: ...

    @abstractmethod
    async def get_by_match_id(
        self, club_id: str, match_id: str
    ) -> Match | None: ...

    @abstractmethod
    async def upsert(self, match: Match) -> Match: ...

    @abstractmethod
    async def update_status(
        self, club_id: str, match_id: str, status: MatchStatus
    ) -> Match: ...

    @abstractmethod
    async def update_fields(
        self, club_id: str, match_id: str, fields: dict
    ) -> Match: ...

    @abstractmethod
    async def archive(self, club_id: str, match_id: str) -> None: ...

    @abstractmethod
    async def update_scores(
        self, club_id: str, match_id: str, scores: dict
    ) -> Match: ...


class EventRepository(ABC):
    @abstractmethod
    async def create_batch(self, events: list[Event]) -> int: ...

    @abstractmethod
    async def get_recent(
        self, club_id: str, match_id: str, limit: int = 20
    ) -> list[Event]: ...

    @abstractmethod
    async def delete_by_id(self, club_id: str, event_id: str) -> None: ...

    @abstractmethod
    async def delete_last_within_window(
        self, club_id: str, match_id: str, minutes: int = 3
    ) -> bool: ...

    @abstractmethod
    async def get_all_for_match(
        self, club_id: str, match_id: str
    ) -> list[Event]: ...

    @abstractmethod
    async def get_all_for_club(self, club_id: str) -> list[Event]: ...

    @abstractmethod
    async def get_all_for_player(
        self, club_id: str, player_id: str, season_id: str | None = None
    ) -> list[Event]: ...

    @abstractmethod
    async def get_all_for_season(
        self, club_id: str, season_id: str
    ) -> list[Event]: ...


class SettingsRepository(ABC):
    @abstractmethod
    async def get_for_club(self, club_id: str) -> ClubSettings: ...

    @abstractmethod
    async def set_active_match(
        self, club_id: str, match_id: str
    ) -> ClubSettings: ...

    @abstractmethod
    async def set_quarter(
        self, club_id: str, quarter: int
    ) -> ClubSettings: ...

    @abstractmethod
    async def create_default(self, club_id: str) -> ClubSettings: ...


class RosterRepository(ABC):
    @abstractmethod
    async def get_for_match(
        self, club_id: str, match_id: str
    ) -> list[RosterEntry]: ...

    @abstractmethod
    async def replace_for_match(
        self, club_id: str, match_id: str, entries: list[RosterEntry]
    ) -> list[RosterEntry]: ...

    @abstractmethod
    async def get_previous_match_roster(
        self, club_id: str, current_match_id: str
    ) -> list[RosterEntry]: ...

    @abstractmethod
    async def get_counts_for_club(self, club_id: str) -> dict[str, int]: ...

    @abstractmethod
    async def get_match_ids_for_player(
        self, club_id: str, player_id: str
    ) -> list[str]: ...


class SeasonRepository(ABC):
    @abstractmethod
    async def create(self, season: Season) -> Season: ...

    @abstractmethod
    async def list_by_club(self, club_id: str) -> list[Season]: ...

    @abstractmethod
    async def get_active(self, club_id: str) -> Season | None: ...

    @abstractmethod
    async def get_by_id(
        self, club_id: str, season_id: str
    ) -> Season | None: ...

    @abstractmethod
    async def update(self, season: Season) -> Season: ...

    @abstractmethod
    async def delete(self, club_id: str, season_id: str) -> None: ...


class ClubConfigRepository(ABC):
    @abstractmethod
    async def get_for_club(self, club_id: str) -> ClubConfig: ...

    @abstractmethod
    async def update(self, config: ClubConfig) -> ClubConfig: ...

    @abstractmethod
    async def create_default(self, club_id: str) -> ClubConfig: ...


class YouTubeStreamRepository(ABC):
    @abstractmethod
    async def get_for_match(self, match_id: str) -> YouTubeStream | None: ...

    @abstractmethod
    async def create(self, stream: YouTubeStream) -> YouTubeStream: ...

    @abstractmethod
    async def update(self, stream: YouTubeStream) -> YouTubeStream: ...

    @abstractmethod
    async def delete(self, match_id: str) -> None: ...
