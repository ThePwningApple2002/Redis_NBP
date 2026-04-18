# Run Guide

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

