from functools import lru_cache

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.graph.state import GraphState
from app.services.vectorstore import get_retriever


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        openai_api_key=settings.openrouter_api_key,
        model=settings.llm_model,
        streaming=True,
    )


async def retrieve(state: GraphState) -> dict:
    last_human_msg = next(
        (m for m in reversed(state["messages"]) if m.type == "human"),
        None,
    )
    if not last_human_msg:
        return {"retrieved_context": ""}

    retriever = get_retriever()
    docs = await retriever.ainvoke(last_human_msg.content)
    # Filter out bootstrap/placeholder docs
    docs = [d for d in docs if d.metadata.get("title") != "__bootstrap__"]
    context = "\n\n".join(doc.page_content for doc in docs)
    return {"retrieved_context": context}


async def generate(state: GraphState) -> dict:
    context = state.get("retrieved_context", "")

    system_prompt = (
        "Ti si koristan asistent za kulinarske recepte. "
        "Koristi sledeci kontekst recepta da odgovoris na korisnikovo pitanje. "
        "Ako kontekst nema relevantne informacije, odgovori iz svog opsteg znanja.\n\n"
        f"Kontekst recepta:\n{context}"
    )

    # Strip any SystemMessages that accumulated from previous turns to avoid duplication
    conversation: list[AnyMessage] = [
        m for m in state["messages"]
        if not isinstance(m, SystemMessage)
    ]
    messages = [SystemMessage(content=system_prompt)] + conversation
    response = await get_llm().ainvoke(messages)
    return {"messages": [response]}
