from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RosterEntry:
    id: str
    club_id: str
    match_id: str  # References Match.match_id
    player_id: str  # References Player.player_id
    number: int
    name: str
    team: str = "my"
    created_at: datetime = field(default_factory=datetime.utcnow)
