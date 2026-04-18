from pydantic import BaseModel
from typing import Literal


class Message(BaseModel):
    role: Literal["user", "ai"]
    content: str


class IngestRequest(BaseModel):
    url: str | None = None
    title: str | None = None
    description: str | None = None
    siteName: str | None = None
    htmlFragment: str | None = None
    html: str | None = None  # fallback from old extension version
    sourceUrl: str | None = None
    timestamp: str | None = None


class IngestResponse(BaseModel):
    status: str
    title: str


class ConversationMeta(BaseModel):
    conversation_id: str
    created_at: str
    updated_at: str
    message_count: int


class ConversationListResponse(BaseModel):
    user_id: str
    conversations: list[ConversationMeta]


class HistoryResponse(BaseModel):
    messages: list[Message]
