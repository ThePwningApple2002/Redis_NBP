from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.repository.chat_repository import ChatRepository

router = APIRouter(prefix="/conversations", tags=["conversations"])


class TitleUpdate(BaseModel):
    title: str


@router.get("/{user_id}")
async def list_conversations(user_id: str, request: Request):
    chat_repo = ChatRepository(request.app.state.redis)
    conversations = await chat_repo.list_conversations(user_id)
    return {"user_id": user_id, "conversations": conversations}


@router.delete("/{user_id}/{conversation_id}")
async def delete_conversation(
    user_id: str, conversation_id: str, request: Request
):
    chat_repo = ChatRepository(request.app.state.redis)
    deleted = await chat_repo.delete_conversation(user_id, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


@router.patch("/{user_id}/{conversation_id}/title")
async def update_conversation_title(
    user_id: str, conversation_id: str, payload: TitleUpdate, request: Request
):
    chat_repo = ChatRepository(request.app.state.redis)
    await chat_repo.update_title(user_id, conversation_id, payload.title)
    return {"status": "updated", "conversation_id": conversation_id, "title": payload.title}
