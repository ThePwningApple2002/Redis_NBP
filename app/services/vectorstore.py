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
    config = RedisConfig(
        index_name="recipe_index",
        redis_url=settings.redis_url,
        metadata_schema=[
            {"name": "title", "type": "text"},
            {"name": "source_url", "type": "text"},
            {"name": "tags", "type": "text"},
        ],
    )
    return RedisVectorStore(embeddings=get_embeddings(), config=config)


def get_retriever(k: int = 4):
    return get_vector_store().as_retriever(search_kwargs={"k": k})
