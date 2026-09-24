from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PageQuery


async def page_scalars(session: AsyncSession, statement, page: PageQuery):
    total = await session.scalar(select(func.count()).select_from(statement.subquery()))
    offset = (page.page - 1) * page.page_size
    rows = await session.scalars(statement.offset(offset).limit(page.page_size))
    return list(rows.all()), int(total or 0)
