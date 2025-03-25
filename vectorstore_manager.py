from langchain_community.vectorstores import Redis


def create_vectorstore_from_docs(docs, embeddings, redis_url: str, index_name: str):
    vectorstore = Redis.from_documents(
        docs, embeddings, redis_url=redis_url, index_name=index_name
    )
    print("Vector index created in Redis.")
    return vectorstore


def connect_existing_vectorstore(embeddings, redis_url: str, index_name: str):
    print("Attempting to connect to existing Redis instance...")
    vectorstore = Redis(
        redis_url=redis_url, index_name=index_name, embedding=embeddings
    )
    return vectorstore
