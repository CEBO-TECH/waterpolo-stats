from pydantic import BaseModel


class PlayerCreate(BaseModel):
    number: int
    name: str
    team: str = "my"


class PlayerResponse(BaseModel):
    player_id: str
    number: int
    name: str
    team: str


class PlayerDeleteRequest(BaseModel):
    player_id: str


class AgeCategoryUpdate(BaseModel):
    categories: list[str]  # ["U17", "Seniorzy"]
