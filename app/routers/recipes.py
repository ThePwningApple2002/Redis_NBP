from fastapi import APIRouter, Body
import logging

from app.models import IngestResponse
from app.repository.recipe_repository import RecipeRepository
from app.services.parser import parse_recipe_html

router = APIRouter(prefix="/recipes", tags=["recipes"])
logger = logging.getLogger(__name__)
# Ensure logs propagate to Uvicorn/STDOUT even if basicConfig wasn't set elsewhere
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = True

_recipe_repo = RecipeRepository()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_recipe(payload: dict = Body(...)):
    """Ingest recipe payload from the browser extension.

    Payload is intentionally loose to avoid request validation 422s when fields are missing.
    """
    try:
        html_content = payload.get("htmlFragment") or payload.get("html")
        title = (payload.get("title") or "").strip() or (payload.get("siteName") or "").strip() or "Untitled Recipe"
        url = (payload.get("url") or payload.get("sourceUrl") or "").strip()
        description = (payload.get("description") or "").strip() or None
        site_name = (payload.get("siteName") or "").strip() or None

        if not html_content:
            logger.error(f"No HTML content provided. Payload keys: {list(payload.keys())}")
            return IngestResponse(status="error", title="No HTML content")

        logger.info(f"Ingesting recipe - URL: {url}, Title: {title}, Site: {site_name}")
        logger.debug(f"Payload received: {payload}")

        parsed = parse_recipe_html(
            html=html_content,
            title=title,
            url=url,
            description=description or site_name,
        )
        await _recipe_repo.add_recipe(
            title=parsed["title"],
            content=parsed["content"],
            source_url=parsed["source_url"],
            tags=parsed["tags"],
        )
        logger.info(f"Successfully ingested recipe: {parsed['title']}")
        return IngestResponse(status="ok", title=parsed["title"])
    except Exception as e:
        logger.error(f"Error ingesting recipe: {str(e)}", exc_info=True)
        return IngestResponse(status="error", title=f"Error: {str(e)}")
