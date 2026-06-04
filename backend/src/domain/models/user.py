from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"
    COACH = "coach"
    PLAYER = "player"


@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ClubMembership:
    id: str
    user_id: str
    club_id: str
    role: UserRole
    created_at: datetime = field(default_factory=datetime.utcnow)
