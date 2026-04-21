from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore

from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key,
    )


@lru_cache(maxsize=1)
def get_vector_store() -> RedisVectorStore:
    """Return a Redis vector store, creating the index if missing.

    We first try to connect to an existing index. If it doesn't exist, we create
    it by inserting a tiny bootstrap document.
    """
    config = RedisConfig(
        index_name="recipe_index",
        redis_url=settings.redis_url,
        metadata_schema=[
            {"name": "title", "type": "text"},
            {"name": "source_url", "type": "text"},
            {"name": "tags", "type": "text"},
        ],
    )
    embeddings = get_embeddings()

    try:
        return RedisVectorStore.from_existing_index(embeddings=embeddings, config=config)
    except Exception:
        return RedisVectorStore.from_texts(
            texts=["__bootstrap__"],
            embedding=embeddings,
            metadatas=[{"title": "__bootstrap__", "source_url": "", "tags": "__bootstrap__"}],
            config=config,
        )


def get_retriever(k: int = 4):
    return get_vector_store().as_retriever(search_kwargs={"k": k})
