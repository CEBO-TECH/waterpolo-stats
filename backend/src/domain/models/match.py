from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


@dataclass
class Match:
    id: str
    club_id: str
    match_id: str  # Legacy external ID like "match_timestamp"
    date: str
    opponent: str
    place: str
    age_category: str  # "U17", "U19", "Seniorzy"
    status: MatchStatus = MatchStatus.ACTIVE
    archived: bool = False
    season_id: str | None = None
    # Cumulative quarter scores (score at END of each quarter)
    q1_my: int = 0
    q1_opp: int = 0
    q2_my: int = 0
    q2_opp: int = 0
    q3_my: int = 0
    q3_opp: int = 0
    q4_my: int = 0
    q4_opp: int = 0
    final_my: int = 0
    final_opp: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def per_quarter_scores(self) -> dict:
        """Convert cumulative scores to per-quarter differences for display.

        Scores in DB are cumulative (q2_my = total at end of Q2).
        Display shows per-quarter differences.
        Port of logic from app/api/stats/[matchId]/route.ts:36-54.
        """
        return {
            "1": {"my": self.q1_my, "opp": self.q1_opp},
            "2": {"my": self.q2_my - self.q1_my, "opp": self.q2_opp - self.q1_opp},
            "3": {"my": self.q3_my - self.q2_my, "opp": self.q3_opp - self.q2_opp},
            "4": {"my": self.q4_my - self.q3_my, "opp": self.q4_opp - self.q3_opp},
            "final": {
                "my": self.final_my or self.q4_my,
                "opp": self.final_opp or self.q4_opp,
            },
        }
