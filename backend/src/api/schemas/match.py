from pydantic import BaseModel


class MatchCreate(BaseModel):
    match_id: str | None = None
    date: str = ""
    opponent: str = ""
    place: str = ""
    age_category: str = "Seniorzy"


class MatchWithRosterCreate(BaseModel):
    match: MatchCreate
    roster: list[dict] = []  # [{player_id, number, name, team}]


class MatchResponse(BaseModel):
    match_id: str
    date: str
    opponent: str
    place: str
    age_category: str = "Seniorzy"
    status: str
    roster_count: int = 0


class RosterReplaceRequest(BaseModel):
    roster: list[dict] = []  # [{player_id, number, name, team}]


class MatchEditRequest(BaseModel):
    date: str | None = None
    opponent: str | None = None
    place: str | None = None
    age_category: str | None = None


class ScoreUpdateRequest(BaseModel):
    quarter: str  # "1", "2", "3", "4", "final"
    my_score: int
    opp_score: int
