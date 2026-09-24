from typing import Annotated

from fastapi import APIRouter, Query

from app.core.envelope import DataEnvelope
from app.core.pagination import PageQueryDep
from app.modules.points.deps import PointsServiceDep, PointsUserIdDep
from app.modules.points.schemas import CheckinResult, MakeupRequest, MakeupResult, PointsEntryPage, PointsSummary


router = APIRouter()


@router.get("/summary")
async def read_summary(user_id: PointsUserIdDep, service: PointsServiceDep) -> DataEnvelope[PointsSummary]:
    return DataEnvelope(data=await service.summary(user_id))


@router.get("/ledger")
async def read_ledger(
    user_id: PointsUserIdDep,
    service: PointsServiceDep,
    page: PageQueryDep,
    kind: Annotated[str | None, Query()] = None,
    range_key: Annotated[str | None, Query(alias="range")] = None,
) -> DataEnvelope[PointsEntryPage]:
    return DataEnvelope(data=await service.ledger(user_id, page, kind, range_key))


@router.post("/checkin")
async def checkin(user_id: PointsUserIdDep, service: PointsServiceDep) -> DataEnvelope[CheckinResult]:
    return DataEnvelope(data=await service.checkin(user_id))


@router.post("/makeup")
async def makeup(
    body: MakeupRequest,
    user_id: PointsUserIdDep,
    service: PointsServiceDep,
) -> DataEnvelope[MakeupResult]:
    return DataEnvelope(data=await service.makeup(user_id, body.date))
