from fastapi import APIRouter

from app.models import IngestRequest, IngestResponse
from app.repository.recipe_repository import RecipeRepository
from app.services.parser import parse_recipe_html

router = APIRouter(prefix="/recipes", tags=["recipes"])

_recipe_repo = RecipeRepository()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_recipe(request: IngestRequest):
    parsed = parse_recipe_html(request.html)
    await _recipe_repo.add_recipe(
        title=parsed["title"],
        content=parsed["content"],
        source_url=parsed["source_url"],
        tags=parsed["tags"],
    )
    return IngestResponse(status="ok", title=parsed["title"])
