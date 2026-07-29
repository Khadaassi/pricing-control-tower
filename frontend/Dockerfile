FROM python:3.14-slim

WORKDIR /app
ENV UV_CACHE_DIR=/app/.cache/uv

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && mkdir -p /app/staticfiles \
    && chown -R app:app /app
USER app

EXPOSE 8001

# collectstatic runs here (not at build time) because settings.py reads
# DJANGO_SECRET_KEY/INTERNAL_AUTH_SECRET from the environment at import time,
# and those secrets are only injected at container start, not during the build.
CMD ["sh", "-c", "uv run python manage.py migrate --noinput && uv run python manage.py collectstatic --noinput && uv run gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers ${GUNICORN_WORKERS:-2}"]
