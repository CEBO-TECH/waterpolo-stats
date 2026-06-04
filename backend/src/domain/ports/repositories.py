from abc import ABC, abstractmethod

from src.domain.models import (
    Club,
    ClubConfig,
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
    YouTubeStream,
)


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


class PlayerRepository(ABC):
    @abstractmethod
    async def list_by_club(self, club_id: str) -> list[Player]: ...

    @abstractmethod
    async def get_by_player_id(
        self, club_id: str, player_id: str
    ) -> Player | None: ...

    @abstractmethod
    async def create(self, player: Player) -> Player: ...

    @abstractmethod
    async def delete(self, club_id: str, player_id: str) -> None: ...

    @abstractmethod
    async def exists_with_number(self, club_id: str, number: int) -> bool: ...

    @abstractmethod
    async def get_age_categories(
        self, player_id: str
    ) -> list[PlayerAgeCategory]: ...

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
