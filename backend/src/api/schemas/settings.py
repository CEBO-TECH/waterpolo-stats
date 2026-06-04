from pydantic import BaseModel


class SettingsResponse(BaseModel):
    ActiveMatch: str
    Quarter: int


class SetActiveMatchRequest(BaseModel):
    match_id: str


class SetQuarterRequest(BaseModel):
    quarter: int
