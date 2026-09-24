from pydantic import BaseModel


class Media(BaseModel):
    url: str
    width: int
    height: int
    mime: str
