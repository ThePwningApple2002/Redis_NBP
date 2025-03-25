import os
import asyncio
from config import load_config, get_openai_api_key
from scrapper import scrape_website, process_documents
from vectorstore_manager import (
    create_vectorstore_from_docs,
    connect_existing_vectorstore,
)
from chat import perform_search_and_chat
from langchain_openai import OpenAIEmbeddings

async def main():
    config = load_config("schema.yaml")
    redis_url = config.get("redis_url")
    index_name = config.get("index_name")
    website_url = config.get("website_url")
    text_splitter_config = config.get("text_splitter", {})
    chunk_size = text_splitter_config.get("chunk_size", 500)
    chunk_overlap = text_splitter_config.get("chunk_overlap", 50)

    fajlovi_ucitaj = input("Da li zelis da ucitas nove fajlove? (da/ne): ")

    try:
        openai_api_key = get_openai_api_key()
    except ValueError as e:
        print(e)
        return

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = None

    if fajlovi_ucitaj.lower() == "da":
        try:
            docs = scrape_website(website_url)
            docs = process_documents(docs, chunk_size, chunk_overlap)
            vectorstore = create_vectorstore_from_docs(
                docs, embeddings, redis_url, index_name
            )
        except Exception as e:
            print(f"Error during website scraping or vectorstore creation: {e}")
            print("Continuing with existing Redis data (if available).")

    if vectorstore is None:
        try:
            vectorstore = connect_existing_vectorstore(
                embeddings, redis_url, index_name
            )
        except Exception as e:
            print("Failed to connect to the existing vectorstore:", e)
            return

    input_query = input("Input your question: ")
    preprompts = (
        "You are given more context via a mechanism I made. When asked a question "
        "use that context to answer the question"
    )
    await perform_search_and_chat(vectorstore, input_query, preprompts)

if __name__ == "__main__":
    api_key = os.getenv("OPEN_AI_KEY")
    os.environ["OPENAI_API_KEY"] = api_key
    asyncio.run(main())
