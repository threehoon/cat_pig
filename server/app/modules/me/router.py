from fastapi import APIRouter

from app.core.envelope import DataEnvelope
from app.modules.me.deps import MeServiceDep, MeUserIdDep
from app.modules.me.schemas import Me, MePatch


router = APIRouter()


@router.get("")
async def read_me(user_id: MeUserIdDep, service: MeServiceDep) -> DataEnvelope[Me]:
    return DataEnvelope(data=await service.get_me(user_id))


@router.patch("")
async def update_me(
    body: MePatch,
    user_id: MeUserIdDep,
    service: MeServiceDep,
) -> DataEnvelope[Me]:
    return DataEnvelope(data=await service.patch_me(user_id, body))
