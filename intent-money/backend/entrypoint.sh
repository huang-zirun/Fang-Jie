#!/bin/sh
export PYTHONPATH=/app
mkdir -p /app/data
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
