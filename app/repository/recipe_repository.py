from langchain_core.documents import Document

from app.services.vectorstore import get_vector_store


class RecipeRepository:
    async def add_recipe(
        self, title: str, content: str, source_url: str, tags: list[str]
    ) -> None:
        vs = get_vector_store()
        doc = Document(
            page_content=content,
            metadata={
                "title": title,
                "source_url": source_url,
                "tags": ", ".join(tags),
            },
        )
        await vs.aadd_documents([doc])
