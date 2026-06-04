from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Season:
    id: str
    club_id: str
    name: str  # e.g. "2026/2027"
    start_date: date
    end_date: date
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
