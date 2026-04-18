from datetime import datetime, timezone

import redis.asyncio as aioredis


class ChatRepository:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    def _key(self, user_id: str, conv_id: str) -> str:
        return f"chat:{user_id}:{conv_id}"

    async def get_conversation(self, user_id: str, conv_id: str) -> list[dict]:
        key = self._key(user_id, conv_id)
        try:
            result = await self.redis.json().get(key, "$.messages")
            # JSONPath returns a list wrapping the matched value; None if key missing
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
            doc = {
                "messages": new_msgs,
                "created_at": now,
                "updated_at": now,
            }
            await self.redis.json().set(key, "$", doc)
        else:
            await self.redis.json().arrappend(key, "$.messages", *new_msgs)
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
            }
        except Exception:
            return None
