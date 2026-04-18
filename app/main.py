from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.graph.builder import build_graph
from app.routers import chat, conversations, recipes


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    build_graph()
    yield
    await app.state.redis.aclose()


app = FastAPI(title="Food Recipe RAG Chat", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(recipes.router)


@app.get("/")
async def health_check():
    return {"status": "ok"}


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    # Inject WebSocket endpoint documentation (OpenAPI 3.x has no native WS spec;
    # we document it as a GET with 101 response so it appears in Swagger)
    schema["paths"]["/ws/chat/{user_id}/{conversation_id}"] = {
        "get": {
            "tags": ["chat"],
            "summary": "Chat (WebSocket)",
            "description": (
                "Real-time streaming chat via WebSocket.\n\n"
                "**Connect:** `ws://<host>/ws/chat/{user_id}/{conversation_id}`\n\n"
                "**Client → Server** (send JSON each turn):\n"
                "```json\n{\"message\": \"How do I make carbonara?\"}\n```\n\n"
                "**Server → Client** (streaming tokens):\n"
                "```json\n"
                "{\"type\": \"token\", \"content\": \"Here\"}\n"
                "{\"type\": \"token\", \"content\": \" is\"}\n"
                "...\n```\n\n"
                "**Server → Client** (completion):\n"
                "```json\n{\"type\": \"end\", \"content\": \"<full response>\"}\n```\n\n"
                "**Server → Client** (error):\n"
                "```json\n{\"type\": \"error\", \"content\": \"<message>\"}\n```\n\n"
                "---\n"
                "\u27a1️ **[Open interactive playground](/ws-playground)** to test this endpoint live."
            ),
            "parameters": [
                {
                    "name": "user_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "example": "user1"},
                },
                {
                    "name": "conversation_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "example": "conv1"},
                },
            ],
            "responses": {
                "101": {"description": "WebSocket handshake — connection upgraded"},
            },
        }
    }

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _custom_openapi
