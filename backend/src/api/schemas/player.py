from pydantic import BaseModel


class PlayerCreate(BaseModel):
    number: int
    name: str
    team: str = "my"
    birth_year: int | None = None
    email: str | None = None


class PlayerUpdate(BaseModel):
    number: int | None = None
    name: str | None = None
    team: str | None = None
    birth_year: int | None = None
    email: str | None = None


class PlayerResponse(BaseModel):
    player_id: str
    number: int
    name: str
    team: str
    birth_year: int | None = None
    email: str | None = None
    has_account: bool = False
    age_categories: list[str] = []


class PlayerDeleteRequest(BaseModel):
    player_id: str


class AgeCategoryUpdate(BaseModel):
    categories: list[str]  # ["U17", "Seniorzy"]
