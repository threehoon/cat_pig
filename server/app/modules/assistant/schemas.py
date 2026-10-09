import uuid
from typing import Literal

from pydantic import BaseModel


class AssistantSuggestion(BaseModel):
    id: str
    question: str


class SuggestionPage(BaseModel):
    items: list[AssistantSuggestion]
    total: int
    page: int
    page_size: int


class AskRequest(BaseModel):
    question: str
    conversation_id: uuid.UUID | None = None


class AssistantCitation(BaseModel):
    id: str
    title: str
    snippet: str


class RelatedPost(BaseModel):
    id: str
    title: str
    body: str
    cover_url: str | None = None


class AssistantAsk(BaseModel):
    conversation_id: str
    answer: str
    source: Literal["knowledge", "search", "generated"]
    citations: list[AssistantCitation]
    related_posts: list[RelatedPost]


class AssistantConversation(BaseModel):
    id: str
    title: str
    updated_at: str


class ConversationPage(BaseModel):
    items: list[AssistantConversation]
    total: int
    page: int
    page_size: int


class AssistantMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    text: str
    source: Literal["knowledge", "search", "generated"] | None
    citations: list[AssistantCitation]


class MessagePage(BaseModel):
    items: list[AssistantMessage]
    total: int
    page: int
    page_size: int
