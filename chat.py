from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from utils import clean_text

async def perform_search_and_chat(vectorstore, input_query: str, preprompts: str):
    print("===================================")
    print("\nSearch results with scores:")
    results_with_scores = vectorstore.similarity_search_with_relevance_scores(
        input_query, k=5
    )
    print("===================================")

    preview = ""
    for idx, (doc, score) in enumerate(results_with_scores, start=1):
        preview = doc.page_content
        print(
            f"\nResult {idx}:\n{clean_text(preview)}\nDistance: {score}\n"
        )
    print("===================================")

    query_text = f"{preprompts}. {input_query}. {clean_text(preview)}"

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
    )

    await model.ainvoke(query_text)
    
    print("\n===================================")
