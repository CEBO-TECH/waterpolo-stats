from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ClubType(str, Enum):
    REGULAR = "regular"
    NATIONAL_TEAM = "national_team"


@dataclass
class Club:
    id: str
    name: str
    club_type: ClubType = ClubType.REGULAR
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
