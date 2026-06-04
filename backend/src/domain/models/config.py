from dataclasses import dataclass, field
from datetime import datetime


# All available stat modules that can be toggled per club
AVAILABLE_MODULES: list[str] = [
    "attack_positional",
    "attack_man_up",
    "penalties",
    "defense_positional",
    "defense_man_up",
]


@dataclass
class ClubConfig:
    """Per-club UI configuration. Controls which stat modules are visible."""
    id: str
    club_id: str
    active_modules: list[str] = field(default_factory=lambda: list(AVAILABLE_MODULES))
    button_layout: dict = field(default_factory=dict)  # Custom button ordering
    updated_at: datetime = field(default_factory=datetime.utcnow)
