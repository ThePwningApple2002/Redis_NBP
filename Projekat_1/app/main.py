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
    # --- Use environment variables for Redis ---
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    redis_url = f"redis://{redis_host}:{redis_port}"
    print(f"Using Redis URL: {redis_url}")
    # --- Load other config ---
    config = load_config("schema.yaml")
    index_name = config.get("index_name")
    website_url = config.get("website_url")
    text_splitter_config = config.get("text_splitter", {})
    chunk_size = text_splitter_config.get("chunk_size", 500)
    chunk_overlap = text_splitter_config.get("chunk_overlap", 50)

    # --- Force index creation ---
    fajlovi_ucitaj = input("Da li da ucitava fajlove: ")
    print(f"Index creation flag ('fajlovi_ucitaj'): {fajlovi_ucitaj}")

    # --- Check website_url ---
    if not website_url:
        print("Error: 'website_url' is not set in schema.yaml. Cannot scrape.")
        return

    try:
        openai_api_key = get_openai_api_key()
        print("OpenAI API Key obtained successfully.")
    except ValueError as e:
        print(f"Error getting OpenAI API Key: {e}")
        return

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = None

    # --- MODIFIED ERROR HANDLING FOR CREATION ---
    if fajlovi_ucitaj.lower() == "da":
        try:
            print("Starting website scraping...")
            docs = scrape_website(website_url)
            print("Finished website scraping.")

            print("Starting document processing...")
            docs = process_documents(docs, chunk_size, chunk_overlap)
            print("Finished document processing.")

            print("Starting vectorstore creation...")
            vectorstore = create_vectorstore_from_docs(
                docs, embeddings, redis_url, index_name
            )
            print("Finished vectorstore creation successfully.") # Should print if successful

        except Exception as e:
            print(f"--- CRITICAL ERROR DURING SCRAPING/PROCESSING/CREATION ---")
            # Print the detailed traceback for the original error
            import traceback
            traceback.print_exc()
            print(f"--- END CRITICAL ERROR ---")
            # Stop execution immediately by re-raising or returning
            # raise e # Option 1: Re-raise the exception
            return  # Option 2: Simply return to stop the script here
    # --- END MODIFIED BLOCK ---

    # This block should only be reached if fajlovi_ucitaj was 'ne'
    # OR if creation succeeded above.
    if vectorstore is None:
        print("Vectorstore not created in the 'da' block, attempting to connect...")
        try:
            vectorstore = connect_existing_vectorstore(
                embeddings, redis_url, index_name
            )
        except Exception as e:
            print(f"Failed to connect to the existing vectorstore ({redis_url}):", e)
            # Print traceback for connection error as well
            import traceback
            traceback.print_exc()
            return

    # If we reach here, vectorstore should be valid
    if vectorstore is None:
         print("Error: Vectorstore is still None after attempting creation and connection.")
         return

    print("Proceeding to search and chat...")
    input_query = input("Input your question: ")
    preprompts = (
        "You are given more context via a mechanism I made. When asked a question "
        "use that context to answer the question"
    )
    await perform_search_and_chat(vectorstore, input_query, preprompts)

if __name__ == "__main__":
    asyncio.run(main())

