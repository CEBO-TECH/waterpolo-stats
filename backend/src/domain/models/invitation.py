from dataclasses import dataclass, field
from datetime import datetime

from .user import UserRole


@dataclass
class ClubInvitation:
    """Invitation to join a club, for an email that may not have an account yet."""
    id: str
    club_id: str
    email: str
    role: UserRole
    token: str
    status: str = "pending"  # pending | accepted | revoked
    created_at: datetime = field(default_factory=datetime.utcnow)
