from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Substitution:
    """A single player entering ('in') or leaving ('out') the water."""
    id: str
    club_id: str
    match_id: str  # References Match.match_id
    player_id: str  # References Player.player_id
    direction: str  # "in" | "out"
    quarter: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
