from pydantic import BaseModel


class VoiceParseRequest(BaseModel):
    transcript: str
    match_id: str | None = None


class VoiceParseResponse(BaseModel):
    matched: bool
    transcript: str
    # populated when matched:
    player_id: str | None = None
    player_name: str | None = None
    number: int | None = None
    flag: str | None = None
    label: str | None = None
    confidence: float = 0.0
    source: str = ""  # "deterministic" | "claude"
    # populated when not matched:
    reason: str | None = None
