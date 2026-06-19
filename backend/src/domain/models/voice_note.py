from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VoiceNote:
    """A short audio note attached to a match (optionally to a player)."""
    id: str
    club_id: str
    match_id: str
    audio_key: str  # object-storage key
    content_type: str = "audio/webm"
    duration_s: int = 0
    player_id: str | None = None
    note: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
