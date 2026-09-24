from pydantic import BaseModel, ConfigDict


class Me(BaseModel):
    id: str
    nickname: str | None
    avatar_url: str | None
    points_balance: int
    post_count: int
    like_received_count: int
    following_count: int
    follower_count: int


class MePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nickname: str | None = None
    avatar_url: str | None = None
