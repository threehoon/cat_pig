import uuid
from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.assistant.embeddings import get_embedder
from app.modules.assistant.repository import ConversationRepository, KnowledgeRepository
from app.modules.assistant.service import AssistantService


def get_knowledge_repository(session: SessionDep) -> KnowledgeRepository:
    return KnowledgeRepository(session)


def get_conversation_repository(session: SessionDep) -> ConversationRepository:
    return ConversationRepository(session)


def get_assistant_service(
    knowledge: Annotated[KnowledgeRepository, Depends(get_knowledge_repository)],
    conversations: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> AssistantService:
    return AssistantService(knowledge, conversations, get_embedder())


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


AssistantServiceDep = Annotated[AssistantService, Depends(get_assistant_service)]
AssistantUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
