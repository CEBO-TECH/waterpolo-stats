from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class SelectClubRequest(BaseModel):
    club_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    clubs: list[dict] = []  # [{club_id, club_name, role}]
