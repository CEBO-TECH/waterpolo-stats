from pydantic import BaseModel


class PlayerCreate(BaseModel):
    # Jersey number is assigned per match in the roster, not at player creation,
    # so it is optional here (defaults to 0 = "unassigned").
    number: int | None = None
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
