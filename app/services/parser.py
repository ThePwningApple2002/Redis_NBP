from bs4 import BeautifulSoup


def parse_recipe_html(html: str) -> dict:
    # TODO: implement real recipe-specific parsing once sample HTML from the browser extension is provided
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title else "Untitled Recipe"

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    content = soup.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "content": content,
        "source_url": "",
        "tags": [],
    }
