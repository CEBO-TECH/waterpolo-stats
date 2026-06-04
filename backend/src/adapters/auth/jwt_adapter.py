"""JWT token creation and verification."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from jose import JWTError, jwt

from src.config import settings


ALGORITHM = "HS256"


@dataclass
class TokenPayload:
    user_id: str
    club_id: str
    role: str
    exp: datetime


class JWTAdapter:
    def create_access_token(
        self, user_id: str, club_id: str, role: str
    ) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "club_id": club_id,
            "role": role,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> TokenPayload | None:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return TokenPayload(
                user_id=payload.get("sub", ""),
                club_id=payload.get("club_id", ""),
                role=payload.get("role", ""),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
            )
        except JWTError:
            return None

    def decode_refresh_token(self, token: str) -> str | None:
        """Decode refresh token, return user_id or None."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            return payload.get("sub")
        except JWTError:
            return None
