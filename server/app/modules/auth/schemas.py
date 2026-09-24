from pydantic import BaseModel


class LoginRequest(BaseModel):
    code: str


class LoginResult(BaseModel):
    token: str
    expires_in: int


class UserProfile(BaseModel):
    id: str
    nickname: str | None
    avatar_url: str | None
