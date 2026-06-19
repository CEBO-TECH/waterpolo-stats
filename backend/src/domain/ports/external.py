from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


# --- Object storage port (voice notes audio) ---


class StoragePort(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def get_bytes(self, key: str) -> bytes | None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


# --- YouTube Port ---


@dataclass
class VideoInfo:
    video_id: str
    title: str
    duration_seconds: int | None = None


class YouTubePort(ABC):
    @abstractmethod
    def extract_video_id(self, url: str) -> str | None:
        """Extract YouTube video ID from various URL formats."""
        ...

    @abstractmethod
    async def get_video_info(self, url: str) -> VideoInfo | None:
        """Fetch video metadata from YouTube API. Returns None if API key not set."""
        ...

    @abstractmethod
    def calculate_video_timestamp(
        self, stream_start: datetime, event_time: datetime, rewind_seconds: int = 30
    ) -> int:
        """Calculate video seek position in seconds.

        Returns the number of seconds from the start of the video to seek to,
        rewound by `rewind_seconds` to show the full action (max action = 28s).
        """
        ...


# --- AI Analysis Port (Faza 3 stub) ---


@dataclass
class Suggestion:
    message: str
    severity: str = "info"  # "info", "warning", "critical"
    category: str = ""  # "offense", "defense", "fatigue", etc.


@dataclass
class MatchAnalysis:
    summary: str
    key_insights: list[str]
    suggestions: list[Suggestion]


@dataclass
class MatchReport:
    title: str
    summary: str
    sections: list[dict]  # [{title, content, stats}]


class AIAnalysisPort(ABC):
    @abstractmethod
    async def analyze_match(
        self, events: list, roster: list, match: object
    ) -> MatchAnalysis:
        """Analyze current match state and return insights."""
        ...

    @abstractmethod
    async def suggest_tactics(
        self, events: list, historical_data: list
    ) -> list[Suggestion]:
        """Generate tactical suggestions based on match data."""
        ...

    @abstractmethod
    async def generate_match_report(
        self, events: list, roster: list, match: object
    ) -> MatchReport:
        """Generate a post-match report."""
        ...
