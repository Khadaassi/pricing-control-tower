FROM python:3.14-slim

WORKDIR /app
ENV UV_CACHE_DIR=/app/.cache/uv

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY app ./app
COPY scripts ./scripts

RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8001

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers ${UVICORN_WORKERS:-2}"]
