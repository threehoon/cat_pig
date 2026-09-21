from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, Field


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)


def get_page_query(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1)] = 20,
) -> PageQuery:
    return PageQuery(page=page, page_size=page_size)


PageQueryDep = Annotated[PageQuery, Depends(get_page_query)]
