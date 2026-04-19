# Run Guide

## 0) Create .env file (required)

This project requires a `.env` file in the project root before running Docker Compose or Streamlit.

Make sure these values are set in `.env`:
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `REDIS_URL`
- `LLM_MODEL`

## 1) Run backend services with Docker Compose

From the project root:

```bash
docker compose up --build
```

This starts:
- Redis Stack on `localhost:6379` (RedisInsight UI on `localhost:8001`)
- FastAPI backend on `localhost:8000`

To stop services:

```bash
docker compose down
```

## 2) Run Streamlit client with uv

Open a second terminal in the same project folder and run:

```bash
uv sync
uv run streamlit run streamlit_app.py
```

## 3) Browser extension (recipe scraper)

The project includes a Chrome extension in `browser_extension/`.

What it does:
- Adds a popup button that scrapes the current recipe page.
- Extracts recipe HTML (site-specific selectors for a few domains, plus a generic fallback).
- Sends the payload to the backend ingest endpoint: `POST /recipes/ingest`.
- Backend parses and stores the recipe in Redis vector store so it becomes searchable in chat.

### Load extension in Chrome

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the `browser_extension/` folder from this project.

### Use extension

1. Start backend first (Docker Compose section above).
2. Open a recipe page in Chrome.
3. Click the extension icon.
4. Press **Posalji** in the popup.
5. After success, the recipe is ingested and available for RAG retrieval in chat.

### Endpoint and permissions

- Current webhook target is set in `browser_extension/background.js`:

```js
const WEBHOOK_URL = "http://127.0.0.1:8000/recipes/ingest";
```
