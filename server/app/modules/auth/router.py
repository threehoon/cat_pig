from fastapi import APIRouter

from app.core.envelope import DataEnvelope
from app.modules.auth.deps import AuthServiceDep
from app.modules.auth.schemas import LoginRequest, LoginResult


router = APIRouter()


@router.post("/login")
async def login(
    body: LoginRequest,
    service: AuthServiceDep,
) -> DataEnvelope[LoginResult]:
    return DataEnvelope(data=await service.login(body.code))
