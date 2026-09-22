from fastapi import APIRouter

from app.core.envelope import DataEnvelope
from app.core.pagination import PageQueryDep
from app.modules.assistant.deps import AssistantServiceDep, AssistantUserIdDep
from app.modules.assistant.schemas import AskRequest, AssistantAsk, SuggestionPage


router = APIRouter()


@router.get("/suggestion")
def list_suggestions(
    page: PageQueryDep,
    service: AssistantServiceDep,
    _user_id: AssistantUserIdDep,
) -> DataEnvelope[SuggestionPage]:
    return DataEnvelope(data=service.list_suggestions(page))


@router.post("/ask")
async def ask(
    body: AskRequest,
    service: AssistantServiceDep,
    user_id: AssistantUserIdDep,
) -> DataEnvelope[AssistantAsk]:
    return DataEnvelope(data=await service.ask(user_id, body.question, body.conversation_id))
