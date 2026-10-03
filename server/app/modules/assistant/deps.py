import uuid
from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.assistant.completion import Completer, StaticCompleter, UnavailableCompleter
from app.modules.assistant.embeddings import get_embedder
from app.modules.assistant.llm_config import LlmConfig, get_llm_config
from app.modules.assistant.providers.openai_chat import OpenAIChatCompleter
from app.modules.assistant.providers.xai import XaiCompleter
from app.modules.assistant.repository import ConversationRepository, KnowledgeRepository
from app.modules.assistant.service import GENERATED_ANSWER, AssistantService


def get_knowledge_repository(session: SessionDep) -> KnowledgeRepository:
    return KnowledgeRepository(session)


def get_conversation_repository(session: SessionDep) -> ConversationRepository:
    return ConversationRepository(session)


def get_completer() -> Completer:
    config = get_llm_config()
    provider = config.assistant_llm.strip().lower()
    if provider in ("", "off"):
        return StaticCompleter(GENERATED_ANSWER)
    if provider == "xai":
        return _xai_completer(config)
    if provider == "openai":
        return _openai_completer(config)
    return UnavailableCompleter("unknown", "未知提供方")


def _xai_completer(config: LlmConfig) -> Completer:
    key = config.xai_api_key.get_secret_value().strip()
    base = config.xai_base_url.strip()
    model = config.xai_model.strip()
    if not key:
        return UnavailableCompleter("xai", "缺少密钥")
    if not base:
        return UnavailableCompleter("xai", "缺少地址")
    if not model:
        return UnavailableCompleter("xai", "缺少模型")
    return XaiCompleter(key, base, model)


def _openai_completer(config: LlmConfig) -> Completer:
    key = config.openai_api_key.get_secret_value().strip()
    base = config.openai_base_url.strip()
    model = config.openai_model.strip()
    if not key:
        return UnavailableCompleter("openai", "缺少密钥")
    if not base:
        return UnavailableCompleter("openai", "缺少地址")
    if not model:
        return UnavailableCompleter("openai", "缺少模型")
    return OpenAIChatCompleter(key, base, model)


def get_assistant_service(
    knowledge: Annotated[KnowledgeRepository, Depends(get_knowledge_repository)],
    conversations: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> AssistantService:
    return AssistantService(
        knowledge,
        conversations,
        get_embedder(),
        get_completer(),
    )


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


AssistantServiceDep = Annotated[AssistantService, Depends(get_assistant_service)]
AssistantUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
