FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

RUN useradd -m appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app \
    && chmod +x entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 以 root 启动，确保 /app/data 权限正确后切换到 appuser
ENTRYPOINT ["/bin/sh", "-c", "mkdir -p /app/data && chown -R appuser:appuser /app/data && exec su appuser -c './entrypoint.sh'"]
