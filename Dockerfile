FROM python:3.11-alpine

ENV TZ=UTC \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apk add --no-cache tzdata && \
    pip install --no-cache-dir --upgrade uv && \
    rm -rf /var/cache/apk/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN chmod +x main.py

CMD ["sh", "-c", "uv run alembic upgrade head && uv run main.py"]
