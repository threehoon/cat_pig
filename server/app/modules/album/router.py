from fastapi import APIRouter

from app.core.envelope import DataEnvelope
from app.core.pagination import PageQueryDep
from app.modules.album.deps import AlbumServiceDep, AlbumUserIdDep
from app.modules.album.schemas import Album, AlbumDeleted, AlbumPage, AlbumWrite


router = APIRouter()


@router.get("")
async def list_albums(
    page: PageQueryDep,
    user_id: AlbumUserIdDep,
    service: AlbumServiceDep,
) -> DataEnvelope[AlbumPage]:
    return DataEnvelope(data=await service.list_albums(user_id, page))


@router.post("")
async def create_album(
    body: AlbumWrite,
    user_id: AlbumUserIdDep,
    service: AlbumServiceDep,
) -> DataEnvelope[Album]:
    return DataEnvelope(data=await service.create_album(user_id, body))


@router.get("/{album_id}")
async def get_album(
    album_id: str,
    user_id: AlbumUserIdDep,
    service: AlbumServiceDep,
) -> DataEnvelope[Album]:
    return DataEnvelope(data=await service.get_album(user_id, album_id))


@router.patch("/{album_id}")
async def patch_album(
    album_id: str,
    body: AlbumWrite,
    user_id: AlbumUserIdDep,
    service: AlbumServiceDep,
) -> DataEnvelope[Album]:
    return DataEnvelope(data=await service.patch_album(user_id, album_id, body))


@router.delete("/{album_id}")
async def delete_album(
    album_id: str,
    user_id: AlbumUserIdDep,
    service: AlbumServiceDep,
) -> DataEnvelope[AlbumDeleted]:
    return DataEnvelope(data=await service.delete_album(user_id, album_id))
