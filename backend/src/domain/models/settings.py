from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ClubSettings:
    """Per-club settings. Replaces the singleton Settings(id=1) from the monolith."""
    id: str
    club_id: str
    active_match: str = ""  # match_id of the currently active match
    quarter: int = 1  # Current quarter (1-4)
    editor_pin: str = ""  # Legacy PIN for backward compat
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
