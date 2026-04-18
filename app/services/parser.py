from bs4 import BeautifulSoup


def parse_recipe_html(html: str, title: str = None, url: str = None, description: str = None) -> dict:
    """
    Parse recipe HTML from the browser extension.
    
    Args:
        html: The HTML fragment containing recipe content
        title: The page title
        url: The source URL
        description: The page description
    """
    soup = BeautifulSoup(html, "html.parser")

    # Use provided title or extract from soup
    parsed_title = (title or "").strip() or (soup.title.string.strip() if soup.title else "Untitled Recipe")

    # Remove script, style, nav, footer, header tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract text content
    content = soup.get_text(separator="\n", strip=True)

    return {
        "title": parsed_title,
        "content": content,
        "source_url": (url or "").strip(),
        "tags": [description.strip()] if description else [],
    }
