from datetime import datetime, timezone

import redis.asyncio as aioredis


class ChatRepository:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    def _key(self, user_id: str, conv_id: str) -> str:
        return f"chat:{user_id}:{conv_id}"

    @staticmethod
    def _derive_title(text: str) -> str:
        """Use the first sentence (roughly) or fallback to first 80 chars."""
        if not text:
            return "Untitled conversation"
        first_sentence = text.split(". ", 1)[0].split("? ", 1)[0].split("! ", 1)[0]
        candidate = first_sentence.strip()
        if not candidate:
            candidate = text.strip()
        return (candidate[:80]).strip() or "Untitled conversation"

    async def get_conversation(self, user_id: str, conv_id: str) -> list[dict]:
        key = self._key(user_id, conv_id)
        try:
            result = await self.redis.json().get(key, "$.messages")
            if result is None:
                return []
            return result[0] if result else []
        except Exception:
            return []

    async def append_messages(
        self, user_id: str, conv_id: str, new_msgs: list[dict]
    ) -> None:
        key = self._key(user_id, conv_id)
        now = datetime.now(timezone.utc).isoformat()

        exists = await self.redis.exists(key)
        if not exists:
            user_msg = next((m for m in new_msgs if m.get("role") == "user"), None)
            title = self._derive_title(user_msg.get("content", "") if user_msg else "")
            doc = {
                "messages": new_msgs,
                "created_at": now,
                "updated_at": now,
                "title": title,
            }
            await self.redis.json().set(key, "$", doc)
        else:
            await self.redis.json().arrappend(key, "$.messages", *new_msgs)
            await self.redis.json().set(key, "$.updated_at", now)
            # If title missing, try to set from first user message in this batch
            title = await self.redis.json().get(key, "$.title")
            if not title or title == [None]:
                user_msg = next((m for m in new_msgs if m.get("role") == "user"), None)
                if user_msg:
                    derived = self._derive_title(user_msg.get("content", ""))
                    await self.redis.json().set(key, "$.title", derived)

    async def replace_messages(
        self, user_id: str, conv_id: str, messages: list[dict]
    ) -> None:
        key = self._key(user_id, conv_id)
        now = datetime.now(timezone.utc).isoformat()
        exists = await self.redis.exists(key)

        if not exists:
            user_msg = next((m for m in messages if m.get("role") == "user"), None)
            title = self._derive_title(user_msg.get("content", "") if user_msg else "")
            doc = {
                "messages": messages,
                "created_at": now,
                "updated_at": now,
                "title": title,
            }
            await self.redis.json().set(key, "$", doc)
            return

        await self.redis.json().set(key, "$.messages", messages)
        await self.redis.json().set(key, "$.updated_at", now)

    async def list_conversations(self, user_id: str) -> list[dict]:
        pattern = f"chat:{user_id}:*"
        keys = [key async for key in self.redis.scan_iter(match=pattern)]

        results = []
        for key in keys:
            parts = key.split(":", 2)
            if len(parts) == 3:
                conv_id = parts[2]
                meta = await self.get_conversation_metadata(user_id, conv_id)
                if meta:
                    results.append(meta)
        return results

    async def delete_conversation(self, user_id: str, conv_id: str) -> bool:
        key = self._key(user_id, conv_id)
        deleted = await self.redis.delete(key)
        return deleted > 0

    async def get_conversation_metadata(
        self, user_id: str, conv_id: str
    ) -> dict | None:
        key = self._key(user_id, conv_id)
        try:
            result = await self.redis.json().get(key, "$")
            if not result:
                return None
            doc = result[0]
            return {
                "conversation_id": conv_id,
                "created_at": doc.get("created_at", ""),
                "updated_at": doc.get("updated_at", ""),
                "message_count": len(doc.get("messages", [])),
                "title": doc.get("title") or "Untitled conversation",
            }
        except Exception:
            return None

    async def update_title(self, user_id: str, conv_id: str, title: str) -> bool:
        key = self._key(user_id, conv_id)
        clean = title.strip() or "Untitled conversation"
        exists = await self.redis.exists(key)
        now = datetime.now(timezone.utc).isoformat()

        if not exists:
            # Create a minimal conversation doc so the title can be persisted
            doc = {
                "messages": [],
                "created_at": now,
                "updated_at": now,
                "title": clean,
            }
            await self.redis.json().set(key, "$", doc)
            return True

        await self.redis.json().set(key, "$.title", clean)
        await self.redis.json().set(key, "$.updated_at", now)
        return True
