from typing import Generic, TypeVar

from pydantic import BaseModel


DataT = TypeVar("DataT")


class DataEnvelope(BaseModel, Generic[DataT]):
    data: DataT


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody
