from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool = True


class OkCountResponse(BaseModel):
    ok: bool = True
    count: int


class ErrorResponse(BaseModel):
    error: str
