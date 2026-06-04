from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Player:
    id: str
    club_id: str
    player_id: str  # Legacy external ID like "player_1697..."
    number: int
    name: str
    team: str = "my"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlayerAgeCategory:
    """Junction: one player can belong to multiple age categories."""
    id: str
    player_id: str
    age_category: str  # "U15", "U17", "U19", "Seniorzy"
