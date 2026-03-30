from pydantic import BaseModel
from typing import Literal


class Message(BaseModel):
    role: Literal["user", "ai"]
    content: str


class IngestRequest(BaseModel):
    html: str


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
