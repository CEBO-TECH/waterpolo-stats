from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class YouTubeStream:
    """YouTube stream linked to a match for video timestamp tracking."""
    id: str
    match_id: str  # References Match.match_id
    youtube_url: str
    video_id: str  # Extracted from URL (e.g. "dQw4w9WgXcQ")
    stream_start_time: datetime | None = None  # When the stream/recording started
    created_at: datetime = field(default_factory=datetime.utcnow)
