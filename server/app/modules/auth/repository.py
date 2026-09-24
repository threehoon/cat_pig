import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_by_openid(self, openid: str) -> User:
        statement = (
            insert(User)
            .values(id=uuid.uuid4(), openid=openid)
            .on_conflict_do_nothing(constraint="uq_users_openid")
            .returning(User)
        )
        inserted = (await self._session.scalars(statement)).one_or_none()
        if inserted is not None:
            return inserted

        existing = await self._session.scalar(select(User).where(User.openid == openid))
        if existing is None:
            raise RuntimeError("user row missing after openid conflict")
        return existing

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def apply_profile(self, user: User, changes: dict[str, str | None]) -> User:
        if "nickname" in changes:
            user.nickname = changes["nickname"]
        if "avatar_url" in changes:
            user.avatar_url = changes["avatar_url"]
        await self._session.flush()
        return user
