from pydantic import BaseModel


class LoginRequest(BaseModel):
    code: str


class LoginResult(BaseModel):
    token: str
    expires_in: int
