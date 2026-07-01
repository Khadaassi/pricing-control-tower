FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

EXPOSE 8001

CMD ["sh", "-c", "uv run python manage.py migrate --noinput && uv run python manage.py runserver 0.0.0.0:8001"]
