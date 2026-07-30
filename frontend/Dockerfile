# theme/static/css/dist/ (Tailwind output) is gitignored — built from source
# here instead of committing compiled CSS to the repo.
FROM node:22-slim AS tailwind-build
WORKDIR /app/theme/static_src
COPY theme/static_src/package.json theme/static_src/package-lock.json ./
RUN npm ci
COPY theme/static_src/ ./
RUN npm run build

FROM python:3.14-slim

WORKDIR /app
ENV UV_CACHE_DIR=/app/.cache/uv
# --no-create-home leaves $HOME pointing at a nonexistent /home/app;
# gunicorn's control server tries to write there and warns on every start.
ENV HOME=/app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
COPY --from=tailwind-build /app/theme/static/css/dist ./theme/static/css/dist

RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && mkdir -p /app/staticfiles \
    && chown -R app:app /app
USER app

EXPOSE 8001

# collectstatic runs here (not at build time) because settings.py reads
# DJANGO_SECRET_KEY/INTERNAL_AUTH_SECRET from the environment at import time,
# and those secrets are only injected at container start, not during the build.
CMD ["sh", "-c", "uv run python manage.py migrate --noinput && uv run python manage.py collectstatic --noinput && uv run gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers ${GUNICORN_WORKERS:-2}"]
