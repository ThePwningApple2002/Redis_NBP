from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils import clean_text


def scrape_website(website_url: str):
    print(f"Attempting to scrape content from: {website_url}")
    loader = WebBaseLoader(website_url)
    docs = loader.load()
    print(f"Loaded {len(docs)} document(s) from the URL.")
    return docs


def process_documents(docs, chunk_size: int, chunk_overlap: int):
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    docs_split = text_splitter.split_documents(docs)
    print(f"Split content into {len(docs_split)} chunk(s).")
    return docs_split
