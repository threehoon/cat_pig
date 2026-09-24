import uuid
from typing import Annotated, Any

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.album.repository import AlbumRepository
from app.modules.album.service import AlbumService


class _MissingCommunity:
    """Stand-in when community.deps is not importable yet."""


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


def get_album_repository(session: SessionDep) -> AlbumRepository:
    return AlbumRepository(session)


def _missing_community() -> _MissingCommunity:
    return _MissingCommunity()


def _community_dependency() -> Any:
    # Album routes still load when the community slice has not landed.
    # publish_album_show then raises inside the savepoint.
    try:
        from app.modules.community.deps import CommunityServiceDep
    except ModuleNotFoundError as exc:
        if exc.name not in {"app.modules.community", "app.modules.community.deps"}:
            raise
        return Annotated[_MissingCommunity, Depends(_missing_community)]
    except ImportError as exc:
        if "CommunityServiceDep" not in str(exc):
            raise
        return Annotated[_MissingCommunity, Depends(_missing_community)]
    return CommunityServiceDep


_CommunityDep = _community_dependency()


def get_album_service(
    repository: Annotated[AlbumRepository, Depends(get_album_repository)],
    community: _CommunityDep,
) -> AlbumService:
    return AlbumService(repository, community)


AlbumUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
AlbumServiceDep = Annotated[AlbumService, Depends(get_album_service)]
