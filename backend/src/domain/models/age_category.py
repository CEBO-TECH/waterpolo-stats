from dataclasses import dataclass, field
from datetime import datetime


# Default age categories seeded for every new club.
DEFAULT_AGE_CATEGORIES: list[str] = ["Seniorzy", "U19", "U17", "U15"]


@dataclass
class AgeCategory:
    """Per-club age category dictionary entry (e.g. 'U17', 'Seniorzy')."""
    id: str
    club_id: str
    name: str
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
